"""用水鱼账号登录（BFF）。

查分器是 auth.diving-fish.com 的**机密客户端**，令牌只存在于后端：

    浏览器 --GET /oauth/login--> 这里 --302--> IdP
    IdP --302 带 code--> /oauth/callback（浏览器只是路过，JS 读不到 code）
    这里 --POST /oauth/token（服务器直连）--> IdP
    这里 --Set-Cookie: jwt_token--> 浏览器

于是「换 code」只是接在原来「校验 md5 密码」那个位置上，下游全都不用改：
login_required 读的还是同一个 jwt_token，import_token / developer-token
两条路径完全不受影响。

access token 和 id_token 都不落到浏览器，也不长期保存——这里只需要它们
问一次「你是谁」，问完就丢。真正的会话仍然是查分器自己那个 cookie。
"""

import json
import secrets
import time
from urllib.parse import urlencode, urlparse

import httpx
from quart import make_response, redirect, request

from access.redis import redis
from app import app, config
from models.maimai import Player
from tools._jwt import username_encode

_idp = config.get("idp") or {}
ISSUER = (_idp.get("issuer") or "").rstrip("/")
CLIENT_ID = _idp.get("client_id") or ""
CLIENT_SECRET = _idp.get("client_secret") or ""
REDIRECT_URI = _idp.get("redirect_uri") or ""
HOME = _idp.get("home") or "/"

#: 允许承载回调的站点。查分器同时挂在 maimai 和 www 两个域名下，CI 出的
#: 测试页（/maimaidx/prober-test/<sha>/）走的是 www——回调地址如果写死成
#: maimai，测试页登录完会跳到另一个域名，cookie 也落在那边，等于登不上。
#: 这里按请求的 Host 选回调地址，但只认下面列出来的域名：redirect_uri 在
#: IdP 侧是逐字符匹配的，凭 Host 头拼一个没注册过的地址只会被拒，
#: 而白名单保证我们连拼都不会去拼一个陌生域名。
CALLBACK_PATH = "/api/maimaidxprober/oauth/callback"
REDIRECT_HOSTS = _idp.get("redirect_hosts") or []

#: state 的存活时间。用户从点「登录」到输完密码跳回来，10 分钟足够，
#: 再长就只是给攻击者多留一个可用的 state
STATE_TTL = 600
STATE_PREFIX = "prober:oauth:state:"

_discovery = {"at": 0, "doc": None}


def enabled() -> bool:
    return bool(ISSUER and CLIENT_ID and CLIENT_SECRET and REDIRECT_URI)


async def discovery():
    """读发现文档，缓存 10 分钟。

    代码里只硬编码 issuer，端点一律从这里取——IdP 将来挪端点不用改查分器。
    """
    now = time.time()
    if _discovery["doc"] and now - _discovery["at"] < 600:
        return _discovery["doc"]
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{ISSUER}/.well-known/openid-configuration")
        resp.raise_for_status()
        doc = resp.json()
    if doc.get("issuer", "").rstrip("/") != ISSUER:
        # iss 对不上说明配置或 DNS 有问题，不能拿它去换令牌
        raise ValueError(f"发现文档的 issuer 不匹配：{doc.get('issuer')!r}")
    _discovery.update(at=now, doc=doc)
    return doc


def _pkce():
    import base64
    import hashlib

    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")
    return verifier, challenge


def _safe_next(target: str) -> str:
    """只允许站内相对路径。放开就是一个挂在查分器域名下的开放重定向。"""
    if not target or not target.startswith("/") or target.startswith("//"):
        return HOME
    return target


def _redirect_uri() -> str:
    """本次请求该用哪个回调地址。不在白名单里的 Host 一律回落到配置值。"""
    host = (request.host or "").split(":")[0]
    if host in REDIRECT_HOSTS:
        return f"https://{host}{CALLBACK_PATH}"
    return REDIRECT_URI


def _site_root() -> str:
    host = (request.host or "").split(":")[0]
    if host in REDIRECT_HOSTS:
        return f"https://{host}/"
    parsed = urlparse(REDIRECT_URI)
    return f"{parsed.scheme}://{parsed.netloc}/"


@app.route("/oauth/login", methods=["GET"])
async def oauth_login():
    if not enabled():
        return {"status": "error", "message": "未配置 OAuth 登录"}, 503

    verifier, challenge = _pkce()
    state = secrets.token_urlsafe(32)
    redirect_uri = _redirect_uri()
    await redis.set(
        STATE_PREFIX + state,
        # 回调地址一并存下来：换令牌时必须原样回传，两次不一致 IdP 会拒
        json.dumps({"v": verifier, "r": redirect_uri,
                    "next": _safe_next(request.args.get("next", ""))}),
        ex=STATE_TTL,
    )

    doc = await discovery()
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "openid profile",
        "state": state,
        "nonce": secrets.token_urlsafe(16),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    if request.args.get("prompt") == "login":
        # 「切换账号」：强制重新输密码，不吃 IdP 那边现成的 SSO 会话
        params["prompt"] = "login"

    authorize = doc["authorization_endpoint"] + "?" + urlencode(params)

    if request.args.get("screen") == "register":
        # 「注册」按钮走的是同一条流程，只是先落在 IdP 的注册页上。
        # 把授权请求做成注册页的 next，用户验证完邮箱就会被送回授权端点，
        # 第一方应用直接发码，一路跳回查分器时已经是登录态——
        # 不用注册完再自己回来点一次登录
        relative = authorize[len(ISSUER):] if authorize.startswith(ISSUER) else authorize
        return redirect(f"{ISSUER}/register?" + urlencode({"next": relative}))

    return redirect(authorize)


@app.route("/oauth/callback", methods=["GET"])
async def oauth_callback():
    if not enabled():
        return {"status": "error", "message": "未配置 OAuth 登录"}, 503

    error = request.args.get("error")
    if error:
        # 用户点了「拒绝」，或者 IdP 拒绝了这次请求
        return redirect(HOME + "?login_error=" + error)

    state = request.args.get("state", "")
    code = request.args.get("code", "")
    if not state or not code:
        return {"status": "error", "message": "回调参数不完整"}, 400

    # GETDEL：state 是一次性的，取出来就没了，重放同一个回调会落空
    raw = await redis.getdel(STATE_PREFIX + state)
    if not raw:
        # state 对不上就是 CSRF——这是这条流程唯一的防线，不能放过
        return {"status": "error", "message": "登录状态已过期，请重新登录"}, 400
    saved = json.loads(raw)

    doc = await discovery()
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(doc["token_endpoint"], data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": saved.get("r") or REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code_verifier": saved["v"],
        })
        if resp.status_code != 200:
            app.logger.warning("换令牌失败 %s %s", resp.status_code, resp.text[:200])
            return {"status": "error", "message": "登录失败，请重试"}, 502
        token = resp.json()

        # 不本地验签 id_token：这是机密客户端从 token 端点直连拿到的响应
        # （OIDC §3.1.3.7 允许省略），拿 access token 问一次 userinfo 更直接，
        # 也免得查分器为此引一套 JOSE 依赖
        resp = await client.get(doc["userinfo_endpoint"], headers={
            "Authorization": "Bearer " + token["access_token"]})
        if resp.status_code != 200:
            app.logger.warning("取 userinfo 失败 %s", resp.status_code)
            return {"status": "error", "message": "登录失败，请重试"}, 502
        info = resp.json()

    # sub 是 player.id 的字符串形式。优先按它查——用户名以后可能可改，sub 不会
    player = None
    try:
        player = await Player.aio_get(Player.id == int(info["sub"]))
    except Exception:
        username = info.get("preferred_username")
        if username:
            try:
                player = await Player.aio_get(Player.username == username)
            except Exception:
                player = None
    if player is None:
        app.logger.error("IdP 返回了查分器不认识的 sub=%r", info.get("sub"))
        return {"status": "error", "message": "账号不存在"}, 404

    app.logger.info("OAuth 登录成功 player_id=%s", player.id)
    resp = await make_response(redirect(_safe_next(saved.get("next", ""))))
    resp.set_cookie("jwt_token", username_encode(player.username),
                    max_age=30 * 86400)
    return resp


@app.route("/oauth/logout", methods=["GET", "POST"])
async def oauth_logout():
    """登出查分器，并顺手把 IdP 那边的 SSO 会话也结束掉。

    只清本地 cookie 是不够的：IdP 的会话还在，用户再点一次「登录」会
    一声不响地又登回来，看起来就像登出没生效。
    """
    target = HOME
    if enabled():
        target = f"{ISSUER}/oauth/logout?" + urlencode({
            # 没留 id_token，用 client_id 指明身份（OIDC RP-Initiated Logout
            # 允许），落点仍要在 IdP 侧注册过才会跳
            "client_id": CLIENT_ID,
            "post_logout_redirect_uri": _site_root(),
        })
    resp = await make_response(redirect(target))
    resp.set_cookie("jwt_token", "", expires=0)
    return resp
