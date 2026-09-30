use axum::http::{HeaderMap, HeaderValue};
use chrono::{FixedOffset, TimeZone, Utc};
use mysql_async::{Row, prelude::Queryable};
use serde_json::json;

use crate::records::value;
use crate::{ApiError, AppState};

const APPLICATION_URL: &str = "https://auth.diving-fish.com/console";
const MIGRATION_URL: &str = "https://maimai.diving-fish.com/manual/docs/developer/oauth-migration";
const DAILY_LIMITS: [i64; 5] = [0, 300, 1000, 3000, 10000];

pub struct Developer {
    id: i64,
    legacy: bool,
    available: bool,
    sunset: i64,
    level: i64,
}

impl Developer {
    fn from_row(row: Row, legacy: bool, global_sunset: i64) -> Result<Self, ApiError> {
        let sunset: i64 = value(&row, "sunset_ts")?;
        Ok(Self {
            id: value(&row, "id")?,
            legacy,
            available: value(&row, "available")?,
            sunset: if sunset == 0 { global_sunset } else { sunset },
            level: if legacy { 0 } else { value(&row, "level")? },
        })
    }

    pub fn response_headers(&self) -> HeaderMap {
        let mut headers = HeaderMap::new();
        let deadline =
            std::time::UNIX_EPOCH + std::time::Duration::from_secs(self.sunset.max(0) as u64);
        headers.insert(
            "sunset",
            HeaderValue::from_str(&httpdate::fmt_http_date(deadline)).unwrap(),
        );
        headers.insert("deprecation", HeaderValue::from_static("true"));
        headers.insert(
            "link",
            HeaderValue::from_str(&format!(
                "<{MIGRATION_URL}>; rel=\"sunset\"; type=\"text/html\""
            ))
            .unwrap(),
        );
        headers
    }
}

async fn lookup(
    state: &AppState,
    token: &str,
    legacy: bool,
) -> Result<Option<Developer>, ApiError> {
    let sql = if legacy {
        "SELECT id, available, sunset_ts FROM developer WHERE token=? LIMIT 1"
    } else {
        "SELECT id, available, level, sunset_ts FROM newdeveloper WHERE token=? LIMIT 1"
    };
    let mut connection = state.pool.get_conn().await?;
    let row: Option<Row> = connection.exec_first(sql, (token,)).await?;
    row.map(|row| Developer::from_row(row, legacy, state.sunset))
        .transpose()
}

async fn check_daily_quota(state: &AppState, developer: &Developer) -> Result<(), ApiError> {
    let timezone = FixedOffset::east_opt(8 * 3600).unwrap();
    let today = Utc::now().with_timezone(&timezone).date_naive();
    let midnight = timezone
        .from_local_datetime(&today.and_hms_opt(0, 0, 0).unwrap())
        .single()
        .unwrap()
        .timestamp() as f64
        * 1e9;
    let mut connection = state.pool.get_conn().await?;
    let count: Option<i64> = connection
        .exec_first(
            "SELECT COUNT(*) FROM newdeveloperlog
         WHERE developer_id=? AND `timestamp`>? AND `timestamp`<?",
            (developer.id, midnight, midnight + 86400.0 * 1e9),
        )
        .await?;
    let limit = DAILY_LIMITS
        .get(developer.level as usize)
        .copied()
        .unwrap_or(0);
    if count.unwrap_or(0) >= limit {
        return Err(ApiError::developer(400, "已超出今日请求上限"));
    }
    Ok(())
}

pub async fn authenticate(state: &AppState, headers: &HeaderMap) -> Result<Developer, ApiError> {
    let token = headers
        .get("developer-token")
        .and_then(|header| header.to_str().ok())
        .filter(|token| !token.is_empty())
        .ok_or_else(|| ApiError::developer(400, "请先联系水鱼申请开发者token"))?;

    // Legacy fallback is allowed only when the new token is missing or disabled,
    // matching the existing supported token generations. Database failures fail closed.
    let developer = match lookup(state, token, false).await? {
        Some(developer) if developer.available => {
            check_daily_quota(state, &developer).await?;
            developer
        }
        _ => lookup(state, token, true)
            .await?
            .ok_or_else(|| ApiError::developer(400, "开发者token有误"))?,
    };
    if !developer.available {
        return Err(ApiError::developer(
            400,
            "开发者token被禁用，请联系水鱼重新登记信息",
        ));
    }
    if Utc::now().timestamp() >= developer.sunset {
        let timezone = FixedOffset::east_opt(8 * 3600).unwrap();
        let deadline = timezone
            .timestamp_opt(developer.sunset, 0)
            .single()
            .map(|date| date.format("%Y-%m-%d %H:%M (UTC+8)").to_string())
            .unwrap_or_default();
        return Err(ApiError {
            status: axum::http::StatusCode::GONE,
            body: json!({
                "status": "error",
                "msg": format!("开发者 token 已于 {deadline} 停止服务，请改用水鱼账号 OAuth：{APPLICATION_URL}（迁移说明：{MIGRATION_URL}）"),
                "sunset": developer.sunset,
                "migration": MIGRATION_URL,
            }),
        });
    }
    Ok(developer)
}

pub async fn log_request(
    state: &AppState,
    developer: &Developer,
    remote_address: &str,
    query: &str,
    body: &[u8],
) -> Result<(), ApiError> {
    let timestamp = Utc::now()
        .timestamp_nanos_opt()
        .ok_or_else(ApiError::internal)? as f64;
    let mut connection = state.pool.get_conn().await?;
    if developer.legacy {
        connection
            .exec_drop(
                "INSERT INTO developerlog (developer_id, `function`, remote_addr, `timestamp`)
             VALUES (?, ?, ?, ?)",
                (developer.id, "dev_get_records", remote_address, timestamp),
            )
            .await?;
    } else {
        let mut arguments = serde_json::Map::new();
        for (name, value) in crate::filters::query_pairs(query) {
            arguments.entry(name).or_insert(json!(value));
        }
        let body =
            std::str::from_utf8(body).map_err(|_| ApiError::message(400, "请求体不是 UTF-8"))?;
        connection
            .exec_drop(
                "INSERT INTO newdeveloperlog
             (developer_id, `function`, remote_addr, `timestamp`, request_args, request_body)
             VALUES (?, ?, ?, ?, ?, ?)",
                (
                    developer.id,
                    "dev_get_records",
                    remote_address,
                    timestamp,
                    serde_json::Value::Object(arguments).to_string(),
                    body,
                ),
            )
            .await?;
    }
    Ok(())
}
