---
sidebar_position: 4
toc_min_heading_level: 2
toc_max_heading_level: 4
---

# 水鱼账号 OAuth 接口文档

本文是水鱼账号授权服务器与查分器 OAuth 端点的完整说明。若您是初次接入，建议先阅读 [快速开始](./oauth-quickstart.md)；若您正在从 `Developer-Token` 迁移，请先阅读 [迁移指南](./oauth-migration.md)。

## 1. 端点

水鱼账号授权服务器（以下简称授权服务器）的地址为：

```plaintext
https://auth.diving-fish.com
```

:::tip
**请在代码中只硬编码上述根地址，其余端点一律从发现文档读取。** 这样端点日后有所调整时，您不需要修改代码。
:::

发现文档遵循 OpenID Connect Discovery 与 RFC 8414 两套路径，内容相同：

| **端点路径** | **请求方法** | **说明** |
|-----|-----|-----|
| `/.well-known/openid-configuration` | GET | OIDC 发现文档 |
| `/.well-known/oauth-authorization-server` | GET | 同上，供只识别此路径的客户端库使用 |
| `/.well-known/jwks.json` | GET | 验签公钥集合，建议缓存 5 分钟 |

标准 OIDC 客户端库（如 `authlib` 、 `oidc-client-ts` 、 `openid-client` ）只需提供上述发现文档地址即可自动完成配置。

发现文档中声明的端点如下：

| **端点路径** | **请求方法** | **说明** | **参见** |
|-----|-----|-----|-----|
| `/oauth/authorize` | GET / POST | 授权端点 | [第 3 节](#3-授权端点) |
| `/oauth/token` | POST | 令牌端点 | [第 4 节](#4-令牌端点) |
| `/oauth/device_authorization` | POST | 设备码端点 | [第 5 节](#5-设备码端点) |
| `/oauth/userinfo` | GET / POST | 用户信息端点 | [第 7 节](#7-用户信息端点) |
| `/oauth/revoke` | POST | 撤销端点 | [第 8 节](#8-撤销端点) |
| `/oauth/logout` | GET / POST | 登出端点 | [第 8 节](#8-撤销端点) |

此外还有两个供用户使用的页面：

| **地址** | **说明** |
|-----|-----|
| `https://auth.diving-fish.com/console` | 开发者控制台：登记应用、补全信息、生成 `client_secret` |
| `https://auth.diving-fish.com/device` | 设备码绑定页：用户在此输入用户码并确认授权 |

## 2. scope

| **scope** | **性质** | **含义** |
|-----|-----|-----|
| `openid` | 身份 | 必须携带，否则无法取得 `id_token` ，也无法调用 `/oauth/userinfo` |
| `profile` | 读取 | 用户名、昵称 |
| `prober.profile.read` | 读取 | 查分器资料：段位、姓名框、绑定的 QQ 号 |
| `prober.records.read` | 读取 | 读取舞萌 DX 成绩。**大部分 bot 只需要这一项** |
| `prober.records.write` | 写入 | 代用户上传、修改舞萌 DX 成绩 |
| `chunithm.records.read` | 读取 | 读取 CHUNITHM 成绩 |
| `chunithm.records.write` | 写入 | 代用户上传、修改 CHUNITHM 成绩 |

多个 scope 之间以空格分隔。

请只申请实际用到的 scope 。申请项越多，用户在授权页上放弃授权的概率越大，凭据泄露时的波及面也越大。

:::info
含写入权限的申请一律转为人工审核。在审核通过之前，该应用取得的令牌中不会包含任何写入 scope ，只读部分不受影响。
:::

## 3. 授权端点

| **端点路径** | **请求方法** |
|-----|-----|
| `/oauth/authorize` | GET / POST |

供有回调地址的应用使用。将用户浏览器导向该地址，用户登录并同意后，浏览器携带授权码跳回您登记的回调地址。

### 3.1 请求参数

| **参数** | **必填** | **说明** |
|-----|-----|-----|
| `response_type` | 是 | 固定为 `code` |
| `client_id` | 是 | 您的应用标识 |
| `redirect_uri` | 是 | 必须与登记值**完全一致**，尾斜杠、协议、端口都计入比较 |
| `scope` | 是 | 空格分隔的 scope 列表 |
| `state` | 是 | 随机串，回调时原样返回。您必须自行保存并核对 |
| `nonce` | 否 | 随机串，将写入 `id_token` ，用于防止重放 |
| `code_challenge` | 是 | `code_verifier` 的 sha256 摘要，经 base64url 编码且去掉填充 |
| `code_challenge_method` | 是 | 固定为 `S256` |

:::warning
**PKCE 为强制要求，机密客户端也不例外。** 缺少 `code_challenge` 的请求直接返回 400 ； `code_challenge_method` 只接受 `S256` ，不接受 `plain` 。
:::

### 3.2 响应

用户同意后跳转至：

```plaintext
<redirect_uri>?code=your_authorization_code&state=your_state
```

**请务必先核对 `state` ，不一致则丢弃本次回调。** 这是防止 CSRF 的唯一手段。

授权码为一次性，有效期 60 秒。重复使用不仅会失败，还会连带吊销由该授权码换出的令牌。

用户拒绝授权时跳转至：

```plaintext
<redirect_uri>?error=access_denied&state=your_state
```

## 4. 令牌端点

| **端点路径** | **请求方法** | **请求体格式** |
|-----|-----|-----|
| `/oauth/token` | POST | `application/x-www-form-urlencoded` |

**客户端认证。** 应用登记时选定的**部署形态**决定了它属于哪一类客户端，二者的认证方式不同：

| **部署形态** | **客户端类型** | **认证方式** | **可用的 `grant_type`** |
|-----|-----|-----|-----|
| 由开发者自己部署运行 | 机密客户端 | 每次请求携带 `client_secret` | 授权码 / 刷新 / 设备码 / 换票 |
| 分发给用户各自部署 | 公开客户端 | 不携带 `client_secret` ，由 PKCE 与令牌本身担保 | 授权码 / 刷新 / 设备码 |

机密客户端的 `client_secret` 写在请求体中（`client_secret_post`）。

:::danger
**认证方式按登记值严格比对，多传与少传同样会被拒。**

机密客户端未携带 `client_secret` ，或公开客户端携带了 `client_secret` ，令牌端点均返回 401 `invalid_client` ，两种情形的响应完全相同。若您在接入之初就持续收到 401 ，请先在控制台确认该应用的部署形态，以及机密客户端的 `client_secret` 是否已经生成——**登记应用与生成 `client_secret` 是两个独立的动作**，只完成前者时该应用没有任何可用凭据。
:::

该端点支持四种 `grant_type` 。

### 4.1 authorization_code 授权码换取令牌

| **参数** | **必填** | **说明** |
|-----|-----|-----|
| `grant_type` | 是 | `authorization_code` |
| `code` | 是 | 授权端点返回的授权码 |
| `redirect_uri` | 是 | 与授权请求中完全一致 |
| `client_id` | 是 | 应用标识 |
| `client_secret` | 视情况 | 机密客户端必填，公开客户端不传 |
| `code_verifier` | 是 | 生成 `code_challenge` 时所用的原串 |

响应：

```json
{
    "token_type": "Bearer",
    "access_token": "eyJ0eXAiOiJhdCtqd3QiLCJhbGciOiJSUzI1NiIsImtpZCI6...",
    "expires_in": 900,
    "refresh_token": "your_refresh_token",
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6...",
    "scope": "openid profile prober.records.read"
}
```

### 4.2 refresh_token 刷新令牌

| **参数** | **必填** | **说明** |
|-----|-----|-----|
| `grant_type` | 是 | `refresh_token` |
| `refresh_token` | 是 | 当前持有的 refresh token |
| `client_id` | 是 | 应用标识 |
| `client_secret` | 视情况 | 机密客户端必填 |

响应结构与 4.1 相同。refresh token 有效期为 30 天。

:::danger
**refresh token 强制轮换：每次刷新都会签发一把新的，旧的立即作废。**

旧的 refresh token 再次出现时，服务器会将其视为凭据泄露，**吊销整条令牌链，包括本次刚刚签发的那一把**，用户需要重新授权。这是发现 refresh token 被窃取的唯一手段，因此不会放宽。

实践上需要注意三点：不要并发刷新（多个线程或进程同时持同一把令牌去刷，第二个即触发吊销）；新令牌必须在使用前完成持久化，不要等到进程退出时才落盘；不要在多台机器上共享同一把 refresh token 。
:::

### 4.3 on-behalf-of 换票：代用户获取令牌

这是查分器体系的自定义授权类型，供已经取得用户授权的服务端应用使用。它以「应用凭据 + 用户标识」换取一张代表该用户的短期令牌。

| **参数** | **必填** | **说明** |
|-----|-----|-----|
| `grant_type` | 是 | `urn:diving-fish:params:oauth:grant-type:on-behalf-of` |
| `client_id` | 是 | 应用标识 |
| `client_secret` | 是 | **必填。公开客户端不能使用该授权类型**，改用 [4.4 节](#44-device_code-设备码换取令牌)的设备码取得 refresh token |
| `subject` | 是 | 用户标识，四种写法见 [第 6 节](#6-用户标识-subject) |
| `scope` | 否 | 不填则取「用户授权范围」与「应用已获批准范围」的交集 |

响应中**没有 refresh token** ，这条路径不需要它：

```json
{
    "token_type": "Bearer",
    "access_token": "eyJ0eXAiOiJhdCtqd3QiLCJhbGciOiJSUzI1NiIsImtpZCI6...",
    "expires_in": 300,
    "scope": "prober.records.read"
}
```

服务端在签发前会依次校验三项，缺一不可：

1. `client_secret` 是否正确，即您是哪个应用；
2. 该用户是否授权过您的应用；
3. 本次申请的 scope 是否在用户的授权范围之内。

:::info
`subject` 只是**查找键，不是凭据**。这是它与 `Developer-Token` 时代 `qq` 参数最本质的区别：过去知道 QQ 号加上任意一个开发者 Token 即可读取该用户的成绩，现在它只能在「已授权集合」中查表命中。
:::

:::warning
令牌有效期只有 5 分钟。它比授权码方式的 15 分钟更短，是因为这条路径上的令牌不落库、不可即时吊销，用户撤销授权只能等令牌自然过期后生效。请在有效期内复用令牌，不要每次业务请求都换票。
:::

错误响应：

| **error** | **状态码** | **含义** |
|-----|-----|-----|
| `consent_required` | 400 | 该用户未授权您的应用，或该用户不存在。两者不作区分 |
| `consent_required` （描述含 `scope not granted`） | 400 | 用户已授权，但本次申请的 scope 超出其授权范围 |
| `invalid_client` | 401 | `client_id` 或 `client_secret` 有误，或应用已停用 |
| `invalid_scope` | 400 | 申请的 scope 不在该应用已获批准的范围内 |
| `invalid_request` | 400 | `subject` 缺失或格式错误 |
| `unauthorized_client` | 400 | 该应用未被允许使用此授权类型 |
| `slow_down` | 429 | 换票过于频繁，见 [第 10 节](#10-配额与限流) |

:::info
「该用户未授权」与「该用户不存在」返回同一个错误，是有意为之。若两者可以区分，`subject=qq:` 就成了一个「这个 QQ 号在查分器注册过没有」的枚举接口。

对您而言两种情况的处理方式完全相同：引导用户完成一次绑定。
:::

### 4.4 device_code 设备码换取令牌

| **参数** | **必填** | **说明** |
|-----|-----|-----|
| `grant_type` | 是 | `urn:ietf:params:oauth:grant-type:device_code` |
| `device_code` | 是 | 设备码端点返回的设备码 |
| `client_id` | 是 | 应用标识 |
| `client_secret` | 视情况 | 机密客户端必填 |

用户尚未操作时返回 `authorization_pending` ，轮询过快时返回 `slow_down` ，用户拒绝时返回 `access_denied` ，设备码过期时返回 `expired_token` 。

成功时的响应在标准字段之外，额外包含一个 `sub` 字段，即该用户的水鱼用户 ID ：

```json
{
    "token_type": "Bearer",
    "access_token": "eyJ0eXAiOiJhdCtqd3QiLCJhbGciOiJSUzI1NiIsImtpZCI6...",
    "expires_in": 900,
    "scope": "prober.records.read",
    "sub": "12345"
}
```

同一个设备码只能换取一次令牌，换取后即失效。

**公开客户端的响应中还包含 `refresh_token`** ，此后凭它按 [4.2 节](#42-refresh_token-刷新令牌)自行续期。这是公开客户端取得长期访问能力的唯一途径：它不能使用换票，因此**必须轮询**，且必须为每位用户各自保存这把令牌。机密客户端不在此列——它的 `grant_type` 中不含 `refresh_token` ，续期请走换票。

## 5. 设备码端点

| **端点路径** | **请求方法** | **请求体格式** |
|-----|-----|-----|
| `/oauth/device_authorization` | POST | `application/x-www-form-urlencoded` |

供没有浏览器、也无法开放公网回调地址的应用使用，用于引导用户完成一次绑定。

### 5.1 请求参数

| **参数** | **必填** | **说明** |
|-----|-----|-----|
| `client_id` | 是 | 应用标识 |
| `client_secret` | 视情况 | 机密客户端必填 |
| `scope` | 是 | 本次绑定申请的权限，必须在应用已获批准的范围内 |
| `subject_ref` | 否 | 您自己的用户标识的摘要，见 [6.1 节](#61-ref应用自有标识的摘要)。仅供换票使用，公开客户端用不到 |
| `binding_label` | 否 | 遮挡后的身份展示串，例如 `QQ 11****14` ，最长 64 字符 |

:::warning
`binding_label` 虽非必填，但**请务必填写**。

设备码流程没有回调地址，用户无从通过「跳转到哪里」判断自己在授权给谁。若攻击者向您的应用索要一条绑定链接（其中的标识是攻击者自己的）并转发给受害者，受害者点击同意后，攻击者即可通过您的应用读写受害者的数据。同意页上那一行「绑定身份」，是受害者唯一可能察觉异常的地方。

该字段会被作为不可信文本处理，即转义后截断显示。
:::

:::danger
**公开客户端另有一重风险：该端点不校验凭据，任何人都能用您的 `client_id` 生成绑定链接。**

对机密客户端而言，冒名者最多只能让受害者绑到自己的标识上；而公开客户端在轮询中直接取得用户的 refresh token ，冒名者把链接转发给受害者、受害者点击同意之后，对方即持有该账号的长期访问权限。

因此请让用户**在您的程序界面中看到那串用户码**，不要以「把这个链接发给需要绑定的人」的形式使用它。同意页会对公开客户端额外提示这一点，但那是最后一道防线，不是第一道。
:::

### 5.2 响应

```json
{
    "device_code": "your_device_code",
    "user_code": "BCDF-GHJK",
    "verification_uri": "https://auth.diving-fish.com/device",
    "verification_uri_complete": "https://auth.diving-fish.com/device?user_code=BCDF-GHJK",
    "expires_in": 600,
    "interval": 5
}
```

将 `verification_uri_complete` 提供给用户即可。用户码有效期为 10 分钟。

对机密客户端而言，用户点击同意的那一刻，授权记录与 `subject_ref` 的映射即告建立，因此**轮询并非必需**：您可以不理会 `device_code` ，下一次换票自然会成功。轮询的价值在于明确知晓用户点击的是同意还是拒绝。

公开客户端则**必须轮询**：它无法换票，用户令牌只在这一次轮询的响应中出现。

### 5.3 错误响应

| **error** | **含义** |
|-----|-----|
| `invalid_client` | `client_id` 或 `client_secret` 有误 |
| `unauthorized_client` | 该应用未被允许使用设备码方式 |
| `unauthorized_client` （描述含 `client profile is incomplete`） | 应用信息尚未补全，见 [迁移指南 3.1 节](./oauth-migration.md#31-补全应用信息) |
| `unauthorized_client` （描述含 `client is disabled`） | 该应用已被停用 |
| `invalid_scope` | 申请的 scope 不在该应用已获批准的范围内 |
| `invalid_request` | `subject_ref` 格式错误，须为小写十六进制的 sha256 摘要 |
| `slow_down` | 发起绑定过于频繁，见 [第 10 节](#10-配额与限流) |

## 6. 用户标识 subject

换票时的 `subject` 参数用于指明「代哪个用户操作」。共有四种写法。

### 6.1 ref：应用自有标识的摘要

**长期方案，所有应用均可使用。**

```plaintext
subject=ref:9a1b2c3d...
```

摘要的计算方式为：

```python
import hashlib

def subject_ref(client_id: str, external_id: str) -> str:
    """external_id 是您的应用自己使用的用户标识，QQ 号、频道 ID、自有用户 ID 均可。"""
    return hashlib.sha256(f"{client_id}:{external_id}".encode()).hexdigest()
```

必须为小写十六进制，共 64 位。该摘要与用户账号的映射在设备码绑定完成时建立，因此使用这种写法前，需要用户走一次 [设备码绑定](#5-设备码端点)，且发起绑定时提交了对应的 `subject_ref` 。

由 `Developer-Token` 迁移而来的应用是例外：其存量映射已在迁移时一并建好，**这些用户无需重新绑定**，但摘要必须与迁移时算出的完全一致——算法、拼接方式、`external_id` 的取值任一不同都会查不到人，且返回的同样是 `consent_required` 。详见 [迁移文档 5.1 节](./oauth-migration.md#51-ref您自己生成的映射)。

采用这种写法的理由：摘要中混入了 `client_id` ，同一个用户在不同应用中的标识互不相同，任一应用的数据泄露都不会暴露该用户在其他应用中的身份；同时它允许您使用自己的用户体系，不必要求用户在您的服务中以 QQ 号出现。

### 6.2 sub：水鱼用户 ID

**长期方案，所有应用均可使用。**

```plaintext
subject=sub:12345
```

取值为水鱼用户 ID ，即设备码换取令牌时响应中的 `sub` 字段，也是 access token 中 `sub` claim 的值。适用于愿意自行保存映射关系的应用。

### 6.3 qq：QQ 号

**过渡方案，仅对从 `Developer-Token` 迁移过来的应用开放，且将于 2026 年 10 月 1 日 00:00（UTC+8）停止工作**，与 `Developer-Token` 同时。

```plaintext
subject=qq:123456
```

取值同时匹配用户绑定的 QQ 号与频道 ID ，与 `Developer-Token` 时代 `qq` 参数的行为一致。

请在该日期之前改用 6.1 的 `ref` ：您手上已经有这个 QQ 号，按 6.1 的公式算出摘要即可，不需要用户重新绑定（见 [迁移文档 5.1 节](./oauth-migration.md#51-ref您自己生成的映射)）。届时该写法将返回：

```json
{"error": "invalid_request", "error_description": "'subject=qq:' is retired for this client; use ref: or sub:"}
```

保留期限止于此日的原因：QQ 号与频道 ID 共用同一个字段，用户可以随时改绑或解绑，改绑之后同一个取值指向的将是另一个账号；而它并不提供 `ref` 之外的任何能力。

### 6.4 username：查分器用户名

**长期方案，所有应用均可使用。**

```plaintext
subject=username:your_username
```

取值为查分器用户名。

这种写法解决的是 6.1 与 6.2 都覆盖不到的场景：**用户名由第三方在查询时临时给出**，例如群聊中一位用户要求您的 bot 查询另一位用户的成绩，而后者的标识您在绑定阶段从未记录过，因而算不出可命中的 `ref` 摘要。

它不会让您读到授权范围以外的数据：解析出用户后仍需通过该用户对您的应用的授权检查，未授权者一律返回 `consent_required` ，与用户不存在的情形无法区分。因此能够查到的始终是您自己的已授权用户集合。

:::warning
仅 6.3 一种写法有截止时间，见该节。6.4 长期可用。
:::

## 7. 用户信息端点

| **端点路径** | **请求方法** | **权限要求** |
|-----|-----|-----|
| `/oauth/userinfo` | GET / POST | 携带 `openid` scope 的 access token |

```plaintext
GET https://auth.diving-fish.com/oauth/userinfo
Authorization: Bearer your_access_token
```

```json
{
    "sub": "12345",
    "preferred_username": "your_username",
    "name": "your_nickname",
    "nickname": "your_nickname"
}
```

返回哪些字段取决于令牌的 scope 。

:::tip
请通过该端点获取用户资料，不要把用户资料塞进 access token 自行解析——令牌会进入日志与代理缓存，其中不应包含个人信息。
:::

## 8. 撤销端点

用户可以随时在水鱼账号的设置页中撤销对您的授权，撤销后您持有的相关令牌立即失效。您也可以主动撤销：

| **端点路径** | **请求方法** |
|-----|-----|
| `/oauth/revoke` | POST |

| **参数** | **必填** | **说明** |
|-----|-----|-----|
| `token` | 是 | 要撤销的令牌 |
| `token_type_hint` | 否 | `refresh_token` 或 `access_token` |
| `client_id` | 是 | 应用标识 |
| `client_secret` | 视情况 | 机密客户端必填 |

登出端点用于结束用户在水鱼账号的登录会话：

```plaintext
GET https://auth.diving-fish.com/oauth/logout?id_token_hint=your_id_token&post_logout_redirect_uri=your_registered_uri&state=your_state
```

`post_logout_redirect_uri` 必须是该应用登记过的地址，否则只执行登出，不予跳转。

## 9. 查分器端点

取得 access token 后，即可携带它请求查分器：

```plaintext
GET https://www.diving-fish.com/api/maimaidxprober/player/records
Authorization: Bearer your_access_token
```

**请求中不需要、也不接受 `qq` 与 `username` 参数**，查询对象由令牌决定。

端点路径的写法与 [查分器 API 文档](./zh-api-document.md#1-api端点) 一致，即：

```plaintext
https://www.diving-fish.com/api/{游戏数据类别}/{端点路径}
```

支持 Bearer 令牌的端点如下。这些端点同时也接受 [登录验证](./zh-api-document.md#24-登录验证) 与 [Import-Token](./zh-api-document.md#22-import-token验证要求)，三种验证方式择一即可。

| **游戏数据类别** | **端点路径** | **请求方法** | **所需 scope** | **替代的旧端点** |
|-----|-----|-----|-----|-----|
| `maimaidxprober` | [`/player/records`](#91-获取用户的完整成绩信息) | GET | `prober.records.read` | `/dev/player/records` |
| `maimaidxprober` | [`/player/record`](#92-获取用户的单曲成绩信息) | POST | `prober.records.read` | `/dev/player/record` |
| `maimaidxprober` | [`/player/plate`](#93-按版本获取用户的成绩信息) | POST | `prober.records.read` | `/query/plate` |
| `maimaidxprober` | `/player/update_records` | POST | `prober.records.write` | —— |
| `maimaidxprober` | `/player/update_records_html` | POST | `prober.records.write` | —— |
| `maimaidxprober` | `/player/update_record` | POST | `prober.records.write` | —— |
| `maimaidxprober` | `/player/delete_records` | DELETE | `prober.records.write` | —— |
| `chunithmprober` | [`/player/records`](#94-获取用户的-chunithm-成绩数据) | GET | `chunithm.records.read` | `/dev/player/records` |
| `chunithmprober` | `/player/update_records` | POST | `chunithm.records.write` | —— |
| `chunithmprober` | `/player/update_records_html` | POST | `chunithm.records.write` | —— |
| `chunithmprober` | `/player/delete_records` | DELETE | `chunithm.records.write` | —— |

写入类端点的请求体与响应结构，与 [查分器 API 文档](./zh-api-document.md) 中同名端点的说明一致，此处不再重复。

### 9.1 获取用户的完整成绩信息

| **游戏数据类别** | **端点路径** | **请求方法** | **所需 scope** |
|-----|-----|-----|-----|
| `maimaidxprober` | `/player/records` | GET | `prober.records.read` |

无需任何参数。响应结构与 [查分器 API 文档 3.1.5](./zh-api-document.md#315-获取用户的完整成绩信息) 中 `/dev/player/records` 的响应完全一致：

```json
{
    "username": "your_username",
    "nickname": "your_nickname",
    "rating": 15000,
    "additional_rating": 22,
    "plate": "舞神",
    "records": []
}
```

:::tip
完整成绩信息的数据量较大。若您只需要用于绘制 b50 的简略成绩信息，请使用无需验证的 [`/query/player`](./zh-api-document.md#317-获取用户的简略成绩信息) 端点；若您只需要其中一部分成绩，可以用查询参数在服务端过滤，详见 [服务端过滤](./zh-api-document.md#服务端过滤)。
:::

### 9.2 获取用户的单曲成绩信息

| **游戏数据类别** | **端点路径** | **请求方法** | **所需 scope** |
|-----|-----|-----|-----|
| `maimaidxprober` | `/player/record` | POST | `prober.records.read` |

请求体为 JSON ，包含 `music_id` 参数，可以是单个值，也可以是列表：

```json
{"music_id": [11663, 834]}
```

响应结构与 [查分器 API 文档 3.1.6](./zh-api-document.md#316-获取用户的单曲成绩信息) 一致，为以歌曲 ID 为键、该歌曲各难度成绩数组为值的对象。

### 9.3 按版本获取用户的成绩信息

| **游戏数据类别** | **端点路径** | **请求方法** | **所需 scope** |
|-----|-----|-----|-----|
| `maimaidxprober` | `/player/plate` | POST | `prober.records.read` |

请求体为 JSON ，包含 `version` 参数，**必须为列表，即使只有一个元素**：

```json
{"version": ["maimai"]}
```

响应结构与 [查分器 API 文档 3.1.8](./zh-api-document.md#318-按版本获取用户的成绩信息) 一致：

```json
{"verlist": []}
```

:::tip
本端点的功能已并入 `/player/records` 的过滤参数：`GET /player/records?plate=真` 按牌子筛选，`?version=...` 按版本筛选，且返回结构与其他成绩端点一致。详见 [服务端过滤](./zh-api-document.md#服务端过滤)。
:::

### 9.4 获取用户的 CHUNITHM 成绩数据

| **游戏数据类别** | **端点路径** | **请求方法** | **所需 scope** |
|-----|-----|-----|-----|
| `chunithmprober` | `/player/records` | GET | `chunithm.records.read` |

即 `https://www.diving-fish.com/api/chunithmprober/player/records` 。无需任何参数，也可以用查询参数在服务端过滤，详见 [查分器 API 文档 3.2.3 的服务端过滤](./zh-api-document.md#服务端过滤-1)。响应结构与 [查分器 API 文档 3.2.3](./zh-api-document.md#323-获取用户的完整成绩数据) 中 `/dev/player/records` 的响应完全一致：

```json
{
    "username": "your_username",
    "nickname": "your_nickname",
    "rating": 16.5,
    "records": {"best": [], "r10": []}
}
```

### 9.5 错误响应

| **状态码** | **响应体** | **含义** |
|-----|-----|-----|
| 401 | `{"status": "error", "message": "<验签失败的原因>"}` | 令牌无效、已过期，或 `Authorization` 头格式有误。请重新换取令牌 |
| 403 | `{"status": "error", "message": "access token 缺少权限：..."}` | 令牌中缺少该端点所需的 scope |
| 403 | `{"status": "error", "message": "该用户未同意用户协议"}` | 该用户未同意查分器的用户协议 |
| 400 | `{"status": "error", "message": "用户不存在"}` | 令牌中的用户已注销 |
| 429 | `{"status": "error", "message": "已超出今日请求上限"}` | 见 [第 10 节](#10-配额与限流) |
| 503 | `{"status": "error", "message": "服务端未启用 OAuth"}` | 服务端暂时未启用该验证方式 |

### 9.6 与 Developer-Token 时代的行为差异

| **项目** | **变化** |
|-----|-----|
| 已设置隐私的用户 | `Developer-Token` 一律返回 403 。授权体系下，用户既然主动授权了您的应用，即可正常读取 |
| 未同意用户协议的用户 | 仍然拒绝，返回 403 ，与此前一致 |
| 成绩掩码 | 用户勾选「对非网页查询的成绩使用掩码」时，第三方应用读到的仍是掩码值，与此前一致 |
| 未授权的用户 | 在换票阶段即返回 `consent_required` ，请求不会到达查分器 |

## 10. 配额与限流

限制分为两层，作用对象不同。

### 10.1 接口调用配额

由查分器执行，按自然日（UTC）计算，超出后返回 429 。

| **维度** | **默认额度** |
|-----|-----|
| 每个应用对每位用户 | 每日 200 次 |
| 每个应用合计 | 每日 `1000 + 授权用户数 × 20` 次 |

一次查分通常对应一次成绩拉取，因此每位用户每日 200 次对正常使用场景是充裕的。

应用维度的额度跟随您的授权用户数增长，因此不需要随规模扩大反复申请调整。其中的基础量 1000 次是为用户数尚未积累起来的应用预留的余量，调试、重试与定时批量刷新都发生在这一阶段。授权用户数的变化会在数分钟内反映到额度上。

若您的服务确有特殊需求，无法被上述额度覆盖，请通过控制台联系。

### 10.2 授权服务器限流

由授权服务器执行，用于防止滥用，超出后返回 `slow_down` 与状态码 429 。

| **动作** | **限制** |
|-----|-----|
| 换票（同一应用对同一用户） | 每小时 60 次 |
| 换票（同一应用合计） | 每小时 3000 次 |
| 发起设备码绑定（同一应用） | 每小时 600 次 |

:::tip
正常实现会把令牌缓存到过期，5 分钟一张，一小时最多换 12 次。若您触及了每小时 60 次的上限，通常意味着令牌没有被缓存，或存在重复换票的逻辑。
:::

### 10.3 未审核应用的用户数上限

未通过审核的应用，授权用户数上限为 50 。通过审核后取消该限制。

## 11. 校验 access token

本节供自建资源服务器的开发者参考。若您只是调用查分器接口，可以跳过。

access token 是 RS256 签名的 JWT ，请在本地验签，不要每次都请求授权服务器。

```python
import time

import requests
from joserfc import jwt
from joserfc.jwk import KeySet

ISSUER = "https://auth.diving-fish.com"
jwks = KeySet.import_key_set(
    requests.get(f"{ISSUER}/.well-known/jwks.json", timeout=10).json()
)

def verify(token: str) -> dict:
    decoded = jwt.decode(token, jwks, algorithms=["RS256"])
    claims = decoded.claims
    assert claims["iss"] == ISSUER
    assert claims["exp"] > time.time()
    return claims
```

必须校验的项目：`iss` 、 `exp` 、 `aud` ，以及**本次操作所需的 scope 是否在 `scope` 之中**。不校验 scope 等同于没有做授权。

令牌中的 claim ：

| **claim** | **说明** |
|-----|-----|
| `sub` | 水鱼用户 ID 。它是账号的唯一标识，不随用户资料的任何改动而变化 |
| `scope` | 空格分隔的 scope 列表 |
| `client_id` | 签发给哪个应用 |
| `aud` | 该令牌的目标受众。涉及查分器数据的令牌会包含查分器的资源标识 |
| `act` | 仅 on-behalf-of 换来的令牌包含。其中的 `client_id` 表明本次操作由应用代为发起 |
| `df_quota` | 调用配额，`u` 为每用户每日额度，`c` 为每应用每日额度 |
| `iss` / `exp` / `iat` / `jti` | 标准字段 |

JWKS 缓存 5 分钟即可。密钥轮换时，新的 `kid` 会先出现在 JWKS 中，再开始用于签名，因此缓存不会导致验签失败。

:::warning
access token 不查库，**不可即时吊销**，最长存在 15 分钟的窗口。需要立即切断访问时，请撤销 refresh token ；用户在设置页撤销授权时会自动执行这一步。
:::

## 12. 常见错误

| **现象** | **原因** |
|-----|-----|
| 授权页返回 400 ，提示缺少 `code_challenge` | 未实现 PKCE 。所有客户端均须实现 |
| 授权页返回 400 ，提示 `redirect_uri` 未登记 | 与登记值不完全一致，尾斜杠、协议、端口都计入比较 |
| 令牌端点返回 401 `invalid_client` | 机密客户端未传 `client_secret` 、公开客户端多传了 `client_secret` ，或 `client_secret` 尚未生成，见 [第 4 节](#4-令牌端点) |
| 令牌端点返回 400 `invalid_grant` | 授权码已过期（超过 60 秒）、已被使用，或 `code_verifier` 不正确 |
| 刷新后所有令牌突然失效 | 并发刷新，或旧的 refresh token 被重复使用，见 [4.2 节](#42-refresh_token-刷新令牌) |
| 换票返回 `consent_required` | 该用户未授权，或其账号未绑定您提供的标识，见 [4.3 节](#43-on-behalf-of-换票代用户获取令牌) |
| 发起绑定返回 `client profile is incomplete` | 应用信息尚未补全，见 [迁移指南 3.1 节](./oauth-migration.md#31-补全应用信息) |
| 资源服务器返回 `invalid_token` | `iss` 不匹配，或 access token 已过期 |
