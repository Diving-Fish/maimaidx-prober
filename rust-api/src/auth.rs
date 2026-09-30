use crate::{
    ApiError, AppState,
    db::{self, Lookup, Player},
};
use axum::http::HeaderMap;
use chrono::Utc;
use jsonwebtoken::{
    Algorithm, DecodingKey, EncodingKey, Header, Validation, decode, decode_header, encode,
    errors::ErrorKind,
};
use serde_json::{Value, json};
use std::{collections::HashMap, time::Duration};
use tokio::sync::{Mutex, OnceCell, RwLock};

pub struct OAuth {
    pub issuer: String,
    pub audience: String,
    keys: RwLock<HashMap<String, DecodingKey>>,
    last_refresh_attempt: Mutex<i64>,
    http: reqwest::Client,
    redis: redis::Client,
    redis_connection: OnceCell<redis::aio::ConnectionManager>,
}

impl OAuth {
    pub fn new(issuer: String, audience: String) -> Result<Self, Box<dyn std::error::Error>> {
        Ok(Self {
            issuer: issuer.trim_end_matches('/').into(),
            audience,
            keys: RwLock::new(HashMap::new()),
            last_refresh_attempt: Mutex::new(0),
            http: reqwest::Client::builder()
                .no_proxy()
                .timeout(Duration::from_secs(10))
                .build()?,
            redis: redis::Client::open("redis://127.0.0.1:6379/0")?,
            redis_connection: OnceCell::new(),
        })
    }
    pub fn enabled(&self) -> bool {
        !self.issuer.is_empty() && !self.audience.is_empty()
    }
    pub async fn refresh(&self, force: bool) -> Result<(), ApiError> {
        if !self.enabled() {
            return Ok(());
        }
        let mut last_attempt = self.last_refresh_attempt.lock().await;
        let now = Utc::now().timestamp();
        if !force && now - *last_attempt < 30 {
            return Ok(());
        }
        *last_attempt = now;
        let response = self
            .http
            .get(format!("{}/.well-known/jwks.json", self.issuer))
            .send()
            .await
            .map_err(|_| ApiError::internal())?;
        let document: Value = response
            .error_for_status()
            .map_err(|_| ApiError::internal())?
            .json()
            .await
            .map_err(|_| ApiError::internal())?;
        let mut keys = HashMap::new();
        for key in document["keys"].as_array().into_iter().flatten() {
            if key["kty"] != "RSA" {
                continue;
            }
            if let (Some(kid), Some(modulus), Some(exponent)) =
                (key["kid"].as_str(), key["n"].as_str(), key["e"].as_str())
                && let Ok(public_key) = DecodingKey::from_rsa_components(modulus, exponent)
            {
                keys.insert(kid.into(), public_key);
            }
        }
        if !keys.is_empty() {
            *self.keys.write().await = keys;
        }
        Ok(())
    }
    async fn verify(&self, token: &str) -> Result<Value, ApiError> {
        let header =
            decode_header(token).map_err(|_| ApiError::error(401, "access token 格式不正确"))?;
        let kid = header.kid.unwrap_or_default();
        if !self.keys.read().await.contains_key(&kid) {
            let _ = self.refresh(false).await;
        }
        let key = self
            .keys
            .read()
            .await
            .get(&kid)
            .cloned()
            .ok_or_else(|| ApiError::error(401, "access token 的签名密钥未知"))?;
        let mut validation = Validation::new(Algorithm::RS256);
        validation.leeway = 0;
        validation.validate_nbf = true;
        validation.set_required_spec_claims(&["exp", "iss", "aud", "sub"]);
        validation.set_issuer(&[&self.issuer]);
        validation.set_audience(&[&self.audience]);
        decode::<Value>(token, &key, &validation)
            .map(|token| token.claims)
            .map_err(|error| match error.kind() {
                ErrorKind::ExpiredSignature => ApiError::error(401, "access token 已过期"),
                ErrorKind::InvalidAudience => {
                    ApiError::error(401, "这张 access token 不是发给查分器的")
                }
                ErrorKind::InvalidSignature => {
                    ApiError::error(401, "access token 无效（InvalidSignatureError）")
                }
                ErrorKind::InvalidIssuer => {
                    ApiError::error(401, "access token 无效（InvalidIssuerError）")
                }
                ErrorKind::ImmatureSignature => {
                    ApiError::error(401, "access token 无效（ImmatureSignatureError）")
                }
                ErrorKind::InvalidAlgorithm => {
                    ApiError::error(401, "access token 无效（InvalidAlgorithmError）")
                }
                _ => ApiError::error(401, "access token 无效（DecodeError）"),
            })
    }
    async fn quota(&self, claims: &Value, user_id: i64) -> Result<bool, redis::RedisError> {
        let mut connection = self
            .redis_connection
            .get_or_try_init(|| self.redis.get_connection_manager())
            .await?
            .clone();
        let client = claims["act"]["client_id"]
            .as_str()
            .filter(|s| !s.is_empty())
            .or_else(|| claims["client_id"].as_str().filter(|s| !s.is_empty()))
            .unwrap_or("unknown");
        let parse = |v: &Value, default: i64| -> Option<i64> {
            if v.is_null() || v == &json!(0) || v == &json!("") {
                Some(default)
            } else {
                v.as_i64()
                    .or_else(|| v.as_str().and_then(|s| s.parse().ok()))
            }
        };
        let limits = match (
            parse(&claims["df_quota"]["u"], 200),
            parse(&claims["df_quota"]["c"], 10000),
        ) {
            (Some(u), Some(c)) => (u, c),
            _ => (200, 10000),
        };
        let day = Utc::now().format("%Y%m%d");
        for (key, limit) in [
            (
                format!("prober:oauth:q:u:{client}:{user_id}:{day}"),
                limits.0,
            ),
            (format!("prober:oauth:q:c:{client}:{day}"), limits.1),
        ] {
            let request_count: i64 = redis::cmd("INCR")
                .arg(&key)
                .query_async(&mut connection)
                .await?;
            if request_count == 1 {
                let _: i64 = redis::cmd("EXPIRE")
                    .arg(&key)
                    .arg(172800)
                    .query_async(&mut connection)
                    .await?;
            }
            if request_count > limit {
                return Ok(false);
            }
        }
        Ok(true)
    }
}

#[derive(Clone, Copy, PartialEq)]
pub enum Kind {
    Cookie,
    ImportToken,
    OAuth,
}

pub struct Identity {
    pub player: Player,
    pub kind: Kind,
}

pub fn bearer(headers: &HeaderMap) -> Option<&str> {
    let authorization = headers.get("authorization")?.to_str().ok()?;
    if authorization.get(..7)?.eq_ignore_ascii_case("bearer ") {
        Some(authorization[7..].trim())
    } else {
        None
    }
}

pub fn cookie(headers: &HeaderMap) -> Option<String> {
    headers
        .get_all("cookie")
        .iter()
        .filter_map(|h| h.to_str().ok())
        .flat_map(|v| v.split(';'))
        .find_map(|pair| {
            let (key, value) = pair.trim().split_once('=')?;
            if key == "jwt_token" {
                Some(value.trim_matches('"').into())
            } else {
                None
            }
        })
}

pub fn cookie_claims(state: &AppState, token: &str) -> Option<Value> {
    let mut validation = Validation::new(Algorithm::HS256);
    validation.leeway = 0;
    validation.validate_nbf = true;
    decode::<Value>(
        token,
        &DecodingKey::from_secret(state.secret.as_bytes()),
        &validation,
    )
    .ok()
    .map(|token| token.claims)
}

pub fn renewed_cookie(state: &AppState, username: &str) -> Result<String, ApiError> {
    let jwt = encode(
        &Header::new(Algorithm::HS256),
        &json!({"username":username,"exp":Utc::now().timestamp()+2592000}),
        &EncodingKey::from_secret(state.secret.as_bytes()),
    )
    .map_err(|_| ApiError::internal())?;
    Ok(format!(
        "jwt_token={jwt}; Expires={}; Max-Age=2592000; Path=/",
        httpdate::fmt_http_date(std::time::SystemTime::now() + Duration::from_secs(2592000))
    ))
}

pub async fn oauth(state: &AppState, token: &str) -> Result<Identity, ApiError> {
    if !state.oauth.enabled() {
        return Err(ApiError::error(503, "服务端未启用 OAuth"));
    }
    let claims = state.oauth.verify(token).await?;
    if !claims["scope"]
        .as_str()
        .unwrap_or("")
        .split_whitespace()
        .any(|s| s == "prober.records.read")
    {
        return Err(ApiError::error(
            403,
            "access token 缺少权限：prober.records.read",
        ));
    }
    let sub = claims["sub"]
        .as_str()
        .ok_or_else(|| ApiError::error(400, "用户不存在"))?;
    let player = db::find(state, Lookup::Id, sub)
        .await?
        .ok_or_else(|| ApiError::error(400, "用户不存在"))?;
    if !player.accept_agreement {
        return Err(ApiError::error(403, "该用户未同意用户协议"));
    }
    match tokio::time::timeout(
        Duration::from_secs(2),
        state.oauth.quota(&claims, player.id),
    )
    .await
    {
        Ok(Ok(false)) => return Err(ApiError::error(429, "已超出今日请求上限")),
        Ok(Ok(true)) => {}
        _ => eprintln!("OAuth quota unavailable; allowing authenticated request"),
    }
    Ok(Identity {
        player,
        kind: Kind::OAuth,
    })
}

pub async fn authenticate(state: &AppState, headers: &HeaderMap) -> Result<Identity, ApiError> {
    if let Some(token) = bearer(headers) {
        return oauth(state, token).await;
    }
    if let Some(token) = headers
        .get("import-token")
        .and_then(|v| v.to_str().ok())
        .filter(|v| !v.is_empty())
    {
        let player = db::find(state, Lookup::ImportToken, token)
            .await?
            .ok_or_else(|| ApiError::error(400, "导入token有误"))?;
        return Ok(Identity {
            player,
            kind: Kind::ImportToken,
        });
    }
    let token = cookie(headers).ok_or_else(|| ApiError::error(403, "尚未登录"))?;
    let claims = cookie_claims(state, &token).ok_or_else(|| ApiError::error(403, "尚未登录"))?;
    let username = claims["username"]
        .as_str()
        .ok_or_else(|| ApiError::error(403, "尚未登录"))?;
    let player = db::find(state, Lookup::Username, username)
        .await?
        .ok_or_else(|| ApiError::error(403, "尚未登录"))?;
    Ok(Identity {
        player,
        kind: Kind::Cookie,
    })
}
