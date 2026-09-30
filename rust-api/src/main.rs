mod auth;
mod db;
mod developer;
mod filters;
mod handlers;
mod records;
use axum::{
    Router,
    extract::{DefaultBodyLimit, Request},
    http::{HeaderValue, StatusCode},
    middleware::{self, Next},
    response::{IntoResponse, Response},
    routing::{get, post},
};
use mysql_async::{Opts, OptsBuilder, Pool, PoolConstraints, PoolOpts};
use serde_json::{Value, json};
use std::{
    sync::Arc,
    time::{Duration, Instant},
};

pub struct AppState {
    pub pool: Pool,
    pub secret: String,
    pub oauth: auth::OAuth,
    pub sunset: i64,
}

#[derive(Debug)]
pub struct ApiError {
    status: StatusCode,
    body: Value,
}

impl ApiError {
    pub fn message(code: u16, msg: &str) -> Self {
        Self {
            status: StatusCode::from_u16(code).unwrap(),
            body: json!({"message":msg}),
        }
    }
    pub fn error(code: u16, msg: &str) -> Self {
        Self {
            status: StatusCode::from_u16(code).unwrap(),
            body: json!({"status":"error","message":msg}),
        }
    }
    pub fn developer(code: u16, msg: &str) -> Self {
        Self {
            status: StatusCode::from_u16(code).unwrap(),
            body: json!({"status":"error","msg":msg}),
        }
    }
    pub fn internal() -> Self {
        Self::message(500, "内部错误")
    }
}

impl From<String> for ApiError {
    fn from(_: String) -> Self {
        eprintln!("row conversion failed");
        Self::internal()
    }
}

impl From<mysql_async::Error> for ApiError {
    fn from(e: mysql_async::Error) -> Self {
        match e {
            mysql_async::Error::Server(ref server) => eprintln!("MySQL error code={}", server.code),
            _ => eprintln!("MySQL connection/query failed"),
        };
        Self::internal()
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (self.status, axum::Json(self.body)).into_response()
    }
}

pub fn json_response<T: serde::Serialize>(value: &T) -> Result<Response, ApiError> {
    let body = records::serialize(value).map_err(|_| ApiError::internal())?;
    Ok(([("content-type", "application/json")], body).into_response())
}

async fn common(request: Request, next: Next) -> Response {
    let method = request.method().clone();
    let path = request.uri().path().to_owned();
    let start = Instant::now();
    let mut response = match tokio::time::timeout(Duration::from_secs(35), next.run(request)).await
    {
        Ok(r) => r,
        Err(_) => ApiError::message(504, "请求超时").into_response(),
    };
    let headers = response.headers_mut();
    headers.insert("access-control-allow-origin", HeaderValue::from_static("*"));
    headers.insert("access-control-allow-method", HeaderValue::from_static("*"));
    headers.insert(
        "access-control-allow-headers",
        HeaderValue::from_static("x-requested-with,content-type,import-token,authorization"),
    );
    headers.insert("x-prober-backend", HeaderValue::from_static("rust"));
    let ms = start.elapsed().as_secs_f64() * 1000.;
    headers.insert(
        "server-timing",
        HeaderValue::from_str(&format!("total;dur={ms:.3}")).unwrap(),
    );
    eprintln!(
        "{} {} {} {} {:.3}ms",
        chrono::Utc::now().to_rfc3339(),
        method,
        path,
        response.status().as_u16(),
        ms
    );
    response
}

async fn options_records() -> Response {
    ([("allow", "GET, HEAD, OPTIONS")], "").into_response()
}

async fn options_query() -> Response {
    ([("allow", "POST, OPTIONS")], "").into_response()
}

#[tokio::main(worker_threads = 2)]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "database/config.json".into());
    let config: Value = serde_json::from_slice(&std::fs::read(path)?)?;
    let raw = config["mysql_url"].as_str().ok_or("missing mysql_url")?;
    let (_, tail) = raw.split_once("://").ok_or("invalid mysql_url")?;
    let opts =
        Opts::from_url(&format!("mysql://{tail}")).map_err(|_| "invalid mysql configuration")?;
    let pool = Pool::new(
        OptsBuilder::from_opts(opts)
            .prefer_socket(false)
            .pool_opts(PoolOpts::default().with_constraints(PoolConstraints::new(2, 12).unwrap())),
    );
    let oauth = auth::OAuth::new(
        config["idp"]["issuer"].as_str().unwrap_or("").into(),
        config["idp"]["resource"]
            .as_str()
            .unwrap_or("https://www.diving-fish.com/api/maimaidxprober")
            .into(),
    )?;
    if oauth.enabled() {
        oauth
            .refresh(true)
            .await
            .map_err(|_| "initial JWKS refresh failed")?;
    }
    let state = Arc::new(AppState {
        pool,
        secret: config["jwt_secret"]
            .as_str()
            .ok_or("missing jwt_secret")?
            .into(),
        oauth,
        sunset: 1798732800,
    });
    let updater = state.clone();
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(Duration::from_secs(300)).await;
            if updater.oauth.refresh(true).await.is_err() {
                eprintln!("JWKS refresh failed; retaining current keys")
            }
        }
    });
    let router = Router::new()
        .route(
            "/player/records",
            get(handlers::player_records).options(options_records),
        )
        .route(
            "/query/player",
            post(handlers::query_player).options(options_query),
        )
        .route(
            "/dev/player/records",
            get(handlers::developer_records).options(options_records),
        )
        .route("/healthz", get(|| async { "ok" }))
        .layer(DefaultBodyLimit::max(16 * 1024 * 1024))
        .layer(middleware::from_fn(common))
        .with_state(state);
    let bind = std::env::var("RUST_API_BIND").unwrap_or_else(|_| "127.0.0.1:8345".into());
    let addr: std::net::SocketAddr = bind.parse()?;
    if !addr.ip().is_loopback() {
        return Err("Rust API must bind a loopback address behind the trusted proxy".into());
    }
    let listener = tokio::net::TcpListener::bind(addr).await?;
    eprintln!("Rust API listening on {addr}");
    axum::serve(
        listener,
        router.into_make_service_with_connect_info::<std::net::SocketAddr>(),
    )
    .with_graceful_shutdown(async {
        let mut terminate =
            tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
                .expect("signal handler");
        tokio::select! {
            _ = tokio::signal::ctrl_c() => {},
            _ = terminate.recv() => {},
        }
    })
    .await?;
    Ok(())
}

#[cfg(test)]
mod tests;
