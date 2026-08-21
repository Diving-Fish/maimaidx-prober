---
sidebar_position: 3
toc_min_heading_level: 2
toc_max_heading_level: 4
---

# 水鱼账号 OAuth 快速开始

本文以可直接运行的示例代码，说明第三方应用如何接入水鱼账号，代用户读写查分器数据。若您正在从 `Developer-Token` 迁移，请先阅读 [迁移指南](./oauth-migration.md)。

全部接口的完整说明见 [OAuth 接口文档](./oauth-api-document.md)。

## 1. 登记应用

使用您的水鱼账号登录开发者控制台：

```plaintext
https://auth.diving-fish.com/console
```

点击「登记新应用」，填写应用名称（不超过 20 字）、应用描述（不超过 100 字）、主页地址（可留空，如填写须可公开访问），选择接入方式、部署形态与所需权限。

提交后，只读权限的申请将被自动审核，结果立即在控制台显示；包含写入权限的申请将转为人工审核，在审核通过之前，写入权限不会生效。

**部署形态**决定了您的应用是机密客户端还是公开客户端，判断标准只有一条：`client_secret` 能不能只留在您手上。

| **部署形态（控制台上的选项）** | **适用于** | **客户端类型** |
|-----|-----|-----|
| 「由你自己部署运行」 | 您自己运行的 bot、网站、后端服务 | 机密客户端，使用 `client_secret` |
| 「分发给用户各自部署」 | 插件、桌面程序、开源后由用户自行搭建的 bot | 公开客户端，**没有** `client_secret` |

跟着安装包分发出去的 `client_secret` 不再是秘密，因此后一类应用不签发该凭据，改由 PKCE 与 refresh token 担保安全。

若您选择的是前者，请在登记完成后于控制台生成 `client_secret` ——**登记应用与生成凭据是两个独立的动作**，只做前者的话应用没有任何可用凭据，所有请求都会得到 401 。

:::danger
`client_secret` 只在生成的那一刻显示一次，服务端保存的是它的哈希值。请立即将其写入您的服务端配置，切勿写入客户端、前端代码或公开仓库。
:::

:::warning
认证方式按登记值严格比对：机密客户端少传 `client_secret` ，或公开客户端多传 `client_secret` ，都会得到 401 `invalid_client` 。
:::

## 2. 选择接入方式

| **您的应用形态** | **接入方式** | **参见** |
|-----|-----|-----|
| 网站、桌面客户端、移动应用，有可登记的回调地址，需要「用水鱼账号登录」 | 授权码 + PKCE | [第 3 节](#3-方式一授权码--pkce) |
| 您自己运行的 QQ 机器人、命令行工具、脚本，没有浏览器也开不了公网回调地址 | 设备码绑定 + 换票 | [第 4 节](#4-方式二设备码绑定--换票) |
| 分发给用户各自部署、且开不了回调地址的插件与自建 bot | 设备码绑定 + refresh token | [第 5 节](#5-方式三设备码绑定--refresh-token) |

三种方式并不互斥，但一个应用通常只需要其中一种。

**接入方式与部署形态是两个独立的问题。** 方式一对机密客户端与公开客户端同样适用，分发出去的桌面程序、移动应用只要能登记回调地址（填 `http://127.0.0.1/callback` 一类的本机回环地址即可，端口不参与比对），就走方式一，仅仅是不携带 `client_secret` 而已。方式二与方式三的差别才是部署形态本身：绑定阶段完全相同，区别只在取得令牌的方式——机密客户端凭 `client_secret` 随时换票，不保存任何用户凭据；公开客户端则为每位用户各自保存一把 refresh token 。

## 3. 方式一：授权码 + PKCE

适用于有回调地址的应用。用户在授权页上完成登录与同意，浏览器携带授权码跳回您的回调地址，您再用授权码换取令牌。

:::info
PKCE 为**强制要求**，机密客户端也不例外，且 `code_challenge_method` 只接受 `S256` 。缺少 `code_challenge` 的授权请求将直接返回 400 。
:::

### 3.1 生成 PKCE 参数并把用户送到授权页

```python
import base64
import hashlib
import secrets
from urllib.parse import urlencode

AUTH = "https://auth.diving-fish.com"
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
REDIRECT_URI = "https://example.com/callback"    # 必须与登记值完全一致

def build_authorize_url(session: dict) -> str:
    """生成授权页地址。session 用于保存本次请求的临时状态。"""
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")

    session["code_verifier"] = verifier          # 自行保存，切勿发出
    session["state"] = secrets.token_urlsafe(16)
    session["nonce"] = secrets.token_urlsafe(16)

    return AUTH + "/oauth/authorize?" + urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile prober.records.read",
        "state": session["state"],
        "nonce": session["nonce"],
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
```

用户同意后，浏览器会跳转回：

```plaintext
https://example.com/callback?code=your_authorization_code&state=your_state
```

### 3.2 校验 state 并换取令牌

```python
import requests

def handle_callback(session: dict, code: str, state: str) -> dict:
    # 必须先核对 state，对不上一律丢弃。这是防止 CSRF 的唯一手段
    if not state or state != session.get("state"):
        raise RuntimeError("state 不匹配，已丢弃本次回调")

    response = requests.post(f"{AUTH}/oauth/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,            # 与上一步完全一致
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,          # 公开客户端删掉此行
        "code_verifier": session["code_verifier"],
    }, timeout=10)
    response.raise_for_status()
    return response.json()
```

响应如下：

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

:::warning
授权码为一次性，有效期 60 秒。重复使用不仅会失败，还会连带吊销由该授权码换出的令牌，因此请勿对换取令牌的请求做「重发同一个 code」式的重试。
:::

### 3.3 刷新令牌

access token 有效期为 15 分钟，过期后使用 refresh token 换取新的令牌：

```python
def refresh(refresh_token: str) -> dict:
    response = requests.post(f"{AUTH}/oauth/token", data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,          # 公开客户端删掉此行
    }, timeout=10)
    response.raise_for_status()
    return response.json()
```

:::danger
**每次刷新都会签发一把新的 refresh token ，旧的立即作废。** 拿到响应后必须先持久化新的 refresh token ，再继续后续逻辑。

旧的 refresh token 再次出现时，服务器会将其视为凭据泄露，**吊销整条令牌链，包括您刚刚拿到的那把新令牌**，用户需要重新授权。因此请注意：不要并发刷新，不要在多台机器上共享同一把 refresh token ，不要等到进程退出时才落盘。
:::

## 4. 方式二：设备码绑定 + 换票

适用于**由您自己部署运行**的 bot 与命令行工具，即机密客户端。分发给用户各自部署的应用请看 [第 5 节](#5-方式三设备码绑定--refresh-token)。

这条路径分为两个阶段：

1. **绑定**：一次性动作。您的应用向授权服务器申请一个用户码与一条链接，用户在浏览器中打开链接、登录、点击同意，绑定即告完成。
2. **换票**：日常动作。您的应用凭 `client_secret` 与该用户的标识，换取一张代表该用户的短期令牌，用它请求查分器。

绑定关系保存在授权服务器一侧，因此您的应用不需要为每个用户保存任何令牌，持久状态只有配置文件里的 `client_secret` 一行。

### 4.1 用户标识：选择一种写法

在开始之前，需要先确定「您的应用如何指称一个用户」。

#### 路径 A：使用 QQ 号（过渡期写法）

**仅对从 `Developer-Token` 迁移过来的应用开放，且将于 2026 年 10 月 1 日 00:00（UTC+8）停止工作。** 若您原本就是按 QQ 号定位用户的，这条路径不需要改动任何用户标识存储：

```plaintext
subject=qq:123456
```

取值同时会匹配用户绑定的 QQ 号与频道 ID ，与 `Developer-Token` 时代 `qq` 参数的行为一致。

采用这条路径时，您的存量用户已经在迁移中补齐了授权记录，无需重新绑定，可以直接跳到 [4.4 节](#44-换票)。仅当换票返回 `consent_required` 时，才需要引导用户走一次 4.2 与 4.3 的绑定流程。

请在上述日期之前改用路径 B 。您手上已经有这个 QQ 号，按下方公式算出摘要即可，同样不需要用户重新绑定。

#### 路径 B：使用 ref 摘要（推荐）

**所有应用均可使用。** 您把自己那一侧的用户标识（QQ 号、频道 ID 、您自己的用户 ID 均可）与 `client_id` 拼接后取 sha256 ：

```python
import hashlib

def subject_ref(external_id: str) -> str:
    """external_id 是您的应用自己使用的用户标识。"""
    return hashlib.sha256(f"{CLIENT_ID}:{external_id}".encode()).hexdigest()
```

换票时写作：

```plaintext
subject=ref:9a1b2c3d...   # 上面算出的 64 位十六进制摘要
```

由于摘要中混入了 `client_id` ，同一个用户在不同应用中的标识互不相同。这是长期方案，建议新接入的应用直接采用，迁移中的应用在 2026 年 10 月 1 日之前切换过来。

### 4.2 发起绑定

```python
import hashlib
import requests

AUTH = "https://auth.diving-fish.com"
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

def start_binding(external_id: str, label: str) -> dict:
    """向用户发起一次绑定。label 是给用户看的遮挡后展示串。"""
    response = requests.post(f"{AUTH}/oauth/device_authorization", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "prober.records.read",
        "subject_ref": subject_ref(external_id),
        "binding_label": label,
    }, timeout=10)
    response.raise_for_status()
    return response.json()
```

响应如下：

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

把 `verification_uri_complete` 发给用户即可。用户打开链接、登录水鱼账号、确认应用名称与绑定身份无误后点击同意，绑定就完成了——**您的应用不需要做任何其他事情**，下一次换票即可成功。

:::warning
`binding_label` 不是装饰性字段，请务必填写。它是遮挡后的身份展示串，例如 `QQ 11****14` ，会显示在用户的同意页上。

设备码流程没有回调地址，用户无从通过「跳转到哪里」判断自己在授权给谁。若攻击者向您的 bot 索要一条绑定链接（其中的标识是攻击者自己的）并转发给受害者，受害者点击同意后，攻击者即可通过您的 bot 读写受害者的成绩。同意页上那一行「绑定身份」，是受害者唯一可能察觉异常的地方。
:::

`user_code` 的有效期为 10 分钟。过期后重新发起一次即可。

:::tip
即使您当前采用的是路径 A （ `qq:` ），发起绑定时也建议一并提交 `subject_ref` 。绑定完成后两种写法都可以换到票，而您在 2026 年 10 月 1 日之前切换到 `ref:` 时，不必再让用户重新绑定一次。

此外还有一种写法不需要事先绑定：`subject=username:<查分器用户名>` ，所有应用均可长期使用，适用于「用户名由第三方在查询时临时给出」的场景（例如群聊中查询他人的成绩）。详见 [接口文档 6.4 节](./oauth-api-document.md#64-username查分器用户名)。
:::

### 4.3 确认绑定结果（可选）

如前所述，绑定完成后直接换票即可，轮询并非必需。若您希望明确知道用户点击的是同意还是拒绝，可以轮询令牌端点：

```python
import time

def poll(device_code: str, interval: int = 5, timeout: int = 600) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(interval)
        response = requests.post(f"{AUTH}/oauth/token", data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }, timeout=10)
        if response.status_code == 200:
            return response.json()

        error = response.json().get("error")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval += 5
            continue
        raise RuntimeError(f"绑定失败: {error}")     # access_denied / expired_token
    raise TimeoutError("用户未在有效期内完成绑定")
```

轮询成功时的响应中会额外包含一个 `sub` 字段，即该用户的水鱼用户 ID 。若您希望自行保存映射关系，可以记下它，此后用 `subject=sub:12345` 换票。

:::tip
请遵守响应中给出的 `interval` （5 秒）。轮询过快会收到 `slow_down` ，此时应当增大间隔而非立即重试。
:::

### 4.4 换票

日常调用时，用应用凭据与用户标识换取一张代表该用户的令牌：

```python
class NotBound(Exception):
    """该用户尚未绑定，或其账号不存在。两者不作区分。"""

def fetch_token(subject: str, scope: str = "prober.records.read") -> dict:
    response = requests.post(f"{AUTH}/oauth/token", data={
        "grant_type": "urn:diving-fish:params:oauth:grant-type:on-behalf-of",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "subject": subject,
        "scope": scope,
    }, timeout=10)
    if response.status_code == 400 and response.json().get("error") == "consent_required":
        raise NotBound()
    response.raise_for_status()
    return response.json()
```

响应如下，注意其中**没有 refresh token** ——这条路径不需要，令牌过期后重新换一张即可：

```json
{
    "token_type": "Bearer",
    "access_token": "eyJ0eXAiOiJhdCtqd3QiLCJhbGciOiJSUzI1NiIsImtpZCI6...",
    "expires_in": 300,
    "scope": "prober.records.read"
}
```

:::warning
令牌有效期为 5 分钟，**请在有效期内复用，不要每次业务请求都换一次票**。换票接口设有频率限制：同一个应用对同一个用户每小时最多 60 次，整个应用每小时最多 3000 次，超出后返回 `slow_down` 与状态码 429 。
:::

一个足够用的缓存实现：

```python
import time

_cache: dict = {}

def access_token(subject: str) -> str:
    token, expires_at = _cache.get(subject, (None, 0))
    if token and time.time() < expires_at - 30:      # 留 30 秒余量
        return token
    data = fetch_token(subject)
    token = data["access_token"]
    _cache[subject] = (token, time.time() + data["expires_in"])
    return token
```

### 4.5 完整示例

以下是一个按 QQ 号服务用户的 bot 的完整骨架，涵盖了「未绑定则引导绑定，已绑定则直接查询」：

```python
import hashlib
import time
import requests

AUTH = "https://auth.diving-fish.com"
PROBER = "https://www.diving-fish.com/api/maimaidxprober"
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

_cache: dict = {}


class NotBound(Exception):
    pass


def subject_ref(external_id: str) -> str:
    return hashlib.sha256(f"{CLIENT_ID}:{external_id}".encode()).hexdigest()


def mask_qq(qq: str) -> str:
    return f"QQ {qq[:2]}****{qq[-2:]}" if len(qq) > 4 else "QQ ****"


def access_token(qq: str) -> str:
    token, expires_at = _cache.get(qq, (None, 0))
    if token and time.time() < expires_at - 30:
        return token

    response = requests.post(f"{AUTH}/oauth/token", data={
        "grant_type": "urn:diving-fish:params:oauth:grant-type:on-behalf-of",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "subject": "ref:" + subject_ref(qq),
        "scope": "prober.records.read",
    }, timeout=10)
    if response.status_code == 400 and response.json().get("error") == "consent_required":
        raise NotBound()
    response.raise_for_status()

    data = response.json()
    _cache[qq] = (data["access_token"], time.time() + data["expires_in"])
    return data["access_token"]


def binding_link(qq: str) -> str:
    response = requests.post(f"{AUTH}/oauth/device_authorization", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "prober.records.read",
        "subject_ref": subject_ref(qq),
        "binding_label": mask_qq(qq),
    }, timeout=10)
    response.raise_for_status()
    return response.json()["verification_uri_complete"]


def records_of(qq: str) -> dict:
    response = requests.get(f"{PROBER}/player/records", headers={
        "Authorization": "Bearer " + access_token(qq),
    }, timeout=15)
    if response.status_code == 401:
        _cache.pop(qq, None)                          # 令牌已失效，下次重新换取
    response.raise_for_status()
    return response.json()


def on_command(qq: str) -> str:
    """收到用户指令时的处理。"""
    try:
        data = records_of(qq)
    except NotBound:
        return f"请先绑定查分器账号：{binding_link(qq)}\n链接 10 分钟内有效。"
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            return "今日查询次数已达上限，请明天再试。"
        raise
    return f"{data['nickname']} 的 Rating 为 {data['rating']}"
```

## 5. 方式三：设备码绑定 + refresh token

适用于分发给用户各自部署的插件、桌面程序与自建 bot ，即公开客户端。**本节所有请求都不携带 `client_secret`** ——这类应用没有该凭据。

绑定阶段与方式二相同，区别在于：您的应用无法换票，用户令牌只在轮询的响应中出现一次，因此**必须轮询**，并且要为每位用户各自保存取回的 refresh token 。

### 5.1 发起绑定

```python
import requests

AUTH = "https://auth.diving-fish.com"
CLIENT_ID = "your_client_id"                     # 公开客户端只有这一项


def start_binding() -> dict:
    response = requests.post(f"{AUTH}/oauth/device_authorization", data={
        "client_id": CLIENT_ID,
        "scope": "prober.records.read",
    }, timeout=10)
    response.raise_for_status()
    return response.json()
```

响应结构与 [4.2 节](#42-发起绑定)相同。请把其中的 `user_code` 与 `verification_uri` **显示在您自己的程序界面里**，由使用者本人打开链接完成授权。

:::danger
**不要把绑定链接做成「发给需要绑定的人」的形式。**

该端点不校验凭据，任何人都能用您的 `client_id` 生成一条绑定链接。受害者点击同意之后，令牌落到的是发起那次请求的人手上，也就是攻击者——公开客户端在这条路上交出的是长期访问权限，比机密客户端的冒名绑定更直接。

同意页会对公开客户端额外做出提示，但那是最后一道防线。让用户码只出现在用户自己启动的程序中，才是第一道。
:::

### 5.2 轮询取得令牌

```python
import time


def poll(device_code: str, interval: int = 5, timeout: int = 600) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(interval)
        response = requests.post(f"{AUTH}/oauth/token", data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id": CLIENT_ID,
        }, timeout=10)
        if response.status_code == 200:
            return response.json()

        error = response.json().get("error")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval += 5
            continue
        raise RuntimeError(f"绑定失败: {error}")     # access_denied / expired_token
    raise TimeoutError("用户未在有效期内完成绑定")
```

响应如下，其中 `sub` 是该用户的水鱼用户 ID ，`refresh_token` 就是这条路径的全部成果：

```json
{
    "token_type": "Bearer",
    "access_token": "eyJ0eXAiOiJhdCtqd3QiLCJhbGciOiJSUzI1NiIsImtpZCI6...",
    "expires_in": 900,
    "refresh_token": "your_refresh_token",
    "scope": "prober.records.read",
    "sub": "12345"
}
```

**拿到后请立即持久化 `refresh_token`。** 同一个设备码不能换第二次，这一步失手就只能让用户重新绑定一遍。

### 5.3 续期

access token 有效期 15 分钟，过期后用 refresh token 换新的：

```python
def refresh(refresh_token: str) -> dict:
    response = requests.post(f"{AUTH}/oauth/token", data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
    }, timeout=10)
    response.raise_for_status()
    return response.json()
```

:::danger
**每次刷新都会签发一把新的 refresh token ，旧的立即作废。** 拿到响应后必须先持久化新的 refresh token ，再继续后续逻辑。

旧的 refresh token 再次出现时，服务器会将其视为凭据泄露，**吊销整条令牌链，包括您刚刚拿到的那把新令牌**，该用户需要重新绑定。因此请注意：不要并发刷新，不要在多处共享同一把 refresh token ，不要等到进程退出时才落盘。
:::

用户在水鱼账号中撤销授权后，refresh token 立即失效，刷新将返回 `invalid_grant` 。此时应引导用户重新走一次 5.1 的绑定流程，而不是反复重试。

### 5.4 完整示例

```python
import json
import os
import time
import requests

AUTH = "https://auth.diving-fish.com"
PROBER = "https://www.diving-fish.com/api/maimaidxprober"
CLIENT_ID = "your_client_id"
STORE = os.path.expanduser("~/.config/your-plugin/token.json")


def load() -> dict:
    try:
        with open(STORE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save(data: dict):
    """先写临时文件再改名：崩在半途也不会留下一个读不出来的令牌。"""
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    with open(STORE + ".tmp", "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(STORE + ".tmp", STORE)


def bind() -> dict:
    """首次绑定。用户码请显示在自己的界面上，不要让用户转发。"""
    device = start_binding()
    print(f"请打开 {device['verification_uri']} 并输入绑定码 "
          f"{device['user_code']} ，10 分钟内有效。")
    token = poll(device["device_code"], device["interval"])
    data = {"refresh_token": token["refresh_token"],
            "access_token": token["access_token"],
            "expires_at": time.time() + token["expires_in"]}
    save(data)                                   # 先落盘，再返回
    return data


def access_token() -> str:
    data = load()
    if not data:
        data = bind()
    if time.time() < data["expires_at"] - 30:     # 留 30 秒余量
        return data["access_token"]

    token = refresh(data["refresh_token"])
    data = {"refresh_token": token["refresh_token"],
            "access_token": token["access_token"],
            "expires_at": time.time() + token["expires_in"]}
    save(data)                                   # 用之前先落盘
    return data["access_token"]


def records() -> dict:
    response = requests.get(f"{PROBER}/player/records", headers={
        "Authorization": "Bearer " + access_token(),
    }, timeout=15)
    response.raise_for_status()
    return response.json()
```

## 6. 使用 access token 访问查分器

无论通过哪种方式取得令牌，访问查分器的方式都相同：

```plaintext
GET https://www.diving-fish.com/api/maimaidxprober/player/records
Authorization: Bearer eyJ0eXAiOiJhdCtqd3QiLCJhbGciOiJSUzI1NiIsImtpZCI6...
```

**请求中不需要、也不接受 `qq` 与 `username` 参数**，查询对象由令牌决定。

支持 Bearer 令牌的端点及其所需 scope 见 [OAuth 接口文档第 9 节](./oauth-api-document.md#9-查分器端点)。

调用配额为每位用户每日 200 次，每个应用合计每日 `1000 + 授权用户数 × 20` 次，超出后返回 429 。详见 [OAuth 接口文档第 10 节](./oauth-api-document.md#10-配额与限流)。

## 7. 接入自检清单

通用：

- [ ] access token 在有效期内被复用，而非每次请求都重新换取
- [ ] 收到 429 时给用户明确的提示，并在下一个自然日（UTC）之前不再重试
- [ ] 只申请了实际用到的 scope

机密客户端（由您自己部署运行）：

- [ ] `client_secret` 已在控制台生成，且只存在于服务端配置中，未进入客户端、前端代码或版本库
- [ ] 换票收到 `consent_required` 时，向用户给出绑定链接，而非提示「查询失败」
- [ ] 发起设备码绑定时填写了 `binding_label`

公开客户端（分发给用户各自部署）：

- [ ] 所有请求都不携带 `client_secret`
- [ ] 绑定码显示在自己的程序界面中，未做成「把链接发给他人」的形式
- [ ] 每位用户的 refresh token 各自保存，未在多处共享

使用 refresh token 的应用（授权码方式与公开客户端）：

- [ ] 授权码方式下，回调时先校验 `state` 再换取令牌
- [ ] 新的 refresh token 在使用前已完成持久化，且不存在并发刷新
- [ ] 刷新返回 `invalid_grant` 时引导用户重新授权，而非反复重试
