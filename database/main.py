from collections import defaultdict
from functools import wraps
from typing import Optional, Dict

from quart import *
from _jwt import *
import asyncio
from models import *
import json
import hashlib
import random
import string


def md5(v: str):
    return hashlib.md5(v.encode(encoding='UTF-8')).hexdigest()


def music_data():
    data = []
    dct = None
    music = Music.select(Music, Chart).join(Chart)
    prev_music_id = 0
    for m in music:
        m: Music
        if m.id != prev_music_id:
            if dct:
                data.append(dct)
            prev_music_id = m.id
            value = vars(m)['__data__']
            dct = {
                "id": str(value["id"]),
                "title": value["title"],
                "type": value["type"],
                "ds": [],
                "level": [],
                "charts": [],
                "basic_info": {
                    "title": value["title"],
                    "artist": value["artist"],
                    "genre": value["genre"],
                    "bpm": value["bpm"],
                    "release_date": value["release_date"],
                    "from": value["version"]
                }
            }
        c: Chart = m.chart
        dct['ds'].append(c.ds)
        dct['level'].append(c.difficulty)
        if m.type == 'SD':
            notes = [c.tap_note, c.hold_note, c.slide_note, c.break_note]
        else:
            notes = [c.tap_note, c.hold_note, c.slide_note, c.touch_note, c.break_note]
        dct['charts'].append({
            'notes': notes, "charter": c.charter
        })
    data.append(dct)
    return data


cs_need_update = True
cs_cache = {}
md_cache = music_data()
app = Quart(__name__)

with open('config.json', encoding='utf-8') as fr:
    config = json.load(fr)
    db_url = config["database_url"]
    jwt_secret = config["jwt_secret"]


@app.after_request
def cors(environ):
    environ.headers['Access-Control-Allow-Origin'] = '*'
    environ.headers['Access-Control-Allow-Method'] = '*'
    environ.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
    return environ


@app.route("/feedback", methods=['POST'])
async def feedback():
    j = await request.get_json()
    FeedBack.insert(j).execute()
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
        g.user = Player.get(Player.username == g.username)
        return await f(*args, **kwargs)

    return func


@app.route("/login", methods=['POST'])
async def login():
    j = await request.get_json()
    username = j["username"]
    password = j["password"]
    try:
        user: Player = Player.get(Player.username == username)
        if md5(password + user.salt) == user.password:
            resp = await make_response({"message": "登录成功"})
            resp.set_cookie('jwt_token', username_encode(username), max_age=30 * 86400)
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
    player = Player.select().where(Player.username == j["username"])
    if player.exists():
        return {
                   "errcode": -1,
                   "message": "此用户名已存在",
               }, 400
    salt = ''.join(random.sample(string.ascii_letters + string.digits, 16))
    Player.create(username=j["username"], salt=salt, password=md5(j["password"] + salt))
    resp = await make_response({"message": "注册成功"})
    resp.set_cookie('jwt_token', username_encode(j["username"]))
    return resp


@app.route("/player/profile", methods=['GET', 'POST'])
@login_required
async def profile():
    if request.method == 'GET':
        u: Player = g.user
        return {
            "username": u.username,
            "nickname": u.nickname,
            "additional_rating": u.additional_rating,
            "bind_qq": u.bind_qq,
            "privacy": u.privacy
        }
    else:
        try:
            obj = await request.json
            for key in obj:
                g.user.__setattr__(key, obj[key])
            g.user.save()
            u: Player = g.user
            return {
                "username": u.username,
                "nickname": u.nickname,
                "additional_rating": u.additional_rating,
                "bind_qq": u.bind_qq,
                "privacy": u.privacy
            }
        except Exception:
            return {
                "message": "error"
            }, 400


@app.route("/player/change_password", methods=['POST'])
@login_required
async def change_password():
    password = (await request.json)["password"]
    if len(password) >= 30:
        return {"message": "密码不能大于30位"}, 400
    g.user.password = md5(password + g.user.salt)
    return {"message": "success"}


@app.route("/music_data", methods=['GET'])
async def get_music_data():
    resp = await make_response(json.dumps(md_cache))
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp


@app.route("/player/records", methods=['GET'])
@login_required
async def get_records():
    r = Record.select().where(Record.player == g.user.id)
    records = []
    for record in r:
        records.append(record.json(md=md_cache))
    resp = await make_response(
        '{"records":' + json.dumps(records, ensure_ascii=False) + ', "username": "' + g.username + '", "additional_rating": ' + str(g.user.additional_rating) + '}')
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp


@app.route("/query/player", methods=['POST'])
async def query_player():
    obj = await request.json
    try:
        if "qq" in obj:
            p: Player = Player.get(Player.bind_qq == obj["qq"])
        else:
            username = obj["username"]
            p: Player = Player.get(Player.username == username)
    except Exception:
        return {
            "message": "user not exists"
        }, 400
    if p.privacy and "username" in obj:
        try:
            token = decode(request.cookies['jwt_token'])
        except KeyError:
            return {"status": "error", "msg": "已设置隐私"}, 403
        if token == {}:
            return {"status": "error", "msg": "已设置隐私"}, 403
        if token['exp'] < ts():
            return {"status": "error", "msg": "会话过期"}, 403
        if token['username'] != obj["username"]:
            return {"status": "error", "msg": "已设置隐私"}, 403
    sd: List = Record.select().where((Record.player == p.id) & (Record.type == "SD")).order_by(Record.ra.desc()).limit(
        25)
    dx: List = Record.select().where((Record.player == p.id) & (Record.type == "DX")).order_by(Record.ra.desc()).limit(
        15)
    nickname = p.nickname
    if nickname == "":
        nickname = p.username if len(p.username) <= 8 else p.username[:8] + '…'
    return {
        "username": p.username,
        "rating": p.rating,
        "additional_rating": p.additional_rating,
        "nickname": nickname,
        "charts": {
            "sd": [c.json(md=md_cache) for c in sd],
            "dx": [c.json(md=md_cache) for c in dx]
        }
    }


def update_one(records, record):
    for i in range(len(records)):
        r = records[i]
        if r['level_index'] == record['level_index'] and r['title'] == record['title'] and r['type'] == record['type']:
            records[i] = record
            return
    records.append(record)


async def compute_ra(player: Player):
    rating = 0
    sd = Record.select().where((Record.player == player.id) & (Record.type == "SD")).order_by(Record.ra.desc()).limit(
        25)
    dx = Record.select().where((Record.player == player.id) & (Record.type == "DX")).order_by(Record.ra.desc()).limit(
        15)
    for t in sd:
        rating += t.ra
    for t in dx:
        rating += t.ra
    player.rating = rating
    player.save()
    return rating


@app.route("/player/update_records", methods=['POST'])
@login_required
async def update_records():
    global cs_need_update
    cs_need_update = True
    r = Record.select().where(Record.player == g.user.id)
    records = []
    for record in r:
        records.append(record.json(md=md_cache))
    j = await request.get_json()
    for new in j:
        if "rank" in new:
            del new["rank"]
        if "tag" in new:
            del new["tag"]
        update_one(records, new)
    for r in records:
        r["player"] = g.user
    Record.delete().where(Record.player == g.user.id).execute()
    Record.insert_many(records).execute()
    await compute_ra(g.user)
    return {
        "message": "更新成功",
    }


@app.route("/player/update_record", methods=['POST'])
@login_required
async def update_record():
    global cs_need_update
    cs_need_update = True
    record = await request.get_json()
    r: Record = Record.get((Record.player == g.user.id) & (Record.level_index == record["level_index"]) &
                           (Record.title == record["title"]) & (Record.type == record["type"]))
    r.achievements = record['achievements']
    r.ra = record['ra']
    r.fc = record['fc']
    r.fs = record['fs']
    r.rate = record['rate']
    r.save()
    await compute_ra(g.user)
    return {
        "message": "更新成功",
    }


@app.route("/rating_ranking", methods=['GET'])
async def rating_ranking():
    players = Player.select()
    data = []
    for player in players:
        data.append({"username": player.username, "ra": player.rating})
    resp = await make_response(json.dumps(data, ensure_ascii=False))
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp


@app.route("/count_view", methods=['GET'])
async def count_view():
    v: Views = Views.get()
    v.prober += 1
    v.save()
    return {"views": v.prober}


async def message_resp():
    today_ts = int((time.time() + 8 * 3600) / 86400) * 86400 - 8 * 3600
    results = Message.select(Message, Player).join(Player).where(Message.ts >= today_ts)
    l = []
    for r in results:
        l.append({"text": r.text, "username": r.player.username, "ts": r.ts, "nickname": r.nickname})
    resp = await make_response(json.dumps(l, ensure_ascii=False))
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp


@app.route("/message", methods=['GET'])
async def message_g():
    return await message_resp()


@app.route("/message", methods=['POST'])
@login_required
async def message():
    if request.method == 'POST':
        a = Message()
        a.player = g.user
        j = await request.get_json()
        a.text = j["text"]
        a.nickname = j["nickname"]
        a.ts = int(time.time())
        a.save(force_insert=True)
    return await message_resp()


@app.route("/chart_stats", methods=['GET'])
async def chart_stats():
    global cs_need_update
    global cs_cache
    if not cs_need_update:
        resp = await make_response(json.dumps(cs_cache, ensure_ascii=False))
        resp.headers['content-type'] = "application/json; charset=utf-8"
        return resp
    cursor = Record.raw(
        'select record.title, record.type, record.level_index, count(*) as cnt, avg(achievements) as `avg`, sum(case'
        ' when achievements > 100.5 then 1 else 0 end) as sssp_count from record group by title, `type`, level_index')
    data = defaultdict(lambda: [{}, {}, {}, {}, {}])
    for elem in cursor:
        data[elem.title + elem.type][elem.level_index] = {"count": elem.cnt,
                                                          "avg": elem.avg,
                                                          "sssp_count": int(elem.sssp_count)
                                                          }
    level_dict = defaultdict(lambda: [])
    md = md_cache
    for elem in md:
        key = elem['title'] + elem['type']
        for i in range(len(elem['ds'])):
            elem2 = {
                "key": key,
                "level_index": i,
                "count": 1,
                "avg": 0,
                "sssp_count": 0
            }
            for _k in data[key][i]:
                elem2[_k] = data[key][i][_k]
            if elem2['count'] >= 30:
                level_dict[elem['level'][i]].append(elem2)
    for level in level_dict:
        level_dict[level].sort(key=lambda x: x['sssp_count'] / x['count'], reverse=True)
        ln = len(level_dict[level])
        for i in range(ln):
            elem = level_dict[level][i]
            rate = ((i + 0.5) / ln)
            if elem['count'] < 30:
                continue
            if rate <= 0.1:
                elem['tag'] = 'Very Easy'
            elif rate <= 0.3:
                elem['tag'] = 'Easy'
            elif rate < 0.7:
                elem['tag'] = 'Medium'
            elif rate < 0.9:
                elem['tag'] = 'Hard'
            else:
                elem['tag'] = 'Very Hard'
            elem['v'] = i
            elem['t'] = ln
            level_index = elem['level_index']
            key = elem['key']
            del elem['key']
            del elem['level_index']
            data[key][level_index] = elem
    cs_cache = data
    cs_need_update = False
    resp = await make_response(json.dumps(data, ensure_ascii=False))
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp


app.run(host='0.0.0.0', port=8333, loop=asyncio.get_event_loop())
