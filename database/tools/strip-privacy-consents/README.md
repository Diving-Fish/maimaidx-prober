# 剥离补给「从未授权」用户的存量授权

2026-08-19 执行。撤销 **492** 条授权（涉及 56 个应用、403 个用户），删除 **493** 条绑定映射。
全部来自 `dev_backfill.py`（`source='legacy_developer'`），用户自己在同意页点出来的授权一条没动。

| 类别 | 条数 |
|---|---|
| `privacy = 1` | 290 |
| `accept_agreement = 0` | 223 |
| 两者重叠 | 21 |
| 合计 | 492 |

## 为什么这些行是错的

`developer_required` **先写日志再执行**（`database/app.py`）。bot 查一个 `privacy=1`
的用户，查分器返回 403，但 `newdeveloperlog` 照样留了一行。`dev_backfill.py` 扫日志
判断「这个用户被这个应用查过」，不看 privacy，于是把一次**被拒绝**的调用当成了真实
的调用关系，给建了 consent。

这批用户当初的表态恰好相反：勾 privacy 等于「谁都别查我」，`accept_agreement=0`
是连用户协议都没同意。他们没有点过任何同意页，却在授权表里有了一条有效授权。

直接后果：`subject=username:` 长期保留之后，「A 通过某 bot 查 B」成为常规用法，
这 290 个人会从「谁都读不到」变成「该应用的任意用户都能按用户名查到」——而这个
转变没有任何一个动作是他们做出的。（`accept_agreement=0` 的 223 条另说：查分器
侧 `_auth_by_bearer` 本来就会拦，属于脏数据而非安全问题，一并清掉。）

## 处理规则

**只动 backfill 建的行。** 用户自己点的同意页授权一律不碰，哪怕他也开着 privacy——
那是他本人的选择，脚本无权代他反悔。执行后核对：`source='user'` 且 `privacy=1` 的
14 条完好无损。

**撤销而不是删除。** consent 置 `revoked_at`，映射行删除（`oauth_client_subject`
没有 `revoked_at`，撤销即删行，与 IdP 的既有语义一致）。

这些用户日后若真想用某个 bot，走一次设备码绑定即可，那时是他们自己点的。

## 文件

- `strip.py` —— 默认只预演，`--apply` 才写库
- `revoked-*.csv` —— 被撤销的每一行（含 client_id、user_id、username、privacy、
  accept_agreement、scope、subject_hash 等，可据此定位与还原）
- `rollback-*.sql` —— 撤回本次撤销并重建映射。`revoked_at` 精确匹配本次时间戳，
  不会把此前 `strip-scanner-consents` 撤掉的行一起复活

## 配套改动

`diving-fish-auth/app/dev_backfill.py` 的 `_load_player_index()` 现在额外返回一个
`blocked` 集合（`privacy=1` 或 `accept_agreement=0` 的 uid），`record()` 命中即跳过并
单独计入「用户设了隐私或未同意协议」。不加这一层的话，脚本重跑会把这 492 条原样建回来。
