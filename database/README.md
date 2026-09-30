# 数据库说明

## 文档
[中文文档](https://github.com/Diving-Fish/maimaidx-prober/blob/main/database/zh-api-document.md)

## 本机数据与运维文件

`config.json`、`maidle/` 和 `music_data_2024_last.json` 由部署环境提供，不纳入 Git。
其中 `maidle/` 和旧版本曲库仍由 API 启动时读取，清理工作区时不能删除。

服务日志及轮转文件由部署环境管理。`tools/` 下按时间导出的撤销名单、删除记录、
回滚 SQL，以及通知归档的 `private/` 目录均为本机运维资料，只忽略、不自动删除。
可复用的脚本、迁移 SQL 模板和脱敏说明仍纳入版本控制。

`recompute_ra.py` 和 `recompute_ra_bulk.py` 是手动批量重算工具，默认会写库；
应从 `database/` 目录运行。前者逐玩家处理，后者分片扫描，具体参数见各脚本说明。
