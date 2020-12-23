from functools import wraps

from quart import *
from _jwt import *
import asyncio
import motor.motor_asyncio
import json
import hashlib
import random
import string


def md5(v: str):
    return hashlib.md5(v.encode(encoding='UTF-8')).hexdigest()


app = Quart(__name__)

with open('config.json', encoding='utf-8') as fr:
    config = json.load(fr)
    db_url = config["database_url"]
    jwt_secret = config["jwt_secret"]
    fr.close()

client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
db = client["maimaidxprober"]


@app.after_request
def cors(environ):
    environ.headers['Access-Control-Allow-Origin'] = '*'
    environ.headers['Access-Control-Allow-Method'] = '*'
    environ.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
    return environ


@app.route("/feedback", methods=['POST'])
async def feedback():
    j = await request.get_json()
    await db.feedBack.insert_one(j)
    return {"message": "提交成功"}


def login_required(f):
    @wraps(f)
    async def func(*args, **kwargs):
        try:
            token = decode(request.cookies['jwt_token'])
        except KeyError:
            return {"status": "error", "msg": "尚未登录"}, 403
        if token == {}:
            return {"status": "error", "msg": "尚未登录"}, 403
        if token['exp'] < ts():
            return {"status": "error", "msg": "会话过期"}, 403
        g.username = token['username']
        g.user = await db.playerData.find_one({"username": g.username})
        return await f(*args, **kwargs)

    return func


@app.route("/login", methods=['POST'])
async def login():
    j = await request.get_json()
    username = j["username"]
    password = j["password"]
    try:
        user = await db.playerData.find_one({"username": username})
        if md5(password + user["salt"]) == user["password"]:
            resp = await make_response({"message": "登录成功"})
            resp.set_cookie('jwt_token', username_encode(username))
            return resp
    except Exception:
        pass
    return {
               "errcode": -3,
               "message": "用户名或密码错误",
           }, 401


@app.route("/register", methods=['POST'])
async def register():
    j = await request.get_json()
    user = await db.playerData.find_one({"username": j["username"]})
    if user is not None:
        return {
                   "errcode": -1,
                   "message": "此用户名已存在",
               }, 400
    salt = ''.join(random.sample(string.ascii_letters + string.digits, 16))
    await db.playerData.insert_one({
        "username": j["username"],
        "salt": salt,
        "password": md5(j["password"] + salt),
        "records": j["records"]
    })
    resp = await make_response({"message": "注册成功"})
    resp.set_cookie('jwt_token', username_encode(j["username"]))
    return resp


@app.route("/music_data", methods=['GET'])
async def get_music_data():
    csr = db.musicData.find()
    data = []
    async for c in csr:
        del c["_id"]
        data.append(c)
    resp = await make_response(json.dumps(data, ensure_ascii=False))
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp


@app.route("/player/records", methods=['GET'])
@login_required
async def get_records():
    records = g.user["records"]
    resp = await make_response('{"records":' + json.dumps(records, ensure_ascii=False) + ', "username": "' + g.username + '"}')
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp


def update_one(records, record):
    for i in range(len(records)):
        r = records[i]
        if r['level_index'] == record['level_index'] and r['title'] == record['title'] and r['type'] == record['type']:
            records[i] = record
            return
    records.append(record)


@app.route("/player/update_records", methods=['POST'])
@login_required
async def update_records():
    records = g.user["records"]
    j = await request.get_json()
    for r in j:
        update_one(records, r)
    g.user["records"] = records
    db.playerData.replace_one({'_id': g.user['_id']}, g.user)
    return {
        "message": "更新成功",
    }


@app.route("/player/update_record", methods=['POST'])
@login_required
async def update_record():
    records = g.user["records"]
    update_one(records, await request.get_json())
    g.user["records"] = records
    db.playerData.replace_one({'_id': g.user['_id']}, g.user)
    return {
        "message": "更新成功",
    }


def cal_ra(records):
    def isTypeSD(elem):
        return elem['type'] == 'SD'
    def isTypeDX(elem):
        return elem['type'] == 'DX'
    def get_ra(elem):
        return elem["ra"]
    sd_records = list(filter(isTypeSD, records))
    sd_records.sort(key=get_ra, reverse=True)
    dx_records = list(filter(isTypeDX, records))
    dx_records.sort(key=get_ra, reverse=True)
    rt = 0
    for i in range(min(25, len(sd_records))):
        rt += sd_records[i]["ra"]
    for i in range(min(15, len(dx_records))):
        rt += dx_records[i]["ra"]
    return rt


@app.route("/rating_ranking", methods=['GET'])
async def rating_ranking():
    csr = db.playerData.find()
    data = []
    async for player in csr:
        data.append({"username": player["username"], "ra": int(cal_ra(player["records"]))})
    resp = await make_response(json.dumps(data, ensure_ascii=False))
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp


app.run(host='0.0.0.0', port=8333, loop=asyncio.get_event_loop())
