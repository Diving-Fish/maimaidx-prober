from ast import arg
from datetime import datetime
from functools import wraps
import hashlib
from quart import *
from models.maimai import *
from tools._jwt import decode, ts


def md5(v: str):
    return hashlib.md5(v.encode(encoding='UTF-8')).hexdigest()
    

app = Quart(__name__)


config = ...
db_url = ...
jwt_secret = ...
mail_config = ...


with open('config.json', encoding='utf-8') as fr:
    config = json.load(fr)
    db_url = config["database_url"]
    jwt_secret = config["jwt_secret"]
    mail_config = config["mail"]


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


def developer_required(f):
    @wraps(f)
    async def func(*args, **kwargs):
        token = request.headers.get("developer-token", default="")
        if token == "":
            return {"status": "error", "msg": "请先联系水鱼申请开发者token"}, 400
        try:
            dev: Developer = Developer.get(Developer.token == token)
        except Exception:
            return {"status": "error", "msg": "开发者token有误"}, 400
        if not dev.available:
            return {"status": "error", "msg": "开发者token被禁用"}, 400
        remote_addr = request.remote_addr
        xip = request.headers.get("X-Real-IP", default="")
        if xip != "":
            remote_addr = xip
        DeveloperLog.create(developer=dev, function=f.__name__, remote_addr=remote_addr, timestamp=time.time_ns())
        return await f(*args, **kwargs)

    return func