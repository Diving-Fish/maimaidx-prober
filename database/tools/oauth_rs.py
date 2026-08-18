"""把查分器变成 OAuth 资源服务器：验 access token。

access token 是 IdP 用 RS256 签的 JWT，**本地验签，不查库、不问 IdP**。
每个请求去问一次 IdP 会把登录服务变成查分器的同步依赖——IdP 抖一下，
所有 bot 一起 500。代价是令牌不可即时吊销，最长有它剩余寿命的窗口
（授权码那条路 15 分钟，bot 换票那条路 5 分钟），这是既定取舍。

必须检查的四件事，少一件这套授权就白做了：

  iss    是不是我们那个 IdP 签的
  aud    这张票是不是发给查分器的。**不查这条**，签给别的资源服务器的票
         就能直接拿来打查分器——它们用的是同一套 JWKS
  exp    过期没有
  scope  这个操作要的权限在不在票里

JWKS 由后台任务定时刷新，请求路径上只读内存。密钥轮换时新 kid 会先出现
在 JWKS 里、再开始用于签名，所以定时刷新不会造成验签失败；真碰上没见过
的 kid，会立刻补拉一次（带节流，免得被无效 token 拖成 JWKS 压测）。
"""

import json
import time

import httpx
import jwt as pyjwt
from jwt.algorithms import RSAAlgorithm

#: 由 app.py 注入
_settings = {
    "issuer": "",
    "audience": "",
    "enabled": False,
}

_jwks = {"keys": {}, "at": 0.0, "last_try": 0.0}

#: 没见过的 kid 最多这么频繁地触发一次补拉
_REFETCH_INTERVAL = 30


class TokenError(Exception):
    """票不合法。message 会原样回给调用方——写给 bot 开发者看。"""


def init(issuer: str, audience: str):
    _settings["issuer"] = (issuer or "").rstrip("/")
    _settings["audience"] = audience or ""
    _settings["enabled"] = bool(_settings["issuer"] and _settings["audience"])
    return _settings["enabled"]


def enabled() -> bool:
    return _settings["enabled"]


async def refresh_jwks(force=False) -> int:
    """拉一次 JWKS。返回拿到的公钥数量。

    定时任务和「遇到陌生 kid」都走这里。失败时保留上一份——
    IdP 短暂不可用不该让所有已签发的令牌立刻失效。
    """
    if not _settings["enabled"]:
        return 0
    now = time.time()
    if not force and now - _jwks["last_try"] < _REFETCH_INTERVAL:
        return len(_jwks["keys"])
    _jwks["last_try"] = now

    url = f"{_settings['issuer']}/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        doc = resp.json()

    keys = {}
    for jwk in doc.get("keys", []):
        kid = jwk.get("kid")
        if not kid or jwk.get("kty") != "RSA":
            continue
        # PyJWT 2.4 没有异步的 JWKS 客户端，自己按 kid 建索引就够了
        keys[kid] = RSAAlgorithm.from_jwk(json.dumps(jwk))
    if keys:
        _jwks["keys"] = keys
        _jwks["at"] = now
    return len(_jwks["keys"])


async def verify(token: str) -> dict:
    """验签 + 校验 iss / aud / exp，返回 claims。不合法就抛 TokenError。"""
    if not _settings["enabled"]:
        raise TokenError("服务端未配置 OAuth")
    if not token:
        raise TokenError("缺少 access token")

    try:
        kid = pyjwt.get_unverified_header(token).get("kid")
    except pyjwt.PyJWTError:
        raise TokenError("access token 格式不正确")

    key = _jwks["keys"].get(kid)
    if key is None:
        # 没见过的 kid：可能刚轮换过密钥，补拉一次再看
        await refresh_jwks()
        key = _jwks["keys"].get(kid)
    if key is None:
        raise TokenError("access token 的签名密钥未知")

    try:
        claims = pyjwt.decode(
            token,
            key=key,
            algorithms=["RS256"],
            audience=_settings["audience"],
            issuer=_settings["issuer"],
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except pyjwt.ExpiredSignatureError:
        raise TokenError("access token 已过期")
    except pyjwt.InvalidAudienceError:
        # 最常见的原因是申请的 scope 里没有 prober.* ——那种票的 aud
        # 里不会有查分器，拿来打查分器就该被拒
        raise TokenError("这张 access token 不是发给查分器的")
    except pyjwt.PyJWTError as e:
        raise TokenError(f"access token 无效（{type(e).__name__}）")

    return claims


def scopes_of(claims: dict) -> set:
    return set((claims.get("scope") or "").split())


def acting_client(claims: dict) -> str:
    """哪个应用在调这次请求。

    优先取 act.client_id（RFC 8693 的委托标记，bot 换票那条路会带），
    退回 client_id。两者在换票场景下是同一个值，区别在于 act 的存在
    本身就说明「这不是用户自己在操作」。
    """
    act = claims.get("act") or {}
    return act.get("client_id") or claims.get("client_id") or ""


def is_delegated(claims: dict) -> bool:
    return bool((claims.get("act") or {}).get("client_id"))


def quota_of(claims: dict) -> tuple:
    """(每用户每日, 每应用每日)。

    配额是 IdP 写进票里的（df_quota claim），查分器只负责执行。
    这样查分器不用去读 IdP 的 oauth_client 表——依赖方向不能反过来。
    缺这个 claim 的票按保守值处理。
    """
    q = claims.get("df_quota") or {}
    try:
        return int(q.get("u") or 200), int(q.get("c") or 10000)
    except (TypeError, ValueError):
        return 200, 10000
