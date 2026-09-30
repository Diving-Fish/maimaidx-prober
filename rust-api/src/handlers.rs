use std::net::SocketAddr;
use std::sync::Arc;

use axum::body::Bytes;
use axum::extract::{ConnectInfo, RawQuery, State};
use axum::http::{HeaderMap, HeaderValue};
use axum::response::{IntoResponse, Response};
use serde::Serialize;
use serde_json::Value;

use crate::auth::{self, Identity, Kind};
use crate::db::{self, Lookup, Player};
use crate::developer;
use crate::filters::{Filters, query_pairs};
use crate::records::{self, Payload, Record};
use crate::{ApiError, AppState, json_response};

async fn load_and_rate(state: &AppState, player: &mut Player) -> Result<Vec<Record>, ApiError> {
    let records = db::records(state, player).await?;
    let (total, new_rating, old_count, new_count) = records::rating(&records);
    db::update_rating(state, player, total, new_rating, old_count, new_count).await?;
    Ok(records)
}

async fn records_response(
    state: &AppState,
    player: &mut Player,
    masked: bool,
    filters: Option<Filters>,
) -> Result<Response, ApiError> {
    let mut records = load_and_rate(state, player).await?;
    if masked {
        for record in &mut records {
            records::mask(record);
        }
    }
    // Apply achievement filters after masking, so filtering cannot reveal hidden precision.
    let echo = filters.and_then(|filters| {
        records.retain(|record| filters.matches(record));
        if filters.echo.is_empty() {
            None
        } else {
            Some(filters.echo)
        }
    });
    json_response(&Payload {
        username: player.username.clone(),
        rating: player.rating,
        additional_rating: player.additional_rating,
        nickname: player.nickname.clone(),
        plate: player.plate.clone(),
        records,
        filters: echo,
    })
}

pub async fn player_records(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    RawQuery(query): RawQuery,
) -> Response {
    let mut identity = match auth::authenticate(&state, &headers).await {
        Ok(identity) => identity,
        Err(error) => return error.into_response(),
    };
    let result = match Filters::build(query.as_deref().unwrap_or("")) {
        Ok(filters) => {
            let masked = identity.kind == Kind::OAuth && identity.player.mask;
            records_response(&state, &mut identity.player, masked, Some(filters)).await
        }
        Err(error) => Err(error),
    };
    finish_authenticated_response(&state, identity, result)
}

fn finish_authenticated_response(
    state: &AppState,
    identity: Identity,
    result: Result<Response, ApiError>,
) -> Response {
    let mut response = result.unwrap_or_else(IntoResponse::into_response);
    if identity.kind == Kind::Cookie
        && let Ok(cookie) = auth::renewed_cookie(state, &identity.player.username)
        && let Ok(value) = HeaderValue::from_str(&cookie)
    {
        response.headers_mut().append("set-cookie", value);
    }
    response
}

pub async fn developer_records(
    State(state): State<Arc<AppState>>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    headers: HeaderMap,
    RawQuery(query): RawQuery,
    body: Bytes,
) -> Response {
    let developer = match developer::authenticate(&state, &headers).await {
        Ok(developer) => developer,
        Err(error) => return error.into_response(),
    };
    let query = query.unwrap_or_default();
    let remote_address = headers
        .get("x-real-ip")
        .and_then(|header| header.to_str().ok())
        .filter(|address| !address.is_empty())
        .map(str::to_owned)
        .unwrap_or_else(|| peer.ip().to_string());
    if let Err(error) =
        developer::log_request(&state, &developer, &remote_address, &query, &body).await
    {
        return error.into_response();
    }
    let result = developer_records_response(&state, &query).await;
    let mut response = result.unwrap_or_else(IntoResponse::into_response);
    response.headers_mut().extend(developer.response_headers());
    response
}

async fn developer_records_response(state: &AppState, query: &str) -> Result<Response, ApiError> {
    let pairs = query_pairs(query);
    let first = |name| {
        pairs
            .iter()
            .find(|(key, _)| key == name)
            .map(|(_, value)| value.as_str())
            .unwrap_or("")
    };
    let username = first("username");
    let qq = first("qq");
    let player = if !username.is_empty() {
        db::find(state, Lookup::Username, username).await?
    } else if !qq.is_empty() {
        db::by_qq(state, qq).await?
    } else {
        None
    };
    let mut player = player.ok_or_else(|| ApiError::message(400, "no such user"))?;
    if player.privacy || !player.accept_agreement {
        return Err(ApiError::error(403, "已设置隐私或未同意用户协议"));
    }
    let masked = player.mask;
    records_response(state, &mut player, masked, None).await
}

#[derive(Serialize)]
struct BestCharts {
    sd: Vec<Record>,
    dx: Vec<Record>,
}

#[derive(Serialize)]
struct BestResponse {
    username: String,
    rating: i64,
    additional_rating: Option<i64>,
    nickname: Option<String>,
    plate: Option<String>,
    charts: BestCharts,
    user_general_data: Value,
}

pub async fn query_player(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    body: Bytes,
) -> Response {
    query_player_response(&state, &headers, &body)
        .await
        .unwrap_or_else(IntoResponse::into_response)
}

async fn query_player_response(
    state: &AppState,
    headers: &HeaderMap,
    body: &[u8],
) -> Result<Response, ApiError> {
    // Authenticate Bearer before parsing/using the requested username, matching the decorator.
    let identity = if let Some(token) = auth::bearer(headers) {
        Some(auth::oauth(state, token).await?)
    } else {
        None
    };
    let request: Value =
        serde_json::from_slice(body).map_err(|_| ApiError::message(400, "JSON 格式不正确"))?;
    let mut player = if let Some(identity) = identity {
        identity.player
    } else {
        let player = lookup_query_player(state, &request).await?;
        check_public_privacy(state, headers, &player, &request)?;
        player
    };
    let records = load_and_rate(state, &mut player).await?;
    let (mut sd, mut dx) = records::best(&records, request.get("b50").is_some());
    if player.mask {
        for record in sd.iter_mut().chain(dx.iter_mut()) {
            records::mask(record);
        }
    }
    let nickname = if player.nickname.as_deref() == Some("") {
        if player.username.chars().count() <= 8 {
            Some(player.username.clone())
        } else {
            Some(format!(
                "{}…",
                player.username.chars().take(8).collect::<String>()
            ))
        }
    } else {
        player.nickname.clone()
    };
    json_response(&BestResponse {
        username: player.username,
        rating: player.rating,
        additional_rating: player.additional_rating,
        nickname,
        plate: player.plate,
        charts: BestCharts { sd, dx },
        user_general_data: player
            .general_data
            .as_deref()
            .and_then(|data| serde_json::from_str(data).ok())
            .unwrap_or(Value::Null),
    })
}

fn scalar_lookup(value: &Value) -> Option<String> {
    match value {
        Value::String(text) => Some(text.clone()),
        Value::Number(number) => Some(number.to_string()),
        _ => None,
    }
}

async fn lookup_query_player(state: &AppState, request: &Value) -> Result<Player, ApiError> {
    let player = if let Some(qq) = request.get("qq") {
        match scalar_lookup(qq) {
            Some(qq) => db::by_qq(state, &qq).await?,
            None => None,
        }
    } else {
        match request.get("username").and_then(scalar_lookup) {
            Some(username) => db::find(state, Lookup::Username, &username).await?,
            None => None,
        }
    };
    player.ok_or_else(|| ApiError::message(400, "user not exists"))
}

fn check_public_privacy(
    state: &AppState,
    headers: &HeaderMap,
    player: &Player,
    request: &Value,
) -> Result<(), ApiError> {
    if !player.privacy && player.accept_agreement {
        return Ok(());
    }
    let claims = auth::cookie(headers).and_then(|token| auth::cookie_claims(state, &token));
    let authorized = claims.is_some_and(|claims| {
        claims["username"].as_str() == Some(player.username.as_str())
            && request["username"].as_str() == Some(player.username.as_str())
    });
    if authorized {
        Ok(())
    } else {
        Err(ApiError::error(403, "已设置隐私或未同意用户协议"))
    }
}
