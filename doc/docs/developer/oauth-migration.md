---
sidebar_position: 2
toc_min_heading_level: 2
toc_max_heading_level: 4
---

# 从 Developer-Token 迁移到水鱼账号 OAuth

:::warning
`Developer-Token` 已停止签发，其对应的 `/dev/player/records` 、 `/dev/player/record` 、 `/query/plate` 、 `/channel_to_qq` 端点已进入废弃状态，并将于 **2026 年 10 月 1 日 00:00（UTC+8）** 停止服务，届时一律返回 `410 Gone` 。请在该日期之前完成本文所述的迁移。
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

新的调用方式分为两步。第一步，用应用凭据与用户标识换取一张代表该用户的 access token 。用户标识写作 `ref:` 加上一段摘要，摘要由您原本就在使用的那个标识算出：

```python
import hashlib

# external_id 就是您原来写在 ?qq= 里的那个值
subject = "ref:" + hashlib.sha256(f"{CLIENT_ID}:{external_id}".encode()).hexdigest()
```

```plaintext
POST https://auth.diving-fish.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:diving-fish:params:oauth:grant-type:on-behalf-of
&client_id=your_client_id
&client_secret=your_client_secret
&subject=ref:9a1b2c3d...
&scope=prober.records.read
```

您的存量用户在迁移时已经按这个公式建好了映射，**不需要重新授权**，但摘要必须与迁移时算出的完全一致，务必先读 [5.1 节](#51-ref您自己生成的映射)。

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

## 5. 用户标识 subject

### 5.0 它到底是什么

换票时您要回答一个问题：**这张票代表谁？**

难点在于，您和查分器对同一个人的称呼不一样。您的 bot 认识的是「QQ 号 123456」，查分器认识的是「用户名 someone」，两边谁也不知道对方在说谁。`subject` 参数就是用来搭这座桥的，桥有两种搭法：

**第一种，您自己搭 —— 这就是 `ref`。** 您把自己那边的用户标识算成一段摘要，当作一个只有您和查分器知道的暗号。用户点击同意授权的那一刻，这个暗号就和他的查分器账号对上了号，记在查分器这边。此后您报暗号，查分器就知道是哪个账号。您那边不需要保存任何新东西，因为暗号是随时能从您原有的标识算出来的。

**第二种，用查分器现成的 —— 这就是 `username` 和 `sub`。** 它们本来就是查分器账号自带的标识，映射关系一直都在，不需要您建立。您直接报「用户名 someone」或「用户 ID 12345」，查分器立刻知道是谁。

两种搭法都不会让您读到授权范围以外的数据：桥只负责指人，指到之后仍要检查这个人有没有授权过您的应用，没有就是 `consent_required` 。

| **写法** | **映射关系由谁维护** | **可用性** |
|-----|-----|-----|
| `ref:<摘要>` | 您自己生成，用户授权时建立 | 长期，推荐 |
| `username:<用户名>` | 查分器预留 | 长期 |
| `sub:<用户 ID>` | 查分器预留 | 长期 |
| `qq:<QQ 号>` | 查分器预留 | **2026 年 10 月 1 日 00:00（UTC+8）停止工作** |

### 5.1 ref：您自己生成的映射

适用于所有应用，也是推荐写法。把您那一侧的用户标识（QQ 号、频道 ID 、您自己的用户 ID 均可）与 `client_id` 拼接后取 sha256 ：

```python
import hashlib

def subject_ref(client_id: str, external_id: str) -> str:
    return hashlib.sha256(f"{client_id}:{external_id}".encode()).hexdigest()
```

新用户的映射在设备码绑定时建立：发起绑定时把摘要作为 `subject_ref` 参数一并提交，用户点击同意，映射即告建立，此后用 `subject=ref:<摘要>` 换票。具体流程见 [快速开始](./oauth-quickstart.md#4-方式二设备码绑定--换票)。

#### 存量用户的映射已经建好了，但摘要必须算得分毫不差

:::danger
**这是本次迁移最容易出错的一步。**

您的存量用户在迁移时已经按上面这个公式建好了映射，他们**不需要重新授权**。但摘要是等值查找，只要有一个字节不同就查不到人，服务器会返回 `consent_required` ——和「这个用户没授权过您」是同一个响应，您无法从错误信息中看出是算错了还是真的没授权。

因此请确认三件事：

1. **算法与拼接方式完全一致**：`sha256("<client_id>:<external_id>")` ，中间是一个半角冒号，取小写十六进制，共 64 位。不要加盐、不要换成别的哈希、不要 base64 。
2. **`external_id` 用的是当年那个值**：迁移时取的是您调用 `/dev/*` 时在 `qq` 或 `username` 参数中**实际传入的原值**。当年传的是 QQ 号就用 QQ 号，传的是频道 ID 就用频道 ID （它当年混在 `qq` 参数里传入，同样按原值建立），传的是用户名就用用户名。**换成您自己的内部用户 ID 会算出另一个摘要，映射不存在，这些用户就得重新授权一次。**
3. **`client_id` 用的是这个应用自己的**：摘要里混入了 `client_id` ，用错应用的凭据算出来的摘要同样对不上。

建议先验证再全量切换：任取一个您近期查询过的用户，用其标识算出摘要换一次票。成功即说明映射命中；若返回 `consent_required` ，先检查上面三条，再考虑该用户是否属于未被补齐的三种情形（见 2.1 节）。
:::

选择这条写法的理由：

- 摘要中混入了 `client_id` ，因此同一个用户在不同应用中的标识互不相同，任一应用的数据泄露都不会暴露该用户在其他应用中的身份；
- 用户在您的服务中未必以 QQ 号出现，这条写法允许您使用自己的用户体系；
- 它不依赖查分器账号上任何可变的字段，用户改绑 QQ 、改换绑定方式都不影响已建立的映射。

### 5.2 username：查分器预留的用户名

**所有应用均可使用，长期有效，无需申请。**

```plaintext
subject=username:your_username
```

取值为查分器用户名，映射关系由查分器维护，您不需要事先建立任何东西。

它解决的是 `ref` 覆盖不到的场景：**用户名由第三方在查询时临时给出**。例如群聊中一位用户要求您的 bot 查询另一位用户的成绩，而后者的标识您在绑定阶段从未记录过，因此算不出可命中的摘要。

这种写法不会让您读到授权范围以外的数据。解析出用户之后仍需通过该用户对您的应用的授权检查，未授权者一律返回 `consent_required` ，且与用户不存在的情形无法区分。因此您能够查到的始终是自己的已授权用户集合。

:::info
被查询的用户是否愿意以这种方式被他人查询，属于您的产品设计范畴。用户授权您的应用，即意味着同意由您的应用使用其成绩数据；若用户不希望如此，正确的做法是不授权，或随时在账号设置中撤销。
:::

### 5.3 sub：查分器预留的用户 ID

**所有应用均可使用，长期有效。**

```plaintext
subject=sub:12345
```

设备码绑定完成后，若您通过轮询取回了令牌，响应中会额外包含一个 `sub` 字段，即该用户的水鱼用户 ID 。愿意自行保存这份对应关系的应用可以用它换票。

### 5.4 qq：过渡期写法，10 月 1 日停止工作

```plaintext
subject=qq:123456
```

仅对迁移过来的应用开放，新登记的应用无法使用。取值同时匹配用户绑定的 QQ 号与频道 ID ，与 `Developer-Token` 时代 `qq` 参数的行为一致。

:::warning
该写法**将于 2026 年 10 月 1 日 00:00（UTC+8）停止工作**，与 `Developer-Token` 同时。届时服务器将返回：

```json
{"error": "invalid_request", "error_description": "'subject=qq:' is retired for this client; use ref: or sub:"}
```

请在该日期之前改用 5.1 的 `ref:` ：您手上已经有这个 QQ 号，按公式算出摘要即可，用户不需要做任何事。
:::

保留期限止于此日的原因：QQ 号与频道 ID 共用同一个字段，用户可以随时改绑或解绑，改绑之后同一个取值指向的将是另一个账号；而它并不提供 `ref` 之外的任何能力。

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
