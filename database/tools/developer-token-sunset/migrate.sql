-- developer token 日落：给两张表补失效时间列。
--
-- 必须在部署带 sunset_ts 的后端**之前**执行：peewee 的 SELECT 会带上模型里
-- 声明的每一列，列不存在时所有 /dev/* 请求会直接 500，而不是优雅降级。
--
-- 0 表示「按全局日落时间算」（app.DEVELOPER_TOKEN_SUNSET_TS，
-- 2026-10-01 00:00 UTC+8）。存量行全部保持 0：日期只写在代码里一处，
-- 不往几百行数据里复制一遍，否则改期就要再跑一次 UPDATE。
ALTER TABLE `developer`    ADD COLUMN `sunset_ts` BIGINT NOT NULL DEFAULT 0;
ALTER TABLE `newdeveloper` ADD COLUMN `sunset_ts` BIGINT NOT NULL DEFAULT 0;
