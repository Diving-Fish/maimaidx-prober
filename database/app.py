from ast import arg
from datetime import datetime
from functools import wraps
import hashlib
from quart import *
from models.maimai import *
from tools._jwt import username_encode, decode, ts
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
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
    environ.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type,import-token'
    if getattr(g, "user", None) is not None and request.method != 'OPTIONS':
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
        return await f(*args, **kwargs)

    return func


def login_or_token_required(f):
    @wraps(f)
    async def func(*args, **kwargs):
        import_token = request.headers.get('Import-Token', default='')
        if import_token != '':
            try:
                g.user = await Player.aio_get(Player.import_token == import_token)
                g.username = g.user.username
            except Exception:
                return {"status": "error", "message": "导入token有误"}, 400
        else:
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
        
        return await f(*args, **kwargs)

    return func


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
        return await f(*args, **kwargs)

    return func


def ci_access_required(f):
    @wraps(f)
    async def func(*args, **kwargs):
        token = request.args.get("token", type=str, default="")
        if token != ci_token:
            return "ERROR", 403
        return await f(*args, **kwargs)

    return func
