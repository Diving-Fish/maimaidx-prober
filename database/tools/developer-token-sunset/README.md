# developer token 日落

`Developer-Token` 与「新版」开发者 token 于 **2026-10-01 00:00 (UTC+8)** 全部停止服务，
第三方改走水鱼账号 OAuth（`https://auth.diving-fish.com`）。

停的是凭据，不是数据：受影响的端点是 `developer_required` 保护的那五个
（`/dev/player/records`、`/dev/player/record`、`/query/plate`、
`/chuni/dev/player/records`、`/channel_to_qq`），替代端点见
[迁移文档](../../../doc/docs/developer/oauth-migration.md)。

## 上线顺序

1. 先跑 `migrate.sql`——两条 `ALTER TABLE`，给 `developer` / `newdeveloper` 各补一列
   `sunset_ts`。**必须在部署代码之前**：peewee 的 SELECT 会带上模型里声明的每一列，
   列不存在时所有 `/dev/*` 请求直接 500。
2. 再部署后端。日落之前行为不变，只是成功响应上多了三个头
   （`Sunset` / `Deprecation` / `Link`，RFC 8594），告诉还在调用的服务哪天停。
3. 到点之后 `is_developer()` 一律返回 410，正文里带 `sunset` 时间戳和迁移文档地址。

```bash
mysql -u <user> -p maimaidxprober < migrate.sql
```

## 单独续期

`sunset_ts` 为 0 表示按全局日落时间算，非 0 则以该行为准。总会有一两家在最后一刻
才发现没改完——给那一个 token 续几天，比把全局日期整体往后推要好，后者等于让所有
已经改完的人白改。

```sql
-- 给某个 token 续到 2026-10-08 00:00 (UTC+8)
UPDATE `newdeveloper` SET `sunset_ts` = UNIX_TIMESTAMP('2026-10-08 00:00:00') WHERE `token` = '<token>';
-- 收回续期，改回按全局日期
UPDATE `newdeveloper` SET `sunset_ts` = 0 WHERE `token` = '<token>';
```

（`UNIX_TIMESTAMP()` 按 MySQL 会话时区解释字面量，这台机器是 CST，与公告口径一致；
不确定时用 `SELECT UNIX_TIMESTAMP('2026-10-08 00:00:00');` 核一下，
2026-10-01 00:00 UTC+8 应当是 `1790784000`。）

`available = 0` 不能替代它：置 false 是「这个 token 出事了，现在就断」，
日落是「到那天为止都正常」，二者在到期之前对调用方的表现完全不同。

## 回滚

`rollback.sql` 删掉这两列，仅在同时回退后端代码时使用。
