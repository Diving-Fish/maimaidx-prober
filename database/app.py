from ast import arg
from datetime import datetime, timedelta, timezone
from email.utils import formatdate
from functools import wraps
import hashlib
from quart import *
from models.maimai import *
from tools._jwt import username_encode, decode, ts
import tools.oauth_rs as oauth_rs
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
from pathlib import Path
from urllib.parse import urlparse, unquote
from access.redis import redis
import os
import socket
from uuid import uuid4


def md5(v: str):
    return hashlib.md5(v.encode(encoding='UTF-8')).hexdigest()
    

app = Quart(__name__)
scheduler = AsyncIOScheduler()


config = ...
db_url = ...
jwt_secret = ...
mail_config = ...
ci_token = ...
# NEW: global scheduler
scheduler = AsyncIOScheduler()
chart_stat_updated = False

# ...existing code...
with open('config.json', encoding='utf-8') as fr:
    config = json.load(fr)
    db_url = config["mysql_url"]
    jwt_secret = config["jwt_secret"]
    mail_config = config["mail"]
    ci_token = config["ci_token"]

# 资源服务器那一半：验 IdP 签的 access token，让第三方应用能代用户读写数据。
# issuer 复用 BFF 登录已有的那段配置；audience 是查分器自己的资源标识，
# 必须和 IdP 的 prober_audience 一字不差，否则所有票都会被判「不是发给我的」。
_idp_conf = config.get("idp") or {}
oauth_rs.init(
    _idp_conf.get("issuer") or "",
    _idp_conf.get("resource") or "https://www.diving-fish.com/api/maimaidxprober",
)

#: 开发者 token 的全局日落时刻：2026-10-01 00:00 (UTC+8)。到这一刻为止
#: developer_required 的接口照常工作，之后一律 410。
#:
#: 写成带时区的字面量而不是 datetime(2026, 10, 1)：对外公告的是北京时间的
#: 10 月 1 日零点，这台机器现在恰好是 CST，但服务器时区是运维配置，不该由它
#: 决定几百个第三方服务在哪一秒停摆。
DEVELOPER_TOKEN_SUNSET_TS = int(
    datetime(2026, 10, 1, tzinfo=timezone(timedelta(hours=8))).timestamp())

#: 新的开发者接入入口。申请的不再是「一个能查全库的 token」，而是一个应用：
#: 填名称、描述、需要的权限，用户逐个授权，可随时撤销。
#: 指向控制台而不是文档站——这条消息是「你刚才想申请的东西在哪」的回答，
#: 落到能直接动手的那一页才有用。
APPLICATION_DOC_URL = "https://auth.diving-fish.com/console"

#: 迁移说明。和上面那条的分工：控制台回答「去哪申请」，这份文档回答
#: 「我原来的调用怎么改」——被日落挡下来的人要的是后者。
MIGRATION_DOC_URL = "https://maimai.diving-fish.com/manual/docs/developer/oauth-migration"


def developer_token_sunset_ts(dev) -> int:
    """这个 token 什么时候停。0 表示没单独续期，按全局日落算。"""
    return getattr(dev, 'sunset_ts', 0) or DEVELOPER_TOKEN_SUNSET_TS


# NEW: helper to parse mysql url
def _parse_mysql_url(url: str):
    """
    Support formats like:
    - mysql://user:pass@host:3306/db
    - mysql+pymysql://user:pass@host/db
    - mysql+aiomysql://user:pass@host/db
    """
    p = urlparse(url)
    return {
        "host": p.hostname or "127.0.0.1",
        "port": p.port or 3306,
        "user": unquote(p.username or ""),
        "password": unquote(p.password or ""),
        "database": (p.path or "/").lstrip("/"),
    }

# NEW: execute the SQL file (runs in a thread)
def _execute_fixed_inner_level_sql():
    # Prefer config['db_url'], fallback to config['mysql_url'] and db_url variable
    mysql_url = config.get("db_url") or config.get("mysql_url") or db_url
    if not mysql_url:
        raise RuntimeError("No db_url/mysql_url found in config.json")

    creds = _parse_mysql_url(mysql_url)
    sql_file = Path(__file__).parent / "fixed-inner-level.sql"
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    # Lazy import to avoid hard dependency unless the job runs
    import pymysql
    from pymysql.constants import CLIENT

    conn = pymysql.connect(
        host=creds["host"],
        port=creds["port"],
        user=creds["user"],
        password=creds["password"],
        database=creds["database"],
        charset="utf8mb4",
        autocommit=True,
        client_flag=CLIENT.MULTI_STATEMENTS,
    )
    try:
        with conn.cursor() as cur, open(sql_file, "r", encoding="utf-8") as f:
            sql = f.read()
            # Execute all statements in one go; advance through all result sets
            cur.execute(sql)
            while cur.nextset():
                pass
    finally:
        global chart_stat_updated
        chart_stat_updated = True
        conn.close()

# NEW: async job wrapper for scheduler
async def run_fixed_inner_level_job():
    """
    Execute the fixed-inner-level.sql once across multiple instances using a Redis lock.
    """
    lock_key = "job:fixed_inner_level:lock"
    # Give the job ample time (1 hour) to finish before the lock expires.
    lock_ttl = 3600

    # Acquire a distributed lock so only one instance proceeds
    lock_token = f"{socket.gethostname()}:{os.getpid()}:{uuid4().hex}"
    try:
        acquired = await redis.set(lock_key, lock_token, nx=True, ex=lock_ttl)
        if not acquired:
            app.logger.info("Skip fixed-inner-level job: another instance holds the lock.")
            return

        await asyncio.to_thread(_execute_fixed_inner_level_sql)
        app.logger.info("fixed-inner-level.sql executed successfully at 03:00 by this instance.")
    except Exception as e:
        app.logger.exception(f"Error executing fixed-inner-level.sql: {e}")
    finally:
        # Safely release the lock only if we still own it
        try:
            lua = """
            if redis.call('GET', KEYS[1]) == ARGV[1] then
                return redis.call('DEL', KEYS[1])
            else
                return 0
            end
            """
            await redis.eval(lua, 1, lock_key, lock_token)
        except Exception:
            # If release fails (e.g., TTL expired), it's safe to ignore
            pass

async def refresh_oauth_jwks():
    """把 IdP 的公钥拉进内存。

    放后台任务而不是请求路径上：请求里同步拉一次 JWKS 会把 IdP 的延迟
    直接加到每个第三方调用上，IdP 抖一下就是查分器抖一下。
    """
    try:
        n = await oauth_rs.refresh_jwks(force=True)
        app.logger.info("已刷新 IdP JWKS，公钥 %s 个", n)
    except Exception as e:
        # 拉不到就沿用内存里那份旧的。IdP 短暂不可用不该让已签发的令牌失效
        app.logger.warning("刷新 IdP JWKS 失败：%s", e)


@app.before_serving
async def startup():
    db.set_allow_sync(False)
    # NEW: schedule daily job at 03:00
    try:
        trigger = CronTrigger(hour=3, minute=0)
        scheduler.add_job(
            run_fixed_inner_level_job,
            trigger=trigger,
            id="fixed_inner_level_daily_3am",
            replace_existing=True,
        )
        if oauth_rs.enabled():
            # 5 分钟一次。密钥轮换时新 kid 会先出现在 JWKS 里、再开始用于
            # 签名，所以这个间隔不会造成验签失败；真遇上陌生 kid，
            # oauth_rs.verify 会当场补拉一次
            scheduler.add_job(
                refresh_oauth_jwks,
                trigger=IntervalTrigger(minutes=5),
                id="refresh_oauth_jwks",
                replace_existing=True,
            )
            await refresh_oauth_jwks()
        scheduler.start()
        app.logger.info("AsyncIOScheduler started; daily SQL job scheduled at 03:00.")
    except Exception as e:
        app.logger.exception(f"Failed to start scheduler: {e}")

# NEW: gracefully shutdown scheduler
@app.after_serving
async def shutdown():
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            app.logger.info("AsyncIOScheduler stopped.")
    except Exception as e:
        app.logger.exception(f"Failed to stop scheduler: {e}")

@app.after_request
def cors(environ):
    environ.headers['Access-Control-Allow-Origin'] = '*'
    environ.headers['Access-Control-Allow-Method'] = '*'
    environ.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type,import-token,authorization'
    # **白名单，不是黑名单。** 只有「浏览器拿 cookie 登录」这一种认证路径
    # 该续期会话 cookie。
    #
    # 这里曾经写成 login_type != 'token'（排除 Import-Token），于是每加一条
    # 认证路径就要记得回来改一次；Bearer 上线时如果忘了，任何 bot 拿一张
    # 只读的 access token 调一次接口，就会从响应里收到一个 30 天有效、
    # 能调 /player/change_password 的会话 cookie——等于只读权限升级成接管账号。
    # 反过来写就不会有下一次：新路径默认不发 cookie。
    if (getattr(g, "user", None) is not None
            and getattr(g, "login_type", None) == 'cookie'
            and request.method != 'OPTIONS'):
        environ.set_cookie('jwt_token', username_encode(g.username), max_age=30 * 86400)
    return environ


def login_required(f):
    @wraps(f)
    async def func(*args, **kwargs):
        try:
            token = decode(request.cookies['jwt_token'])
        except KeyError:
            return {"status": "error", "message": "尚未登录"}, 403
        if token == {}:
            return {"status": "error", "message": "尚未登录"}, 403
        if token['exp'] < ts():
            return {"status": "error", "message": "会话过期"}, 403
        g.username = token['username']
        g.user = await Player.aio_get(Player.username == g.username)
        # after_request 的 cookie 续期按 login_type 白名单放行，这里必须标出来，
        # 否则 @login_required 的接口会静默地不再续期会话
        g.login_type = 'cookie'
        return await f(*args, **kwargs)

    return func


async def _auth_by_cookie():
    """Cookie 认证。返回 None 表示成功，否则是要直接回给调用方的响应。"""
    try:
        token = decode(request.cookies['jwt_token'])
    except KeyError:
        return {"status": "error", "message": "尚未登录"}, 403
    if token == {}:
        return {"status": "error", "message": "尚未登录"}, 403
    if token['exp'] < ts():
        return {"status": "error", "message": "会话过期"}, 403
    g.username = token['username']
    g.user = await Player.aio_get(Player.username == g.username)
    g.login_type = 'cookie'
    return None


async def _auth_by_import_token(import_token):
    try:
        g.user = await Player.aio_get(Player.import_token == import_token)
        g.username = g.user.username
        g.login_type = 'token'
    except Exception:
        return {"status": "error", "message": "导入token有误"}, 400
    return None


async def _auth_by_bearer(token, required_scopes):
    """OAuth：第三方应用代用户访问。

    票里已经写明了是哪个用户（sub），所以**请求里不需要、也不接受
    qq / username 参数**——这正是和 developer-token 的根本区别：那边
    「查谁」由调用方指定，这边由用户的授权决定。

    检查顺序刻意如此：先验票（便宜、无 IO），再查 scope（同样便宜），
    最后才落库查用户和记配额。无效的票不该产生任何数据库或 Redis 流量。
    """
    if not oauth_rs.enabled():
        return {"status": "error", "message": "服务端未启用 OAuth"}, 503

    try:
        claims = await oauth_rs.verify(token)
    except oauth_rs.TokenError as e:
        # 401 + WWW-Authenticate 是 RFC 6750 规定的形式，客户端库据此
        # 判断「该去刷新令牌了」。用 403 会让它们以为是权限问题而不重试
        return {"status": "error", "message": str(e)}, 401

    scopes = oauth_rs.scopes_of(claims)
    missing = [s for s in required_scopes if s not in scopes]
    if missing:
        return {
            "status": "error",
            "message": "access token 缺少权限：" + " ".join(missing),
        }, 403

    try:
        user = await Player.aio_get(Player.id == int(claims["sub"]))
    except Exception:
        return {"status": "error", "message": "用户不存在"}, 400

    # 用户协议是查分器自己的规则，IdP 不管这一列。用户本人访问自己的数据
    # 时历来不检查，但第三方代访问必须过这道——同意页给的是「让某个应用
    # 读我的成绩」的许可，不是豁免协议
    if not user.accept_agreement:
        return {"status": "error", "message": "该用户未同意用户协议"}, 403

    ok, msg = await _oauth_quota(claims, user)
    if not ok:
        return {"status": "error", "message": msg}, 429

    g.user = user
    g.username = user.username
    g.login_type = 'oauth'
    g.oauth_claims = claims
    g.client_id = oauth_rs.acting_client(claims)
    g.scopes = scopes

    # 代写留一条日志。读取量大得多，记了只会淹掉有用的信息；而「谁改了我的
    # 成绩」是唯一真正需要事后追查的问题——成绩被覆盖是不可恢复的
    if oauth_rs.is_delegated(claims) and any(
            s.endswith(".write") for s in required_scopes):
        app.logger.info(
            "OAuth 代写 client_id=%s user_id=%s path=%s",
            g.client_id, user.id, request.path,
        )
    return None


async def _oauth_quota(claims, user):
    """调用配额。额度由 IdP 写在票里（df_quota），这里只负责数和拦。

    两个维度含义不同：按用户的那条保护用户（一个 bot 一天拉同一个人
    几千次不是正常用法，而今天的 developer-token 完全没有这层），
    按应用的那条保护基础设施。
    """
    per_user, per_client = oauth_rs.quota_of(claims)
    client_id = oauth_rs.acting_client(claims) or "unknown"
    day = time.strftime("%Y%m%d", time.gmtime())
    try:
        for key, limit in (
            (f"prober:oauth:q:u:{client_id}:{user.id}:{day}", per_user),
            (f"prober:oauth:q:c:{client_id}:{day}", per_client),
        ):
            n = await redis.incr(key)
            if n == 1:
                await redis.expire(key, 172800)
            if n > limit:
                app.logger.warning("OAuth 配额超限 %s count=%s limit=%s", key, n, limit)
                return False, "已超出今日请求上限"
    except Exception:
        # Redis 挂了不该把所有第三方访问一起挡死——配额是限流，不是授权
        app.logger.exception("OAuth 配额计数失败，放行本次请求")
    return True, ""


def login_or_token_required(f):
    """Cookie 或 Import-Token。**不接受 Bearer**——OAuth 那条路要声明 scope，
    见 oauth_or_login_required。"""
    @wraps(f)
    async def func(*args, **kwargs):
        import_token = request.headers.get('Import-Token', default='')
        if import_token != '':
            err = await _auth_by_import_token(import_token)
        else:
            err = await _auth_by_cookie()
        if err is not None:
            return err
        return await f(*args, **kwargs)

    return func


def oauth_or_login_required(*required_scopes):
    """Cookie / Import-Token / Bearer 三条路都认，Bearer 必须带够 scope。

    scope 写在装饰器上而不是集中在一张表里：它是这个接口的一部分，
    改接口语义的人应该在同一屏里看到它。漏写就等于「任何 scope 都能调」，
    集中配置更容易漏。
    """
    def deco(f):
        @wraps(f)
        async def func(*args, **kwargs):
            auth = request.headers.get('Authorization', default='')
            import_token = request.headers.get('Import-Token', default='')
            if auth[:7].lower() == 'bearer ':
                err = await _auth_by_bearer(auth[7:].strip(), required_scopes)
            elif import_token != '':
                err = await _auth_by_import_token(import_token)
            else:
                err = await _auth_by_cookie()
            if err is not None:
                return err
            return await f(*args, **kwargs)

        return func

    return deco


async def is_developer(token):
    if token == "":
        return False, {"status": "error", "msg": "请先联系水鱼申请开发者token"}, 400
    try:
        dev: NewDeveloper = await NewDeveloper.aio_get(NewDeveloper.token == token)
        if not dev.available:
            raise Exception("")

        today = datetime.today()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)

        day_start_ts = start_of_day.timestamp() * 1e9
        day_end_ts = day_start_ts + 86400 * 1e9

        max_request_count = [0, 300, 1000, 3000, 1e4]
        count = await NewDeveloperLog.select().where((NewDeveloperLog.developer == dev) & (NewDeveloperLog.timestamp > day_start_ts) & (NewDeveloperLog.timestamp < day_end_ts)).aio_count()

        if count >= max_request_count[dev.level]:
            return False, {"status": "error", "msg": "已超出今日请求上限"}, 400

    except Exception:
        try:
            dev: Developer = await Developer.aio_get(Developer.token == token)
        except Exception:
            return False, {"status": "error", "msg": "开发者token有误"}, 400
    if not dev.available:
        return False, {"status": "error", "msg": "开发者token被禁用，请联系水鱼重新登记信息"}, 400

    # **日落。** 到点之后一律拒绝，不看等级也不看配额——留一个「还能读全库、
    # 只是今天额度没用完」的口子，等于日落没发生。两张表都走这里，老的
    # Developer 和新的 NewDeveloper 同一天停。
    #
    # 410 而不是 403：403 是「你没权限」，客户端库通常会重试或提示用户重新
    # 登记；410 是「这个东西已经不在了」，正好是这里发生的事，对方的日志里
    # 也能和「token 被禁用」一眼区分开。
    sunset_ts = developer_token_sunset_ts(dev)
    if ts() >= sunset_ts:
        sunset_text = datetime.fromtimestamp(
            sunset_ts, timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M (UTC+8)')
        return False, {
            "status": "error",
            "msg": f"开发者 token 已于 {sunset_text} 停止服务，请改用水鱼账号 OAuth："
                   f"{APPLICATION_DOC_URL}（迁移说明：{MIGRATION_DOC_URL}）",
            "sunset": sunset_ts,
            "migration": MIGRATION_DOC_URL,
        }, 410

    return True, dev, 200


def developer_required(f):
    @wraps(f)
    async def func(*args, **kwargs):
        token = request.headers.get("developer-token", default="")
        res = await is_developer(token)
        if not res[0]:
            return res[1], res[2]
        remote_addr = request.remote_addr
        xip = request.headers.get("X-Real-IP", default="")
        if xip != "":
            remote_addr = xip
        if isinstance(res[1], Developer):
            await DeveloperLog.aio_create(developer=res[1], function=f.__name__, remote_addr=remote_addr, timestamp=time.time_ns())
        else:
            request_args = {}
            for key in request.args:
                request_args[key] = request.args.get(key)
            request_body = str(await request.body, encoding='utf-8')
            await NewDeveloperLog.aio_create(developer=res[1], function=f.__name__, remote_addr=remote_addr, timestamp=time.time_ns(), request_args=request_args, request_body=request_body)

        # RFC 8594 的日落声明。挂在**成功**响应上是有意的：需要看到它的正是
        # 那批还在正常调用、没读过公告也没回过邮件的接入方，日落之后这段不再
        # 执行，他们收到的是 410。邮件可能发给了一个早就没人看的地址，
        # 但这几个头一定会到达真正在跑的那台机器上。
        resp = await make_response(await f(*args, **kwargs))
        sunset_ts = developer_token_sunset_ts(res[1])
        resp.headers['Sunset'] = formatdate(sunset_ts, usegmt=True)
        resp.headers['Deprecation'] = 'true'
        resp.headers['Link'] = f'<{MIGRATION_DOC_URL}>; rel="sunset"; type="text/html"'
        return resp

    return func


def ci_access_required(f):
    @wraps(f)
    async def func(*args, **kwargs):
        token = request.args.get("token", type=str, default="")
        if token != ci_token:
            return "ERROR", 403
        return await f(*args, **kwargs)

    return func
