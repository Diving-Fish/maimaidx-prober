from ast import arg
from datetime import datetime
from functools import wraps
import hashlib
from quart import *
from access.maimai import flush_update_cache
from models.maimai import *
from tools._jwt import username_encode, decode, ts
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from access.redis import redis


def md5(v: str):
    return hashlib.md5(v.encode(encoding='UTF-8')).hexdigest()
    

app = Quart(__name__)


config = ...
db_url = ...
jwt_secret = ...
mail_config = ...
ci_token = ...


with open('config.json', encoding='utf-8') as fr:
    config = json.load(fr)
    db_url = config["database_url"]
    jwt_secret = config["jwt_secret"]
    mail_config = config["mail"]
    ci_token = config["ci_token"]


@app.before_serving
async def startup():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        func=flush_update_cache,
        trigger=CronTrigger(hour=4, minute=0, second=0),
        misfire_grace_time=60
    )

    scheduler.start()

@app.after_request
def cors(environ):
    cur = datetime.today()
    try:
        log = RequestLog.get((cur.hour == RequestLog.hour) & (cur.day == RequestLog.day) & (cur.month == RequestLog.month) & (cur.year == RequestLog.year) & (request.path == RequestLog.path))
        log.times += 1
        log.save()
    except Exception:
        log = RequestLog()
        log.year = cur.year
        log.month = cur.month
        log.day = cur.day
        log.hour = cur.hour
        log.times = 1
        log.path = request.path
        log.save()
    environ.headers['Access-Control-Allow-Origin'] = '*'
    environ.headers['Access-Control-Allow-Method'] = '*'
    environ.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
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
        g.user = Player.get(Player.username == g.username)
        return await f(*args, **kwargs)

    return func


def login_or_token_required(f):
    @wraps(f)
    async def func(*args, **kwargs):
        import_token = request.headers.get('Import-Token', default='')
        if import_token != '':
            try:
                g.user = Player.get(Player.import_token == import_token)
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
            g.user = Player.get(Player.username == g.username)
        
        return await f(*args, **kwargs)

    return func


def is_developer(token):
    if token == "":
        return False, {"status": "error", "msg": "请先联系水鱼申请开发者token"}, 400
    try:
        dev: NewDeveloper = NewDeveloper.get(NewDeveloper.token == token)
        if not dev.available:
            raise Exception("")

        today = datetime.today()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)

        day_start_ts = start_of_day.timestamp() * 1e9
        day_end_ts = day_start_ts + 86400 * 1e9

        max_request_count = [0, 300, 1000, 3000, 1e4]
        count = NewDeveloperLog.select().where((NewDeveloperLog.developer == dev) & (NewDeveloperLog.timestamp > day_start_ts) & (NewDeveloperLog.timestamp < day_end_ts)).count()

        if count >= max_request_count[dev.level]:
            return False, {"status": "error", "msg": "已超出今日请求上限"}, 400

    except Exception:
        try:
            dev: Developer = Developer.get(Developer.token == token)
        except Exception:
            return False, {"status": "error", "msg": "开发者token有误"}, 400
    if not dev.available:
        return False, {"status": "error", "msg": "开发者token被禁用，请联系水鱼重新登记信息"}, 400
    return True, dev, 200


def developer_required(f):
    @wraps(f)
    async def func(*args, **kwargs):
        token = request.headers.get("developer-token", default="")
        res = is_developer(token)
        if not res[0]:
            return res[1], res[2]
        remote_addr = request.remote_addr
        xip = request.headers.get("X-Real-IP", default="")
        if xip != "":
            remote_addr = xip
        if isinstance(res[1], Developer):
            DeveloperLog.create(developer=res[1], function=f.__name__, remote_addr=remote_addr, timestamp=time.time_ns())
        else:
            request_args = {}
            for key in request.args:
                request_args[key] = request.args.get(key)
            request_body = str(await request.body, encoding='utf-8')
            NewDeveloperLog.create(developer=res[1], function=f.__name__, remote_addr=remote_addr, timestamp=time.time_ns(), request_args=request_args, request_body=request_body)
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
