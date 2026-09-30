# 开发者停用通知归档

2026-09-29 的核实快照和投送记录保存在本机 `private/2026-09-29/`，该目录已由 `.gitignore` 排除，不提交邮箱名单。

- `legacy-accounts.csv`：11 个老版账号的昵称、调用统计、联系方式及确认情况。lingdu 的账号归属由维护者确认；其余 10 个没有可用邮箱。
- `developers.csv` / `summary.json`：名单核实快照；它们保留投送前的审计结果。
- `send-manifest.json`：最终 133 个去重收件人，包括维护者指定的副本邮箱。
- `message.json`：审核通过的邮件正文及主题。
- `send-results.jsonl`：每封邮件的 Message-ID、尝试记录、SMTP 结果及按原 Message-ID 核实的退信。
- `delivery-status.json` / `delivery-worker.log`：后台续投的当前状态、下一次重试时间及运行日志。
- `bounce-check.json` / `post-send-bounce-check.json`：投送前后读取收件箱的退信检查。

SMTP 接收不等于最终送达。投送日志里每个邮箱的最后一条记录才是当前状态；没有最终结果的 `attempting` 不能直接重发，以免重复投递。

本次归档仅保存账号信息，未禁用或删除数据库中的老版账号。

阿里邮箱发生临时频率限制时，后台任务按 5、10、15、30 分钟及之后最多四次 60 分钟冷却重试，每封间隔 5 秒。只重试未发送、明确收到 SMTP 454 或明确收到限速退信的邮件；已接收且无退信、结果不确定及永久拒收的邮件均不自动重发。
