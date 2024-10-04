# diving-fish 查分器 API 文档

---

## 目录

- [diving-fish 查分器 API 文档](#diving-fish-查分器-api-文档)
  - [目录](#目录)
  - [1. API端点](#1-api端点)
  - [2. 身份验证](#2-身份验证)
    - [2.1 无需验证要求](#21-无需验证要求)
    - [2.2 Import-Token验证要求](#22-import-token验证要求)
    - [2.3 Developer-Token验证要求](#23-developer-token验证要求)
    - [2.4 登录验证](#24-登录验证)
  - [3. 端点交互](#3-端点交互)
    - [3.1 maimaidxprober](#31-maimaidxprober)
      - [3.1.1 获取 / 更新用户是否同意用户协议](#311-获取--更新用户是否同意用户协议)
      - [3.1.2 获取 / 更新用户资料](#312-获取--更新用户资料)
      - [3.1.3 生成一个新的 Import-Token ，并覆盖旧 Token](#313-生成一个新的-import-token-并覆盖旧-token)
      - [3.1.4 获取 maimai 的歌曲数据](#314-获取-maimai-的歌曲数据)
      - [3.1.5 获取用户的完整成绩信息](#315-获取用户的完整成绩信息)
      - [3.1.6 获取用户的单曲成绩信息](#316-获取用户的单曲成绩信息)
      - [3.1.7 获取用户的简略成绩信息](#317-获取用户的简略成绩信息)
      - [3.1.8 按版本获取用户的成绩信息](#318-按版本获取用户的成绩信息)
      - [3.1.9 按 ID 获取歌曲的封面图片](#319-按-id-获取歌曲的封面图片)
      - [3.1.10 获取公开的 用户-rating 完整数据](#3110-获取公开的-用户-rating-完整数据)
      - [3.1.11 更新用户的成绩信息](#3111-更新用户的成绩信息)
      - [3.1.12 通过 html 格式的数据更新用户的成绩信息](#3112-通过-html-格式的数据更新用户的成绩信息)
      - [3.1.13 更新用户的单曲成绩](#3113-更新用户的单曲成绩)
      - [3.1.14 清除用户的所有 maimai 成绩信息](#3114-清除用户的所有-maimai-成绩信息)
      - [3.1.15 返回谱面的拟合难度等数据](#3115-返回谱面的拟合难度等数据)
    - [3.2 chunithmprober](#32-chunithmprober)
    - [3.3 public](#33-public)
      - [3.3.1 使用 diving-fish 账号登录](#331-使用-diving-fish-账号登录)
      - [3.3.2 获取查分器主页的views次数](#332-获取查分器主页的views次数)
      - [3.3.3 验证服务器状态](#333-验证服务器状态)
      - [3.3.4 获取 / 提交查分器主页的今日留言](#334-获取--提交查分器主页的今日留言)
      - [3.3.5 获取查分器主页的广告](#335-获取查分器主页的广告)

---

## 1. API端点

所有向 diving-fish 数据库发起的请求应当被发送到以下 URL ：

```plaintext
https://www.diving-fish.com/api/{游戏数据类别}/{端点路径}
```

- `{游戏数据类别}` : 根据您要访问的游戏数据决定，可以是 `maimaidxprober` 或 `chunithmprober`。
- `{端点路径}` : 具体的表示方法的端点。

您需要根据访问的具体端点构建完整的访问地址，例如， `maimaidxprober` 中的 `/player/profile` 可以通过以下 URL 访问

```plaintext
https://www.diving-fish.com/api/maimaidxprober/player/profile
```

请注意， API 中还包含一类 public 类的端点，用于获取 maimai 和 chunithm 通用的数据。**要访问此类端点，您也需要将 `{游戏数据类别}` 设置为 `maimaidxprober`。**

以下是详细的可访问端点，您可以通过点击具体的端点路径快速定位到相关功能：

| **游戏数据类别** | **端点路径** | **权限要求** | **功能** |
|-----|-----|-----|-----|
| `maimaidxprober` | [`/player/agreement`](#311-获取--更新用户是否同意用户协议) | 登录验证 | 获取 / 更新用户是否同意用户协议 |
| `maimaidxprober` | [`/player/profile`](#312-获取--更新用户资料) | 登录验证 | 获取 / 更新用户资料 |
| `maimaidxprober` | [`/player/import_token`](#313-生成一个新的-import-token-并覆盖旧-token) | 登录验证 | 生成一个新的 `Import-Token` ，并覆盖旧 Token |
| `maimaidxprober` | [`/music_data`](#314-获取-maimai-的歌曲数据) | 无需验证 | 获取 maimai 的歌曲数据 |
| `maimaidxprober` | [`/player/records`](#315-获取用户的完整成绩信息) | 登录验证 / Import-Token | 获取用户的完整成绩信息 |
| `maimaidxprober` | [`/player/test_data`](#315-获取用户的完整成绩信息) | 无需验证 | 获取用于测试的完整成绩信息 |
| `maimaidxprober` | [`/dev/player/records`](#315-获取用户的完整成绩信息) | Developer-Token | 获取用户的完整成绩信息 |
| `maimaidxprober` | [`/dev/player/record`](#316-获取用户的单曲成绩信息) | Developer-Token | 获取用户的单曲成绩信息 |
| `maimaidxprober` | [`/query/player`](#317-获取用户的简略成绩信息) | 无需验证 | 获取用户的简略成绩信息 |
| `maimaidxprober` | [`/query_plate`](#318-按版本获取用户的成绩信息) | 无需验证 | 按版本获取用户的成绩信息 |
| `maimaidxprober` | [`*/covers`](#319-按-id-获取歌曲的封面图片) | 无需验证 | 按 ID 获取歌曲的封面图片 |
| `maimaidxprober` | [`/rating_ranking`](#3110-获取公开的-用户-rating-完整数据) | 无需验证 | 获取公开的 用户-rating 完整数据 |
| `maimaidxprober` | [`/player/update_records`](#3111-更新用户的成绩信息) | 登录验证 | 更新用户的成绩信息 |
| `maimaidxprober` | [`/player/update_records_html`](#3112-通过-html-格式的数据更新用户的成绩信息) | 登录验证 |  通过 html 格式的数据更新用户的成绩信息 |
| `maimaidxprober` | [`/player/update_record`](#3113-更新用户的单曲成绩) | 登录验证 | 更新用户的单曲成绩 |
| `maimaidxprober` | [`/player/delete_records`](#3114-清除用户的所有-maimai-成绩信息) | 登录验证 | 清除用户的所有 maimai 成绩信息 |
| `maimaidxprober` | [`/chart_stats`](#3115-返回谱面的拟合难度等数据) | 无需验证 | 返回谱面的拟合难度等数据 |
| `chunithmprober` | `（待贡献）` | ----- | ----- |
| `public` | [`/login`](#24-登录验证) | 登录验证 | 使用 diving-fish 账号登录 |
| `public` | [`/count_view`](#332-获取查分器主页的views次数) | 无需验证 | 获取查分器主页的views次数 |
| `public` | [`/alive_check`](#333-验证服务器状态) | 无需验证 | 验证服务器状态 |
| `public` | [`/message`](#334-获取--提交查分器主页的今日留言) | 无需验证 / 登录验证 | 获取 / 提交查分器主页的今日留言 |
| `public` | [`/advertisements`](#335-获取查分器主页的广告) | 无需验证 | 获取查分器主页的广告 |

```plaintext
注：对于端点前包含 * 的方法，您需要通过其他基础 URL 进行访问
```

public 类的端点中还包含一些其他功能如注册账户、重置账户、提交反馈等。出于便捷性和安全性考虑，此类功能以及大部分 public 类的功能均建议前往 [diving-fish 查分器主页](https://www.diving-fish.com/maimaidx/prober/) 进行操作。

查看详细的源代码以了解访问过程中进行交互的详细数据结构或了解其他功能，可访问项目的 github 链接: <https://github.com/Diving-Fish/maimaidx-prober>

---

## 2. 身份验证

不同端点的访问对权限有不同级别的要求，您需要根据所访问的端点在 HTTP 请求中添加验证信息。

部分对用户数据的获取（包括 [获取用户的简略成绩信息](#317-获取用户的简略成绩信息) 与 [按版本获取用户的成绩信息](#318-按版本获取用户的成绩信息) ）需要基于用户对用户协议和允许第三方查询的同意。设计服务时，您可能需要考虑此种情况以扩大容错边界。

### 2.1 无需验证要求

获取歌曲详细信息、获取歌曲封面、查询用户基本信息（包括b50、rating等）等功能无需验证信息即可访问，对于和用户相关的信息访问成功与否通常取决于用户是否允许其他人获取成绩等。

### 2.2 Import-Token验证要求

该验证仅用于用户完整成绩信息的获取。对于此类请求，用户需要提供自己的 `Import-Token` 完成请求，用户可以在 <https://www.diving-fish.com/maimaidx/prober/> 登录后，在“编辑个人资料”中生成 `Import-Token` 并提供给您。

您可以在 `headers` 中添加 `Import-Token` 信息进行验证，例如：

```python
headers = {
    "Import-Token": "your_import_token_here"
    }
```

该验证方式会修饰其作用的端点，当 `Import-Token` 验证失败时，会返回以下错误信息：

状态码： `400`
响应体：

```json
{
    "status": "error",
    "message": "导入token有误"
}
```

此类验证方式提供了额外的用户成绩获取的方法，当您缺少 `Developer-Token` 或有其他需要时，可以要求用户生成 `Import-Token` 并提供给您。

### 2.3 Developer-Token验证要求

部分端点访问要求 `Developer-Token` ，需要在查分器官网 <https://www.diving-fish.com/maimaidx/prober/> 申请获得。您可以在登录个人账号后在 `编辑个人资料` - `需要查分器中的玩家数据用于其他应用程序开发？请点击这里~` 中找到相关界面。

通过该验证方式，您可以获取如下信息：

- 指定用户的完整成绩信息，包括rating、昵称、段位和牌子信息等
- 指定用户的单曲成绩信息，在不需要完整成绩信息的情况下可以节省大量资源

2024年8月起，`Developer-Token` 会基于服务规模对每小时的请求数进行限制，您可以上传相关服务规模的证明以对应您申请的 Token 。

获取到 `Developer-Token` 后，您可以将其添加到 `headers` 中进行验证，例如：

```python
headers = {
    "Developer-Token": "your_developer_token_here",
    }
```

该验证方式会修饰其作用的端点，当 `Developer-Token` 验证失败时，会根据不同的情况返回错误信息：

状态码： `400`
响应体：

```json
{
    "status": "error",
    "message": "<错误信息>"
}
```

`Developer-Token` 为空、有误、被禁用均在此范畴内。

在HTTP请求中根据不同方式在 `headers` 中添加对应验证信息，完成验证即可访问具体端点的返回信息。

### 2.4 登录验证

使用 diving-fish 用户名和密码进行登录会提供给操作者极高程度的权限，包括获取和修改几乎所有个人信息和成绩。如果您的项目功能围绕查分开展， `Developer-Token` 已经为您提供了实现现行所有主流查分工具通用功能的途径。

如果您只是需要开发一个查询用户b50和简略信息的工具，无需任何验证方式即可满足您的需求；如果您需要获取用户完整的乐曲成绩，请向水鱼申请 `Developer-Token` ；如果您确实有相关需求，且希望将该验证设计到 bot 中，请务必提示用户关于提供用户名和密码的安全性问题，并且着重**提醒用户不要在公共群聊和频道里提供用户名和密码**；如果一定要存储密码，请务必**避免明文存储**。一切数据泄露所带来的风险与后果需要您自行承担。

请在确保您已经完整了解并理解以上信息的前提下继续进行阅读。

与其它方法直接向指定端点附带 `headers` 进行请求不同，登录验证依赖于 `jwt_token` ，您需要首先利用用户名和密码发送登录请求，得到 `jwt_token` ，随后在 `cookies` 中附带该 `jwt_token` 信息完成对指定端点的请求。具体过程如下。

首先，您需要用用户名和密码构造一个 JSON 格式的请求体：

```json
{"username": "your_username", "password": "your_password"}
```

随后，您需要附加该请求体，并向以下 URL 发送 POST 请求：

```plaintext
https://www.diving-fish.com/api/maimaidxprober/login
```

如果登录凭据错误，服务器会返回一个非200的状态码。

如果登录成功，服务器会返回一个 `200` 的状态码，以及一个包含 `jwt_token` 的 `cookies` 字典，您可以在有效期内使用该 `jwt_token` 进行需要登录验证的端点访问请求。

以下是 python 示例代码，利用 diving-fish 用户名和密码获取用户是否同意过隐私协议：

```python
import json
import requests
from requests.exceptions import RequestException

class ProberAPIClient:
    def __init__(self):
        self.username = ""
        self.password = ""
        self.network_timeout = 10
        self.client = requests.Session()
        self.jwt = ""

    def login(self):
        body = {"username": self.username, "password": self.password}

        try:
            response = self.client.post(
                "https://www.diving-fish.com/api/maimaidxprober/login",
                headers={"Content-Type": "application/json"},
                json=body, 
                timeout=self.network_timeout,
            )
        except RequestException as e:
            raise RuntimeError("登录失败: {}".format(e))

        if response.status_code != 200:
            raise ValueError("登录凭据错误")

        print("登录成功")
        self.jwt = response.cookies.get("jwt_token", "")    # 提取jwt_token
        self.client.cookies.set("jwt_token", self.jwt)  # 附加jwt_token

    def get_player_agreement(self, username, password):
        if not self.jwt:
            self.username = username
            self.password = password
            self.login()

        url = "https://www.diving-fish.com/api/maimaidxprober/player/agreement"

        try:
            response = self.client.get(url)
            response.raise_for_status()  # 检查响应状态码
        except RequestException as e:
            try:    # 检查返回信息中是否包含具体错误信息
                message = response.json().get("message", "Unknown error")
            except Exception:
                message = "Unknown error"
            raise RuntimeError(f"GET 请求失败: {e}, message: {message}")

        return response.json()  # json已转换为python字典


# 示例配置
cfg = {
    "UserName": "your_username",    # 在此处提供用户名和密码
    "Password": "your_password",
}

# 创建 ProberAPIClient 实例
client = ProberAPIClient()

# 使用 GET 请求获取用户是否同意过用户协议
response = client.get_player_agreement(cfg["UserName"], cfg["Password"])
print(response)

```

一旦上述代码成功执行并登录，程序会打印如下的返回信息：

```plaintext
登录成功
{'accept_agreement': True}
```

---

## 3. 端点交互

附加了对应的验证信息之后，您可以访问指定端点并获得返回的 `json` 信息，对于 POST 类的请求，您需要附加特定的请求体。

为方便在目录中直观定位，本部分内容以具体功能为标题索引。

### 3.1 maimaidxprober

所有对于 `maimaidxprober` 类的请求，都应该发送到以下 URL ：

```plaintext
https://www.diving-fish.com/api/maimaidxprober/{端点路径}
```

例如， `/player/profile` 可以通过以下 URL 访问 ：

```plaintext
https://www.diving-fish.com/api/maimaidxprober/player/profile
```

查看源代码以了解更多细节，可以访问 <https://github.com/Diving-Fish/maimaidx-prober/blob/main/database/routes/maimai.py>

#### 3.1.1 获取 / 更新用户是否同意用户协议

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/player/agreement` | [登录验证](#24-登录验证) | GET / POST |

附加了登录验证信息并成功登录之后，您可以获取 / 更新用户是否同意用户协议。是否同意用户协议将会决定用户是否能使用查分器的相关功能，对于新注册的账号而言，相关提示框会在官网第一次登录成功后显示。注意"是否同意用户协议"与"是否允许其他人查询用户成绩"不同。

获取用户是否同意用户协议可以向端点发送 GET 请求，一旦请求成功，服务器会返回一个 `200` 的状态码，并在响应体中包含一个 JSON 格式的数据。如:

```json
{"message": "success"}
```

此过程详细的示例代码可以参考 [登录验证](#24-登录验证) 部分下方的示例代码。

更新用户是否同意用户协议需要向端点发送 POST 请求，您需要附加包含 `"accept_agreement"` 参数的请求体，并将参数值设置为您想要更新的 bool 值（true 或 false）。请注意， JSON 中的 bool 值是小写的 true 和 false，引号采用双引号，而某些语言会通过一些方法自动处理这种转换。

一种可能的请求体如下：

```json
{"accept_agreement": "true"}
```

更新了用户是否同意用户协议为 false 之后，如果不通过此方法重新更新为 true ，用户可能需要重新访问查分器官网并再次手动同意用户协议以使用查分器的相关功能。目前此类方法应用场景有限。

#### 3.1.2 获取 / 更新用户资料

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/player/profile` | [登录验证](#24-登录验证) | GET / POST |

附加了登录验证信息并成功登录之后，您可以获取 / 更新用户资料。用户资料包含以下内容：

| **参数** | **数据类型** | **含义** |
|-----|-----|-----|
| `accept_agreement` | `bool` | 用户是否同意用户协议 |
| `additional_rating` | `int` | 用户段位信息，其中0-10对应初学者-十段，11-20对应真初段-真十段，21-22对应真皆传-里皆传 |
| `bind_qq` | `str` | 用户绑定的 QQ 号 |
| `import_token` | `str` | 用户的 Import-Token |
| `mask` | `bool` | 用户是否对非网页查询的成绩使用掩码 |
| `nickname` | `str` | 用户设置的昵称 |
| `plate` | `str` | 用户的牌子信息 |
| `privacy` | `bool` | 用户是否同意其他人查询自己成绩 |
| `qq_channel_uid` | `str` | 用户绑定的频道 ID |
| `user_general_data` |-----| 暂无实际作用 |
| `username` | `str` | 用户账号的用户名 **（不可修改）** |

完整的用户模型还包含一些其他不可获取的参数，具体可查看 <https://github.com/Diving-Fish/maimaidx-prober/blob/main/database/models/base.py>

获取用户资料可以向端点发送 GET 请求，一旦请求成功，服务器会返回一个 `200` 的状态码，并在响应体中包含一个 JSON 格式的数据，包含以上用户资料信息，如：

```json
{"accept_agreement": true, "additional_rating": 22, "bind_qq": "111122223333", "import_token": "your_import_token_here", "mask": false, "nickname": "your_nickname", "plate": "舞神", "privacy": false, "qq_channel_uid": "", "user_general_data": null, "username": "your_username"}
```

更新用户资料只需要将需要更新的参数附加在以 JSON 格式附加在请求体中向端点发送 POST 请求即可，如：

```json
{"additional_rating": 17, "mask": true}
```

更新用户资料成功后，服务器的响应体中会包含更新后的用户资料数据，与获取用户资料中得到的响应体格式一致。

当更新的参数中包含 `bind_qq` 和 `qq_channel_uid` 时，服务器会首先检查对应 QQ 号和频道 ID 是否已经被绑定，若已被绑定会返回错误信息如下：

```plaintext
状态码： `400`
{"message": "此 QQ 号（频道 ID）已经被用户名为{username}的用户绑定，请先解绑再进行操作~"}
```

当更新的参数中包含 `plate` 时，服务器会首先检查当前用户的成绩信息是否允许其持有该牌子，只有检查成功才能实际更新该参数。

**请注意 `import_token` 不能通过该方式直接更新**。要更新用户的 `import_token` ，请参考 [生成一个新的 Import-Token ，并覆盖旧 Token](#313-生成一个新的-import-token-并覆盖旧-token)。

#### 3.1.3 生成一个新的 Import-Token ，并覆盖旧 Token

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/player/import_token` | [登录验证](#24-登录验证) | PUT |

附加了登录验证信息并成功登录之后，您可以获取 / 更新用户资料。此时向端点发送 PUT 请求即可。

以下是 python 示例代码，发送请求生成一个新的 Import-Token ，并覆盖旧 Token：

```python
class ProberAPIClient:
    # 确保您已经完成了登录并将 jwt_token 附加到了 cookies 中
    ...
    def import_token(self):
        url = "https://www.diving-fish.com/api/maimaidxprober/player/import_token"

        try:
            response = self.client.put(url)
            response.raise_for_status()  # 检查响应状态码
        except RequestException as e:
            self.handle_request_exception(response, e)

        return response.json()
```

完成请求后，服务器会返回新的 Import-Token：

```json
{"token": "new_import_token"}
```

#### 3.1.4 获取 maimai 的歌曲数据

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/music_data` | 无需验证 | GET |

使用 GET 请求访问此端点，服务器会返回 diving-fish 数据库中完整的现行版本下所有 maimai 歌曲的完整信息，信息结构如下：

| **字段** | **类型** | **说明** |
|----------|----------|----------|
| `id` | `string` | 歌曲的唯一标识符，其与现行的歌曲 ID 号一致 |
| `title` | `string` | 歌曲的标题 |
| `type` | `string` | 歌曲的类型，为 "DX" 或 "SD" |
| `ds` | `array of float` | 歌曲的难度定数列表，由 Basic 至 Re:Master |
| `level` | `array of string` | 歌曲的难度等级列表，与 `ds` 的区别在于仅精确到整数或 "+" 等级 |
| `cids` | `array of int` | 歌曲特定难度谱面的唯一标识符 |
| `charts` | `array of object` | 歌曲的谱面信息列表，每个对象包含以下字段： |
| `charts[].notes` | `array of int` | 谱面的音符数量列表，依次为 Tap、Hold、Slide、（Touch，仅 DX 类型）、Break |
| `charts[].charter` | `string` | 谱师信息 |
| `basic_info` | `object` | 歌曲的基本信息，包含以下字段： |
| `basic_info.title` | `string` | 歌曲的标题 |
| `basic_info.artist` | `string` | 曲师信息 |
| `basic_info.genre` | `string` | 歌曲的流派 |
| `basic_info.bpm` | `int` | 歌曲的 BPM 信息 |
| `basic_info.release_date` | `string` | 歌曲的发行日期（目前均为空） |
| `basic_info.from` | `string` | 歌曲的稼动版本（以国服为准） |
| `basic_info.is_new` | `boolean` | 歌曲是否为当前版本的新歌 |

以下是其中一首歌曲信息的具体示例，其中 JSON 已经美观输出：

```json
{
    "id": "11466",
    "title": "群青シグナル",
    "type": "DX",
    "ds": [
        5.0,
        8.2,
        11.7,
        13.9
    ],
    "level": [
        "5",
        "8",
        "11+",
        "13+"
    ],
    "cids": [
        7853,
        7854,
        7855,
        7856
    ],
    "charts": [
        {
            "notes": [
                188,
                21,
                9,
                14,
                4
            ],
            "charter": "-"
        },
        {
            "notes": [
                369,
                18,
                10,
                26,
                20
            ],
            "charter": "-"
        },
        {
            "notes": [
                491,
                70,
                48,
                4,
                39
            ],
            "charter": "翠楼屋"
        },
        {
            "notes": [
                719,
                62,
                114,
                51,
                32
            ],
            "charter": "ものくろっく"
        }
    ],
    "basic_info": {
        "title": "群青シグナル",
        "artist": "テヅカ feat. 獅子神レオナ",
        "genre": "舞萌",
        "bpm": 206,
        "release_date": "",
        "from": "maimai でらっくす FESTiVAL",
        "is_new": false
    }
}
```

不难想象，完整的歌曲信息数据量是较大的。如果每次有相关需求都完整地向服务器 GET 完整的歌曲信息，不仅加大了服务器的负载，您的服务效率也会大打折扣。为了应对这种情况，返回体的返回头中实际包含了 `etag` 参数，用于指示数据的时效性。您在下一次请求中可以将此 `etag` 参数的值附加在请求头的 `If-None-Match` 参数中进行请求。如果 `etag` 与服务器上的数据相匹配，服务器会返回一个 `304` 的状态码，证明您先前请求的歌曲数据仍具有时效性，您可以将先前的歌曲数据缓存下来，在运行服务时使用缓存数据进行操作。

例如，您在 GET 请求中，从如下的返回体中获取了 `etag` 参数：

```json
{
  "Server": "nginx/1.23.2",
  "Date": "Sat, 32 Jul 2028 10:10:10 GMT",
  "Content-Type": "application/json; charset=utf-8",
  "Content-Length": "690231",
  "Connection": "keep-alive",
  "etag": "\"75fbe560a230722e2035946003963076\"",
  "cache-control": "private, max_age=86400",
  "access-control-allow-origin": "*",
  "access-control-allow-method": "*",
  "access-control-allow-headers": "x-requested-with,content-type"
}
```

**请重点关照 `etag` 的格式，其本身具备双引号包裹**，上文的示例试图使用转义符去表示这一特性，即使 Markdown 可能将转义符直接显示了出来，您也需要了解这一点，并在接下来将其附加到请求头时正确附带双引号包裹这一参数。

```plaintext
"75fbe560a230722e2035946003963076"  # 这是上文中完整的 etag 参数，额外于用于包裹字符串的双引号
75fbe560a230722e2035946003963076    # 缺少双引号
```

将 `etag` 的值以 JSON 格式附加在请求头中 `If-None-Match` 参数中，发送 GET 请求：

```json
"headers": {
    "If-None-Match": "\"75fbe560a230722e2035946003963076\""
}
```

一旦服务器返回 `304` 的状态码，证明您先前和 `etag` 对应的歌曲信息是最新的，您可以将 `etag` 缓存下来，并且在其正确对应时使用本地缓存的歌曲信息去处理服务。如果有需要，您也可以设计一个手动更新歌曲信息的功能。

#### 3.1.5 获取用户的完整成绩信息

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/player/records` | [登录验证](#24-登录验证) / [Import-Token](#22-import-token验证要求) | GET |
| `/dev/player/records` | [Developer-Token](#23-developer-token验证要求) | GET |

根据您采用的验证方式选择对应的端点。

需要注意的是，获取完整成绩信息数据量较大，**如果您只是需要用于绘制b50等功能的简略成绩信息**，请参考 [获取用户的简略成绩信息](#317-获取用户的简略成绩信息)

对于 `/player/records` 端点，您需要正确附加所需的验证信息。验证信息本身已经包含了对应用户的凭证，因此服务器会直接返回该用户的完整成绩信息。

对于 `/dev/player/records` 端点，您除了要附加您的 `Developer-Token` 验证信息外，还需要在 URL 查询参数中附加指定用户的 `username` 或 `qq` 参数，如：

```json
{"url": "https://www.diving-fish.com/api/maimaidxprober/dev/player/records?username=your_username"}
```

或：

```json
{"url": "https://www.diving-fish.com/api/maimaidxprober/dev/player/records?qq=your_qq"}
```

对于通过 `Developer-Token` 的访问，如果所请求的用户参数对应用户不存在，服务器会返回以下错误信息：

```plaintext
状态码： `400`
{"message": "no such user"}
```

成功获取用户完整成绩信息后，您会得到如下结构的 JSON 数据：

| **字段**                  | **类型**   | **说明**                                               |
|---------------------------|------------|--------------------------------------------------------|
| `additional_rating`       | `number`   | 用户的段位信息[（可参考此部分）](#312-获取--更新用户资料)     |
| `nickname`                | `string`   | 用户的昵称                                             |
| `plate`                   | `string`   | 用户的牌子信息                                         |
| `rating`                  | `number`   | 用户rating                                            |
| `records`                 | `array`    | 用户的成绩记录列表，以具体难度谱面为单位                    |
| `records[].achievements`  | `number`   | 成绩百分比                                             |
| `records[].ds`            | `number`   | 谱面定数                                               |
| `records[].dxScore`       | `number`   | DX 分数                                                |
| `records[].fc`            | `string`   | FC状态（fc、fcp、ap、app）                              |
| `records[].fs`            | `string`   | FS状态（sync、fs、fsp、fsd、fsdp）                        |
| `records[].level`         | `string`   | 谱面等级，与 `ds` 的区别在于仅精确到整数或 "+" 等级         |
| `records[].level_index`   | `number`   | 谱面难度在歌曲里的索引，由0到4对应 Basic 到 Re:Master      |
| `records[].level_label`   | `string`   | 等级标签（如 `Master`）                                 |
| `records[].ra`            | `number`   | 单曲rating                                             |
| `records[].rate`          | `string`   | 评级（如 `aa`、`sssp`）                                 |
| `records[].song_id`       | `number`   | 歌曲的唯一标识符                                       |
| `records[].title`         | `string`   | 歌曲标题                                               |
| `records[].type`          | `string`   | 歌曲类型（ `DX` 或 `SD`）                              |

一份参考返回数据的部分内容如下，其中 JSON 已经美观输出：

```plaintext
{
  "additional_rating": 13,
  "nickname": "sample",
  "plate": "輝将",
  "rating": 15932,
  "records": [
    {
      "achievements": 91.6265,
      "ds": 6,
      "dxScore": 520,
      "fc": "",
      "fs": "",
      "level": "6",
      "level_index": 1,
      "level_label": "Advanced",
      "ra": 83,
      "rate": "aa",
      "song_id": 11115,
      "title": "だから僕は音楽を辞めた",
      "type": "DX"
    },
    {
      "achievements": 101,
      "ds": 8.5,
      "dxScore": 744,
      "fc": "app",
      "fs": "fsd",
      "level": "8",
      "level_index": 1,
      "level_label": "Advanced",
      "ra": 191,
      "rate": "sssp",
      "song_id": 837,
      "title": "Altale",
      "type": "SD"
    },
    ...
  ],
  "username": "sample_username"
}
```

随后您可以根据自身需求决定对数据的保存和处理方法。如果您希望获得一份**完整的用户成绩参考数据**用于测试及开发，可以对 `/player/test_data` 端点发送 GET 请求，服务器即会返回一份完整的参考数据。此端点不设验证要求，这意味着您可以直接通过浏览器访问该 URL 查看此参考数据：<https://www.diving-fish.com/api/maimaidxprober/player/test_data>

#### 3.1.6 获取用户的单曲成绩信息

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/dev/player/record` | [Developer-Token](#23-developer-token验证要求) | POST |

附加了 `Developer-Token` 并成功验证之后，您可以获取用户的单曲成绩信息，需要向端点发送 POST 请求，且还需要在请求体中以 JSON 格式附带以下参数：

- `username` 或 `qq`
- `music_id` （可以为单个值或列表）

如果所请求的用户参数对应用户不存在，服务器会返回以下错误信息：

```plaintext
状态码： `400`
{"message": "no such user"}
```

请求成功后，服务器会返回指定用户指定单曲的成绩信息，其数据结构与[完整成绩信息](#315-获取用户的完整成绩信息)中单个歌曲的成绩信息结构一致，且包含该歌曲所有难度的谱面成绩。

#### 3.1.7 获取用户的简略成绩信息

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/query/player` | 无需验证 | POST |

作为**获取用户b50等数据的首选**，此方法不设验证要求，访问成功与否取决于用户是否同意用户协议或设置隐私。

要访问指定用户的简略成绩信息，需要向端点发送 POST 请求，并在请求体中以 JSON 格式附带用户的 `username` 或 `qq` 作为用户信息。**如果您需要获取的是b50而非b40，您需要在请求体中附带一个 `b50` 参数，其值可以任意设定，但是不能为空**。否则，服务器会默认返回用户的b40数据，如：

```json
{
    "username": "your_username",
    "b50": "1"
}
```

如果所请求的用户参数对应用户不存在，服务器会返回以下错误信息：

```plaintext
状态码： `400`
{"message": "no such user"}
```

如果用户已设置隐私或未同意用户协议，服务器会返回以下错误信息：

```plaintext
状态码： `403`
{"message": "已设置隐私或未同意用户协议"}
```

请求成功后，服务器会返回指定用户的简略成绩信息，其数据结构与[完整成绩信息](#315-获取用户的完整成绩信息)中的成绩信息结构一致（事实上额外包含一个目前尚未具备实际含义的 `user_general_data` 字段），包含其中如段位、牌子、昵称在内的所有字段的信息，但成绩信息只取新版本单曲 rating 最高的 15 张谱面与旧版本单曲 rating 最高的 35(25) 张谱面。

#### 3.1.8 按版本获取用户的成绩信息

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/query_plate` | 无需验证 | POST |

此方法不设验证要求，访问成功与否取决于用户是否同意用户协议或设置隐私。

要按版本获取用户的成绩信息，需要向端点发送 POST 请求，且还需要以 JSON 格式在请求体中附带以下参数：

- `username` 或 `qq`
- `version` （**必须为列表，即使只有一个元素**）

如果所请求的用户参数对应用户不存在，服务器会返回以下错误信息：

```plaintext
状态码： `400`
{"message": "no such user"}
```

如果用户已设置隐私或未同意用户协议，服务器会返回以下错误信息：

```plaintext
状态码： `403`
{"message": "已设置隐私或未同意用户协议"}
```

`version` 列表中的元素必须按照以下表格对应游戏版本（以国服为准）：

| 版本名称                       | 版本代号 |
|-------------------------------|----------|
| maimai PLUS                   | 真       |
| maimai GreeN                  | 超       |
| maimai GreeN PLUS             | 檄       |
| maimai ORANGE                 | 橙       |
| maimai ORANGE PLUS            | 暁       |
| maimai PiNK                   | 桃       |
| maimai PiNK PLUS              | 櫻       |
| maimai MURASAKi               | 紫       |
| maimai MURASAKi PLUS          | 菫       |
| maimai MiLK                   | 白       |
| MiLK PLUS                     | 雪       |
| maimai FiNALE                 | 輝       |
| ALL FiNALE                    | 舞       |
| maimai でらっくす              | 熊       |
| maimai でらっくす PLUS         | 華       |
| maimai でらっくす Splash       | 爽       |
| maimai でらっくす Splash PLUS  | 煌       |
| maimai でらっくす UNiVERSE     | 宙       |
| maimai でらっくす UNiVERSE PLUS| 星       |
| maimai でらっくす FESTiVAL     | 祭       |
| maimai でらっくす FESTiVAL PLUS| 祝       |

**您在附加 `version` 参数中的元素时，必须严格按照 `版本名称` 发送请求。**

请求成功后，服务器会返回指定用户对应版本的成绩信息，其中单个歌曲成绩信息的数据结构与 [完整成绩信息](#315-获取用户的完整成绩信息) 中的单个歌曲成绩信息（即 `records` 字段下的数据）结构一致，但仅包括了已游玩过的谱面成绩。如果您需要完整的用户版本成绩信息，您还需要通过比对 [完整歌曲数据](#314-获取-maimai-的歌曲数据) 进行整合。

#### 3.1.9 按 ID 获取歌曲的封面图片

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `*/covers` | 无需验证 | GET |

**该方法不属于通常 API 端点，因此与其余方法访问 URL 不同，要按 ID 获取歌曲的封面图片，需要访问以下 URL：**

```plaintext
https://www.diving-fish.com/covers/{cover_id}.png
```

其中 `{cover_id}` 为歌曲 ID，具体可参考 [maimai 歌曲数据](#314-获取-maimai-的歌曲数据) 中的歌曲 ID。**对于不足 5 位数的 ID，您需要在其前面补 `0` 以补足 5 位数**。如 ID 38 应当通过 <https://www.diving-fish.com/covers/00038.png> 访问。该方法不设验证要求，您可以直接通过浏览器打开 URL 进行访问。

在请求歌曲 ID 时，您可以对 ID 区间为 10001~11000 的歌曲做如下处理：

```python
def get_cover_len5_id(self, mid) -> str:
    mid = int(mid)
    if mid > 10000 and mid <= 11000:
        mid -= 10000
    return f"{mid:05d}"
```

即除去补足 5 位数的操作外，对于 ID 在此区间的歌曲，请求其 ID - 10000 的歌曲对应的歌曲封面。该操作的实际含义是：这个 ID 区间通常是预留给同时具有 DX 与 SD 谱面的歌曲，其中 ID 区间为 10001 至 11000 的歌曲对应其 DX 谱面，而其 ID - 10000 的歌曲对应其 SD 谱面，因为二者封面完全一致，因此获取其中一个即可。尽管此操作几乎具备普适性，但仍然具有例外：通常体现在追加标准谱面的 DX 歌曲上，如： DX `VIIIbit Explorer`(ID 11235) 与 SD `VIIIbit Explorer`(ID 1235) 尽管同样在歌曲 ID 上相差10000，但其不属于 10001 至 11000 的 ID 区间。对于此类特例，可能会出现 API 缺少追加谱面封面的情况，此时需要您自行操作，如手动复制一份 DX 谱面的歌曲封面并重命名。

另外，在新版本更新、新歌追加伊始，水鱼数据库不能保证封面 API 维护的时效性。如果希望第一时间得到完整的歌曲封面数据，您可能需要手动对其进行搜集和维护。同时，一个无法检索到对应封面情况下的容错处理是必要的。

#### 3.1.10 获取公开的 用户-rating 完整数据

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/rating_ranking` | 无需验证 | GET |

此方法不设验证要求，您可以直接访问以下完整 URL 查看公开的 用户-rating 完整数据：

```plaintext
https://www.diving-fish.com/api/maimaidxprober/rating_ranking
```

请求成功后，服务器会以 JSON 格式返回包含所有公开的用户的 username-ra 数据，设置隐私的用户不在此列。如下，其中 JSON 已经美观输出：

```plaintext
[
  {
    "username": "user1",
    "ra": 11111
  },
  {
    "username": "user2",
    "ra": 12222
  },
  ...
]
```

尽管端点名为 `/rating_ranking` ，但返回的数据并非按照 `ra` 排序，要得到对应的排名数据，您仍然需要手动对数据进行排序。通过此方法，您可以设计返回指定用户排行的服务，以及获得当前水鱼的公开用户 `username` 数据，请确保妥善利用这些数据。完整的 用户-rating 数据较大，通常而言，您不需要在每次服务时都获取最新数据，具体的更新频率可以根据您提供的服务内容设定。

#### 3.1.11 更新用户的成绩信息

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/player/update_records` | [登录验证](#24-登录验证) / [Import-Token](#22-import-token验证要求) | POST |

附加了验证信息并成功验证之后，您可以更新用户的成绩信息。

要更新用户的成绩信息，您需要通过 POST 请求发送一个 JSON List 格式的请求体，其列表中每一项元素的格式可以参考 [用户的完整成绩信息](#315-获取用户的完整成绩信息) 中 `records` 中的一项。

以下是一个请求体的示例，包含了两首要更新的歌曲信息。实际更新时，您也只需要发送需要更新的歌曲信息即可：

```json
[
    {
        "achievements": 101.0000,
        "dxScore": 2711,
        "fc": "fc",
        "fs": "",
        "level_index": 3,
        "title": "Alea jacta est!",
        "type": "SD",
    },
    {
        "achievements": 100.777,
        "dxScore": 2458,
        "fc": "fc",
        "fs": "",
        "level_index": 4,
        "title": "Revive The Rave",
        "type": "SD",
    },
]
```

不难发现，要上传的实际歌曲成绩信息比在获取歌曲成绩信息时的条目少得多。必须包含，或者说实际生效的参数已经完全包含在上例中。以下是对于其中每个参数的硬性要求：

| **参数**         | **要求**                |
|------------------|-------------------------|
| `achievements`   | 超过101.0000的数据会被设为101.0000。当上传的数据不为数字时，POST请求总是失败          |
| `dxScore`        | 不设任何可能性验证，会被保留至整数部分（甚至允许负数）。当上传的数据不为数字时，该数据会被设置为0  |
| `fc`             | 不设任何可能性验证。当上传的数据不为（fc、fcp、ap、app）时，该数据会被设置为空            |
| `fs`             | 不设任何可能性验证。当上传的数据不为（sync、fs、fsp、fsd、fsdp）时，该数据会被设置为空            |
| `level_index`    | 必须对应该歌曲实际存在的谱面难度。当上传的数据不为整数或不为数字时，POST请求总是失败。当上传的数据为负数或不在实际存在的难度中时，该上传会被跳过 |
| `title`          | 作为确定歌曲的唯一凭证，而非 `song_id` ，必须严格遵循完整歌曲数据中的名称，否则该上传会被跳过            |
| `type`           | 必须对应该歌曲实际存在的 SD 或 DX 谱面，否则该上传会被跳过            |

请注意，上表中的硬性要求仅仅是对于边界条件的验证。为了提供高效而有价值的服务，在实际操作中，您总是应当上传规范而准确的歌曲成绩数据。

#### 3.1.12 通过 html 格式的数据更新用户的成绩信息

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/player/update_records_html` | [登录验证](#24-登录验证) | POST |

附加了登录验证信息并成功登录之后，您可以通过 html 格式的数据更新用户的成绩信息。

该功能实际上用于在 [diving-fish 查分器主页](https://www.diving-fish.com/maimaidx/prober/) 手动根据网页源代码导入歌曲成绩，详情可见 <https://www.diving-fish.com/maimaidx/prober_guide> 中的方法二。服务器会通过 parser 解析网页的 html 源代码并导入指定页面包含的成绩数据。要通过其他更直观的方法导入成绩数据，请参考 [更新用户的成绩信息](#3111-更新用户的成绩信息) 。

#### 3.1.13 更新用户的单曲成绩

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/player/update_record` | [登录验证](#24-登录验证) / [Import-Token](#22-import-token验证要求) | POST |

附加了验证信息并成功验证之后，您可以更新用户的单曲成绩。

更新用户的单曲成绩的流程与 [更新用户的成绩信息](#3111-更新用户的成绩信息) 完全一致，您只需要上传其中的一项成绩信息而非 JSON List 即可。

请注意，**通过这种方式更新的单曲成绩必须已经曾经上传至 diving-fish 数据库**，操作只是更新其具体的数值。如果您希望上传一个暂未被上传到 diving-fish 个人成绩数据库中的谱面成绩，比如某位用户希望上传其第一次游玩的谱面的成绩信息，请参考 [更新用户的成绩信息](#3111-更新用户的成绩信息) 。

#### 3.1.14 清除用户的所有 maimai 成绩信息

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/player/delete_records` | [登录验证](#24-登录验证) / [Import-Token](#22-import-token验证要求) | DELETE |

附加了验证信息并成功验证之后，您可以清除用户的所有 maimai 成绩信息。此时需要向端点发送 DELETE 请求。

请求成功后，所有 diving-fish 数据库上的用户成绩数据会被删除，但个人资料相关的信息会被保留。

删除成功后，服务器会返回响应体，包含被删除的歌曲成绩数量，例如：

```json
{"message": 617}
```

#### 3.1.15 返回谱面的拟合难度等数据

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/chart_stats` | 无需验证 | GET |

此方法不设验证要求，您可以直接访问以下完整 URL 查看谱面的拟合难度等数据：

```plaintext
https://www.diving-fish.com/api/maimaidxprober/chart_stats
```

发送 GET 请求后，服务器会返回 JSON 格式的响应体，包含 `charts` 和 `diff_data` 两个 JSON 字典。其中 `charts` 包含了以 `song_id` 为 key 的每首歌曲所有谱面的数据样本、拟合难度，平均达成率等信息。以下是一个示例：

```json
"8": [
      {
        "cnt": 1345,
        "diff": "5",
        "fit_diff": 5.05332093314643,
        "avg": 100.3753533829,
        "avg_dx": 260.443866171004,
        "std_dev": 0.666460481194254,
        "dist": [1, 1, 0, 0, 2, 19, 5, 4, 8, 7, 5, 8, 160, 1125],
        "fc_dist": [44, 107, 265, 376, 553]
      },
      {
        "cnt": 1353,
        "diff": "7",
        "fit_diff": 7.00483758316906,
        "avg": 99.6642371766444,
        "avg_dx": 321.150036954915,
        "std_dev": 1.41037575587035,
        "dist": [3, 0, 1, 2, 3, 31, 22, 29, 11, 24, 21, 45, 328, 833],
        "fc_dist": [126, 214, 544, 228, 241]
      },
      {
        "cnt": 2550,
        "diff": "10",
        "fit_diff": 10.3128969168726,
        "avg": 97.7445582352932,
        "avg_dx": 434.345490196078,
        "std_dev": 3.0782352855846,
        "dist": [5, 5, 3, 4, 3, 97, 239, 411, 196, 147, 114, 125, 368, 833],
        "fc_dist": [935, 520, 666, 198, 231]
      },
      {
        "cnt": 5769,
        "diff": "12",
        "fit_diff": 11.9801690111511,
        "avg": 99.3764014560584,
        "avg_dx": 780.463511873808,
        "std_dev": 1.61479033898565,
        "dist": [16, 2, 3, 2, 4, 49, 84, 243, 229, 524, 416, 603, 1268, 2326],
        "fc_dist": [1687, 1187, 2281, 312, 302]
      },
      {

      }
    ]
```

以下是上例中每一个参数的含义（例中 `song_id` 为 8 ）：

| **参数** | **含义** |
|----------|----------|
| `cnt`    | 样本数量 |
| `diff`   | 谱面的官标难度等级（精确到整数或 "+" 等级） |
| `fit_diff` | 谱面的拟合难度 |
| `avg`    | 谱面平均达成率 |
| `avg_dx` | 谱面平均 DX Scores |
| `std_dev` | 谱面达成率的标准差 |
| `dist`   | 评级分布（依次对应 d, c, b, bb, bbb, a, aa, aaa, s, sp, ss, ssp, sss, sssp） |
| `fc_dist` | Full Combo 分布（依次对应 非、fc、fcp、ap、app） |

拟合难度通过大量的成绩数据样本，对不同玩家的达成率、评级分布和 Full Combo 分布等因素进行综合分析后计算得出，提供了官标定数以外的参考难度，同时该方法提供的成绩分布等信息也具备价值。然而，由于个人差与其他各类因素的作用，拟合难度无法对每个用户都提供完全准确的难度判定，因此面向大量用户时，拟合难度仅作参考使用。

了解拟合难度的详细算法，可以查看 <https://github.com/Diving-Fish/maimaidx-prober/blob/main/database/routes/maimai.py> 与 <https://github.com/Diving-Fish/maimaidx-prober/blob/main/database/tools/maimai_analysis_curve.py> 中相关实现。

`diff_data` 字典则提供了基于不同难度等级的统计数据。以下是一个示例：

```json
"10": {
        "achievements": 98.3813000646974,
        "dist": [0.00169381069070557, 0.000587997652727524, 0.00121197108962394, 0.00129099986140477, 0.00251712535791482, 0.0251918954225238, 0.0447733378155622, 0.0960553437309247, 0.0830368279974168, 0.126461368790123, 0.0885511490134673, 0.107081626695211, 0.170145996809361, 0.251400549073034],
        "fc_dist": [0.530983112023284, 0.24423547035389, 0.152244800467095, 0.0585532426861526, 0.0139833744695783]
      }
```

以下是上例中每一个参数的含义（例中难度等级为 10 ）：

| **参数** | **含义** |
|----------|----------|
| `achievements`    | 难度平均达成率 |
| `dist`   | 难度的评级分布（依次对应 d, c, b, bb, bbb, a, aa, aaa, s, sp, ss, ssp, sss, sssp） |
| `fc_dist` | 难度的 Full Combo 分布（依次对应 非、fc、fcp、ap、app） |

字典中同样包含了宴谱的难度等级统计数据，如 `13+?` 、 `14?` 等。

通过该方法，您可以得到拟合难度信息为谱面难度提供额外的参考信息，您也可以根据得到的参考数据建立有意义的数据计算。

---

### 3.2 chunithmprober

当前 `chunithmprober` 部分文档暂待贡献。您可以参考 <https://github.com/Diving-Fish/maimaidx-prober/blob/main/database/routes/chunithm.py> 的源码与 [`maimaidxprober`](#31-maimaidxprober) 部分的交互逻辑。

---

### 3.3 public

#### 3.3.1 使用 diving-fish 账号登录

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/login` | [（登录验证）](#24-登录验证) | POST |

关于如何使用 diving-fish 账号登录，请参考 [2.4 登录验证](#24-登录验证) 。

#### 3.3.2 获取查分器主页的views次数

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/count_view` | 无需验证 | GET |

此方法不设验证要求。您可以通过向此端点发送 GET 请求获取查分器主页左上角的 Views 次数。服务器会以 JSON 格式返回如下的响应体：

```json
{"views":2583515}
```

随后您可以自由探索此数据的使用途径。

#### 3.3.3 验证服务器状态

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/alive_check` | 无需验证 | GET |

此方法不设验证要求。您可以通过向此端点发送 GET 请求验证服务器状态。如果运行正常，服务器会以 JSON 格式返回如下的响应体：

```json
{"message":"ok"}
```

#### 3.3.4 获取 / 提交查分器主页的今日留言

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/message` | 无需验证 / [登录验证](#24-登录验证) | GET / POST |

获取查分器主页的今日留言不设验证要求，您可以直接通过 <https://www.diving-fish.com/api/maimaidxprober/message> 进行访问。附加了登录验证信息并成功登录之后，您可以提交查分器主页的今日留言。

获取查分器主页的今日留言可以向端点发送 GET 请求，请求成功后，服务器会返回一个 JSON List 格式的响应体，包含留言文本、 `username` 、时间戳、马甲等。其中马甲可以在留言时实时指定而不与用户默认设定的 `nickname` 绑定。以下是一个可能的示例：

```json
[{"text": "周末了", "username": "document", "ts": 1722622060, "nickname": "可以用马甲欸"}]
```

提交查分器主页的今日留言可以向端点发送 POST 请求。您需要在请求体中包含 `nickname` 与 `text` 字段的信息，其中 `nickname` 参数不与用户默认设定的 `nickname` 存在相关要求。如果 `nickname` 参数为空，则默认以用户的 `username` 展示留言。并以 JSON 的格式发起请求。一旦请求成功，服务器会返回包含刚刚提交的留言在内的今日完整留言信息。如：

```json
{"text": "早"}
```

请求成功后，服务器会返回包含刚刚提交的留言在内的今日完整留言信息，如：

```json
[
    {"text": "周末了", "username": "document", "ts": 1722622060, "nickname": "可以用马甲欸"},
    {"text": "早", "username": "document", "ts": 1722622726, "nickname": ""}
]
```

#### 3.3.5 获取查分器主页的广告

| **端点路径** | **权限要求** |  **请求方法** |
|-----|-----|-----|
| `/advertisements` | 无需验证 | GET |

此方法不设验证要求，您可以直接通过 <https://www.diving-fish.com/api/maimaidxprober/advertisements> 进行访问。

向服务器发送 GET 请求成功后，服务器会以 JSON List 格式返回响应体，包含广告的超链接（点击跳转）以及广告图片 URL 。如：

```json
[
  {
    "l": "https://www.sample.com/",
    "s": "https://www.diving-fish.com/maimaidx/prober_static/sample.png"
  },
  {
    "l": "https://www.sample2.com/",
    "s": "https://www.diving-fish.com/maimaidx/prober_static/sample2.jpg"
  }
]
```

详情可以查看 [diving-fish 查分器主页](https://www.diving-fish.com/maimaidx/prober/) 的广告栏。

随后您可以自由探索此数据的使用途径。
