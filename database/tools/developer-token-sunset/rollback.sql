-- 回滚 migrate.sql。只有在同时回退后端代码时才用得上：
-- 带 sunset_ts 的后端跑在没有这一列的库上会 500。
ALTER TABLE `developer`    DROP COLUMN `sunset_ts`;
ALTER TABLE `newdeveloper` DROP COLUMN `sunset_ts`;
