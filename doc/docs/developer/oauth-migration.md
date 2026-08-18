---
sidebar_position: 2
toc_min_heading_level: 2
toc_max_heading_level: 4
---

# 从 Developer-Token 迁移到水鱼账号 OAuth

:::warning
`Developer-Token` 已停止签发，其对应的 `/dev/player/records` 、 `/dev/player/record` 、 `/query/plate` 、 `/channel_to_qq` 端点已进入废弃状态。请在过渡期内完成本文所述的迁移。过渡期的截止时间将通过您登记的联系方式另行通知。
:::

## 1. 变更概述

查分器的第三方数据访问已迁移至水鱼账号的 OAuth 授权体系，授权服务器地址为：

```plaintext
https://auth.diving-fish.com
```

两套体系的差异如下：

| **对比项** | **Developer-Token** | **水鱼账号 OAuth** |
|-----|-----|-----|
| 应用凭据 | 一个长期有效的 Token | `client_id` 与 `client_secret` ，用于换取有效期 5 至 15 分钟的 access token |
| 查询对象的确定方式 | 由请求中的 `qq` 或 `username` 参数指定 | 由 access token 本身决定，请求中不再接受 `qq` 或 `username` |
| 用户许可 | 无。持有 Token 并知晓 QQ 号即可读取任意已注册用户的成绩 | 必须由用户逐个授权，且用户可随时在账号设置中撤销 |
| 权限范围 | 全部只读接口 | 按 scope 逐项申请，逐项审核 |
| 成绩写入 | 不支持 | 支持，需通过人工审核后开放 |
| 频率限制 | 按小时计的整体请求数 | 按应用与按用户分别计算的每日调用配额 |

迁移完成后，您访问的仍然是查分器的同一批数据，改变的是「谁允许您访问」的判定方式。

## 2. 已经为您完成的部分

### 2.1 存量的授权关系已补齐

过去 90 天内，您通过 `Developer-Token` 实际查询过的每一个用户，其授权记录均已写入水鱼账号。**这些用户不需要重新授权**，您的服务在完成第 3 节的改造后即可继续访问他们的数据。

未被补齐的情况有三种，请您预先在代码中处理：

- 该用户在上述 90 天窗口内没有被您查询过；
- 该用户在您调用时提供的是 QQ 号或频道 ID ，但其查分器账号并未绑定该标识；
- 该用户此后主动撤销了对您的授权。

以上三种情况在换票时的表现一致，均为 `consent_required` ，处理方式也一致：引导用户完成一次绑定，具体请参考 [快速开始](./oauth-quickstart.md#4-方式二设备码绑定--换票)。

### 2.2 对应的应用已建好

系统已按您的开发者账号建立了对应的应用，其名称为系统生成的占位值，形如 `某某的应用` ，描述与主页地址为空，且尚未生成 `client_secret` 。您需要在控制台中补全这些信息，见下一节。

:::info
已被禁用的开发者账号，以及在上述 90 天窗口内没有任何调用记录的开发者账号，不在本次迁移范围内。若您属于这两种情况，请按 [快速开始](./oauth-quickstart.md) 重新登记一个应用。
:::

## 3. 迁移步骤

### 3.1 补全应用信息

使用您的水鱼账号登录开发者控制台：

```plaintext
https://auth.diving-fish.com/console
```

您迁移过来的应用已经在列表中。点击进入并补全以下内容：

| **字段** | **要求** |
|-----|-----|
| 应用名称 | 不超过 20 字。它将作为标题显示在用户的授权页上 |
| 应用描述 | 不超过 100 字，说明该应用的用途 |
| 主页地址 | 可留空；如填写，须可公开访问，提交时会实际请求一次以校验 |
| 接入方式 | bot 与命令行工具选择设备码方式；网页或客户端应用选择授权码方式，并登记回调地址 |
| 需要的权限 | 只勾选实际要用的 scope |

提交后，只读权限的申请将被自动审核，结果立即在控制台显示；包含写入权限的申请将转为人工审核，在审核通过之前，写入权限不会生效，只读权限不受影响。

:::warning
**在补全信息之前，您的应用无法接受新的用户绑定。** 迁移过来的应用名称是系统生成的占位值，用户在授权页上无从判断自己正在授权给谁，因此该状态下的绑定请求会被拒绝。已经迁移过来的授权关系不受此限制，您的现有用户不受影响。
:::

### 3.2 生成 client_secret

在控制台的应用详情中生成 `client_secret` 。

:::danger
`client_secret` **只在生成的那一刻显示一次**，服务端保存的是它的哈希值。请立即将其写入您的服务端配置。若已遗失，只能重新生成，重新生成会使原凭据立即失效。

`client_secret` 代表您的整个应用，泄露等同于该应用的全部已授权用户可被读取。请勿将其写入客户端、前端代码或公开仓库。
:::

### 3.3 改为先换票，再请求

原先的调用方式是「带上 `Developer-Token` ，在参数里写明要查谁」：

```plaintext
GET https://www.diving-fish.com/api/maimaidxprober/dev/player/records?qq=123456
Developer-Token: your_developer_token_here
```

新的调用方式分为两步。第一步，用应用凭据与用户标识换取一张代表该用户的 access token ：

```plaintext
POST https://auth.diving-fish.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:diving-fish:params:oauth:grant-type:on-behalf-of
&client_id=your_client_id
&client_secret=your_client_secret
&subject=qq:123456
&scope=prober.records.read
```

第二步，携带该令牌请求对应的新端点：

```plaintext
GET https://www.diving-fish.com/api/maimaidxprober/player/records
Authorization: Bearer eyJ0eXAiOiJhdCtqd3QiLCJhbGciOiJSUzI1NiIsImtpZCI6...
```

换票接口的完整说明见 [OAuth 接口文档](./oauth-api-document.md#43-on-behalf-of-换票代用户获取令牌)，可直接运行的示例代码见 [快速开始](./oauth-quickstart.md#4-方式二设备码绑定--换票)。

:::tip
换来的令牌有效期为 5 分钟，请在有效期内复用，不要每次请求都换一次票。换票接口设有频率限制，见 [配额与限流](./oauth-api-document.md#10-配额与限流)。
:::

### 3.4 改用新端点

`/dev/*` 系列端点的替代端点见第 4 节的对照表。**新端点一律不接受 `qq` 与 `username` 参数**——查询对象由令牌决定，这正是新旧两套体系最本质的区别。

### 3.5 逐步改用 ref 形式的用户标识

上面第 3.3 步使用的 `subject=qq:123456` 是为本次迁移开放的过渡写法，它与 `subject=username:your_username` 一并只在过渡期内可用，且仅对迁移过来的应用开放。长期方案是使用您自己的用户标识的摘要：

```plaintext
subject=ref:<sha256("<client_id>:<您自己的用户标识>")>
```

两种写法的对比与选择依据见第 5 节。请在过渡期结束前完成切换。

## 4. 端点对照表

| **游戏数据类别** | **已废弃的端点** | **替代端点** | **所需 scope** |
|-----|-----|-----|-----|
| `maimaidxprober` | `GET /dev/player/records?qq=` | [`GET /player/records`](./oauth-api-document.md#91-获取用户的完整成绩信息) | `prober.records.read` |
| `maimaidxprober` | `POST /dev/player/record` | [`POST /player/record`](./oauth-api-document.md#92-获取用户的单曲成绩信息) | `prober.records.read` |
| `maimaidxprober` | `POST /query/plate` | [`POST /player/plate`](./oauth-api-document.md#93-按版本获取用户的成绩信息) | `prober.records.read` |
| `chunithmprober` | `GET /dev/player/records?qq=` | [`GET /player/records`](./oauth-api-document.md#94-获取用户的-chunithm-成绩数据) | `chunithm.records.read` |
| `public` | `GET / POST /channel_to_qq` | 无替代，将直接移除 | —— |

端点路径的写法与 [查分器 API 文档](./zh-api-document.md#1-api端点) 一致，完整地址为 `https://www.diving-fish.com/api/{游戏数据类别}/{端点路径}` 。

替代端点的请求体、响应结构与被替代的端点保持一致，仅去掉了 `qq` 与 `username` 参数。 `/channel_to_qq` 在实际使用中没有任何调用记录，因此不提供替代方案。

## 5. 两种用户标识路径

「您的服务如何告诉授权服务器要代哪个用户操作」有两条路径，请根据自身情况选择。

### 5.1 过渡期路径：直接使用 QQ 号或用户名

适用于**迁移过来的应用**，且您原本就是按 QQ 号或查分器用户名来定位用户的。这条路径不需要改动您现有的用户标识存储，只需把参数从业务请求挪到换票请求里。

| **原有参数** | **换票时的 subject** |
|-----|-----|
| `?qq=123456` | `subject=qq:123456` |
| `?username=your_username` | `subject=username:your_username` |

```plaintext
POST https://auth.diving-fish.com/oauth/token

grant_type=urn:diving-fish:params:oauth:grant-type:on-behalf-of
&client_id=your_client_id
&client_secret=your_client_secret
&subject=username:your_username
&scope=prober.records.read
```

:::warning
这两种写法只在过渡期内可用，且仅对迁移过来的应用开放。新登记的应用无法使用。过渡期结束后，服务器将返回：

```json
{"error": "invalid_request", "error_description": "'subject=qq:' is retired for this client; use ref: or sub:"}
```
:::

请注意，`qq:` 的取值同时会匹配用户绑定的 QQ 号与频道 ID ，这与 `Developer-Token` 时代 `qq` 参数的行为一致。

### 5.2 长期路径：使用 ref 摘要

适用于所有应用，也是新登记应用唯一可用的方式。您把自己那一侧的用户标识（QQ 号、频道 ID 、您自己的用户 ID 均可）与 `client_id` 拼接后取 sha256 ，得到一个只对您的应用有意义的摘要：

```python
import hashlib

def subject_ref(client_id: str, external_id: str) -> str:
    return hashlib.sha256(f"{client_id}:{external_id}".encode()).hexdigest()
```

在引导用户绑定时把这个摘要作为 `subject_ref` 参数一并提交，用户点击同意的那一刻，摘要与其查分器账号的映射即告建立，此后即可用 `subject=ref:<摘要>` 换票。具体流程见 [快速开始](./oauth-quickstart.md#4-方式二设备码绑定--换票)。

选择这条路径的理由：

- QQ 号与频道 ID 共用同一个字段，且用户可以随时改绑或解绑，不适合长期作为定位依据；
- 查分器用户名虽然不可修改，但它是全站通用的公开标识，不同应用之间可以据此串联出同一个用户；
- 摘要中混入了 `client_id` ，因此同一个用户在不同应用中的标识互不相同，任一应用的数据泄露都不会暴露该用户在其他应用中的身份；
- 用户在您的服务中未必以 QQ 号出现，这条路径允许您使用自己的用户体系。

### 5.3 补充路径：使用水鱼用户 ID

设备码绑定完成后，若您通过轮询取回了令牌，响应中会额外包含一个 `sub` 字段，即该用户的水鱼用户 ID 。愿意自行保存映射关系的应用可以用 `subject=sub:12345` 换票。该写法长期可用。

## 6. 行为差异

迁移后，以下行为与 `Developer-Token` 时代不同，请在改造时一并确认：

| **项目** | **变化** |
|-----|-----|
| 已设置隐私的用户 | `Developer-Token` 一律返回 403 。授权体系下，用户既然主动授权了您的应用，即可正常读取 |
| 未同意用户协议的用户 | 仍然拒绝，返回 403 ，与此前一致 |
| 成绩掩码 | 用户勾选了「对非网页查询的成绩使用掩码」时，第三方应用读到的仍然是掩码值，与此前一致 |
| 未授权的用户 | 换票阶段即返回 `consent_required` ，不会到达查分器 |
| 不存在的用户 | 同样返回 `consent_required` ，与「未授权」不作区分 |
| 错误码 | 令牌无效返回 401 ， scope 不足返回 403 ，超出配额返回 429 |

:::info
「不存在的用户」与「未授权的用户」返回同一个错误，是有意为之。若两者可以区分，任何持有应用凭据的一方都能借此逐个枚举出哪些 QQ 号在查分器注册过。这一点在您编写错误提示时需要注意：无法据此告诉用户「您还没有查分器账号」，只能提示「请先完成绑定」。
:::

## 7. 常见问题

| **现象** | **原因与处理** |
|-----|-----|
| 换票返回 `consent_required` | 该用户未授权您的应用，或其账号未绑定您提供的标识。引导用户完成一次绑定 |
| 换票返回 `invalid_client` | `client_id` 或 `client_secret` 有误，或该应用已被停用 |
| 换票返回 `invalid_scope` | 申请的 scope 不在该应用已获批准的范围内，请在控制台确认 |
| 换票返回 `slow_down` ，状态码 429 | 换票过于频繁。请缓存 access token 直至其过期，不要每次业务请求都换票 |
| 发起设备码绑定返回 `client profile is incomplete` | 应用信息尚未补全，见 3.1 节 |
| 调用查分器返回 401 | 令牌已过期（有效期 5 分钟），或 `Authorization` 头格式有误 |
| 调用查分器返回 403 且提示缺少权限 | 换票时申请的 scope 不足，或用户授权范围不含该 scope |
| 调用查分器返回 429 | 已超出每日调用配额，见 [配额与限流](./oauth-api-document.md#10-配额与限流) |
| 用户反馈「已经授权但仍然读不到」 | 在控制台的应用详情中查看当前授权用户数与绑定身份数，确认绑定是否真的建立 |

## 8. 相关文档

- [快速开始](./oauth-quickstart.md)：两种接入方式的完整示例代码
- [OAuth 接口文档](./oauth-api-document.md)：全部端点、参数与错误码
- [查分器 API 文档](./zh-api-document.md)：查分器自身的端点说明
