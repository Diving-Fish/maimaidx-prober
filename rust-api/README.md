# Rust 查询服务

承接舞萌的三个高频查询接口：`GET /player/records`、`POST /query/player`（B40/B50）、`GET /dev/player/records`。使用 Axum、Tokio、mysql_async 连接池和手写 SQL，没有 ORM。数据库仍是原来的 MySQL；其余接口和定时统计继续由 Python 处理。

## 代码结构

- `src/main.rs`：启动、连接池、路由、响应和请求日志。
- `src/handlers.rs`：接口流程及响应类型。
- `src/auth.rs`：Cookie、Import-Token、OAuth/JWKS 和 Redis 配额。
- `src/developer.rs`：开发者鉴权、配额、日落声明及审计记录。
- `src/db.rs`：玩家查询、成绩查询、变化字段写回。
- `src/records.rs`：成绩解码、rating、B40/B50 排序、遮罩、JSON。
- `src/filters.rs`：成绩筛选和牌子版本映射。

每次请求读取成绩一次，并根据当前定数重新计算。rating 等字段与已读取的玩家行一致时跳过写回；访问时间最多每五分钟写一次。未缓存成绩，因此上传成绩和更新定数后无需清理成绩缓存。

接口保留原有鉴权优先级、隐私与协议检查、OAuth 成绩遮罩、筛选语义、Cookie 续期和开发者日志。数据库异常时开发者鉴权直接失败。畸形 JSON 的错误正文可能与 Quart 的 HTML 错误页不同。

## 构建与检查

需要支持 edition 2024 的 Rust 工具链；本机使用 Rust 1.98.1。

```sh
cargo fmt --check --manifest-path rust-api/Cargo.toml
cargo clippy --release --manifest-path rust-api/Cargo.toml --all-targets -- -D warnings
cargo test --release --manifest-path rust-api/Cargo.toml
cargo build --release --locked --manifest-path rust-api/Cargo.toml
```

本机临时工具链位于 `/tmp/maimai-rust-toolchain`。使用时设置 `RUSTUP_HOME=/tmp/maimai-rust-toolchain/rustup`、`CARGO_HOME=/tmp/maimai-rust-toolchain/cargo`、`CARGO_TARGET_DIR=/tmp/maimai-rust-toolchain/target`，调用该目录 `cargo/bin/cargo`。部署后的二进制不依赖这些临时目录。

## 运行与代理

读取现有 `database/config.json`，仅监听 `127.0.0.1:8345`。启动时获取公开 JWKS，此后每五分钟刷新，失败保留已有密钥。MySQL 池最多 12 个连接，Tokio 使用两个工作线程。HTTP 客户端禁用代理。

`deploy/maimaidx-rust-api.service` 使用仓库内 `bin/maimaidx-rust-api`。`deploy/nginx-routes.conf` 是两域名 server 块共用的三个精确 location；原有 `/api/maimaidxprober/` 前缀代理继续指向 Python 8333。

```sh
sudo systemctl status maimaidx-rust-api
sudo journalctl -u maimaidx-rust-api --since '10 minutes ago'
curl --noproxy '*' http://127.0.0.1:8345/healthz
```

响应包含 `X-Prober-Backend: rust` 和 `Server-Timing`。日志不记录请求参数、正文或认证头。开发者审计仍按原接口要求入库。

## 对照与基准

在仓库根目录执行 `database/venv/bin/python rust-api/tests/parity.py`。对照测试创建临时玩家和少量成绩，在 finally 中删除；使用临时、只读、五分钟过期的 OAuth 凭据。可通过环境变量 `PARITY_DEVELOPER_TOKEN` 提供开发者测试 token。`--public URL` 可追加检查公网反代，所有 HTTP 请求均禁用代理。

`tests/benchmark.py` 对 DivingFish 的三个接口交替测量 Python 与 Rust，验证 JSON 一致，并把耗时保存至 `benchmark-results.json`，不保存 token 或成绩。需要同一环境变量。结果反映串行请求延迟，不代表高峰吞吐容量。

## 回退

从两个 server 块中移除 `include /etc/nginx/snippets/maimaidx-rust-routes.conf;`，执行 `sudo nginx -t` 后 `sudo systemctl reload nginx`。三个接口立即重新匹配原有 Python 代理；随后可以停止 Rust 服务。回退不需要修改数据库结构。

## 本次部署记录（2026-09-30）

服务名 `maimaidx-rust-api.service`，端口 `127.0.0.1:8345`；两个站点均通过 `/etc/nginx/snippets/maimaidx-rust-routes.conf` 转发三个精确路径。原 Nginx 配置备份为 `/var/backups/maimaidx-rust-api/default.conf.20260930-before-rust`。

验证：6 项单元测试、59 项本机接口对照、格式检查及 Clippy 严格检查通过。对照包含历史 NULL 玩家字段。首次切换发现历史账号 plate 为 NULL 导致错误，已立即回退并按实际表结构修复后重新切换。公网只完成不带凭据的路由检查；携带凭据的公网完整对照被自动审批拒绝，未执行。

20 组交替请求的中位数（Python → Rust）：普通成绩列表 137.4 → 36.0 ms，B50 60.6 → 28.0 ms，开发者列表 131.9 → 44.5 ms。测试用户 DivingFish，禁用代理，返回 JSON 相同；原始数据见 benchmark-results.json。这轮数据采集于可空字段修复前，修复后接口对照通过；线上负载变化会影响绝对耗时。

修复后首轮真实流量观察：三个接口均有成功请求，未再出现 500 或行转换错误。服务当时 RSS 约 18 MiB；这只是启动后短时观测，不是稳定峰值。原 8344 端口的实验进程已停止。
