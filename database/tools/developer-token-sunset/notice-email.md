**收件人**：持有可用 token 的开发者。`newdeveloper` 424 个 token 全部有 `bind_qq` ，去重后 416 个 `bind_qq@qq.com` 地址；
`developer`（老表）62 个只存了 nickname ，其中 16 个能按同名查分器账号的 `bind_qq` 找到邮箱，其余 46 个没有联系方式，
只能靠响应头和文档得知。近 30 天仍在调用的是老表 11 个、新表 192 个——老表那 11 个里若有触达不到的，建议单独去找。
**发件人**：`official@diving-fish.com` （阿里云企业邮），显示名「舞萌 DX 查分器」。收发均已实测通过，
该邮箱能收到回复，「请回复本邮件」这句话成立。发完后记得回收件箱查退信：历史退信都是发往 QQ 邮箱的
`550 Mailbox unavailable`（对方未开通或拒收），目前已知的 14 个坏地址与上述 416 个收件人无重叠。
**建议发送时间**：即日（距停止服务 42 天），并于 9 月 24 日、9 月 30 日各补发一次提醒

**主题**：【重要】开发者 Token 将于 2026 年 10 月 1 日停止服务，请迁移至水鱼账号 OAuth

---

您好，

您在舞萌 DX | 中二节奏查分器登记过开发者 token 。现通知您：

> **2026 年 10 月 1 日 00:00（UTC+8）起，全部开发者 token 停止服务。**

这一时间对 `Developer-Token` 与后来签发的开发者 token 同时生效。届时以下端点将不再接受 token ，一律返回 `410 Gone` ：

| **停止服务的端点** | **替代端点** | **所需 scope** |
|-----|-----|-----|
| `GET /maimaidxprober/dev/player/records` | `GET /maimaidxprober/player/records` | `prober.records.read` |
| `POST /maimaidxprober/dev/player/record` | `POST /maimaidxprober/player/record` | `prober.records.read` |
| `POST /maimaidxprober/query/plate` | `POST /maimaidxprober/player/plate` | `prober.records.read` |
| `GET /chunithmprober/dev/player/records` | `GET /chunithmprober/player/records` | `chunithm.records.read` |
| `GET / POST /public/channel_to_qq` | 无替代，直接移除 | —— |

您访问的仍是同一批数据，改变的是「谁允许您访问」的判定方式：过去持有 token 并知晓 QQ 号即可读取任意已注册用户的成绩，此后改为由用户逐个授权、可随时撤销。

## 需要您做的事

**一、补全应用信息。** 用您的水鱼账号登录开发者控制台 <https://auth.diving-fish.com/console> 。您原有 token 对应的应用已经建好并在列表中，但名称是系统生成的占位值（形如「某某的应用」），需要您填写正式名称、用途说明，并勾选实际需要的权限。**在补全之前，该应用无法接受新的用户绑定。**

若列表为空，说明您的 token 在过去 90 天内没有调用记录，未纳入自动迁移，请按《快速开始》重新登记一个应用。

**二、生成 `client_secret` 并改造调用。** 调用方式由「带上 `Developer-Token` ，在参数里写明要查谁」改为两步：先用应用凭据换取一张代表某个用户的 access token（有效期 5 分钟，请在有效期内复用），再携带该令牌请求上表中的新端点。新端点不再接受 `qq` 与 `username` 参数。完整示例见迁移文档。

换票时用于指明「代哪个用户操作」的 `subject` 参数，请直接使用 `ref:` 形式：过渡写法 `subject=qq:123456` 与开发者 token 同日停止工作。这项切换不需要用户重新授权——您手上原本就有的那个 QQ 号，按迁移文档 5.2 节的公式算出摘要即可直接使用。`subject=username:` 不受影响，长期可用。

**三、确认存量用户。** 过去 90 天内您通过 token 实际查询过的用户，其授权记录**已经为您补齐，这些用户无需重新授权**。未覆盖的情况有三种：90 天内未被您查询过的用户、调用时所用的 QQ 号或频道 ID 未绑定到其查分器账号的用户、以及此后主动撤销授权的用户。这三种情况在换票时均表现为 `consent_required` ，请在代码中引导用户完成一次绑定。

## 文档

- 迁移说明（含端点对照、行为差异、常见问题）：<https://maimai.diving-fish.com/manual/docs/developer/oauth-migration>
- 快速开始（两种接入方式的完整示例代码）：<https://maimai.diving-fish.com/manual/docs/developer/oauth-quickstart>
- OAuth 接口文档：<https://maimai.diving-fish.com/manual/docs/developer/oauth-api-document>

## 其他说明

- **在 10 月 1 日之前，您现有的调用不受任何影响**，无需赶在某个时间点前一次性切换。自本次通知起，上述端点的成功响应中会带有 `Sunset` 与 `Deprecation` 响应头，可用于在您的服务中自动告警。
- 若您的服务确实无法在 10 月 1 日前完成改造，请在此日期**之前**回复本邮件说明情况与预计完成时间，我们可为您单独延长数日。逾期未联系的 token 不再单独处理。
- 若您已不再使用该 token ，无需任何操作。

感谢您长期以来对查分器的支持。

—— 舞萌 DX | 中二节奏查分器
