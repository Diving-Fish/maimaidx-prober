import asyncio
from audioop import reverse
from collections import defaultdict
from math import floor
from app import app, developer_required, login_required, md5
from quart import Quart, request, g, make_response
from models.maimai import NewRecord
from tools._jwt import *
from models.chunithm import *
import tools.page_parser as page_parser

md_cache = chuni_music_data()
md_cache_eTag = md5(json.dumps(md_cache))
md_map = {}
md_title_map = {}
chart_id_map = {}
for music in md_cache:
    md_map[music['id']] = music
    md_title_map[music['title']] = music
    for i, cid in enumerate(music['cids']):
        chart_id_map[cid] = (i, music)

@app.route("/chuni/music_data")
async def get_music_data_chuni():
    if request.headers.get('If-None-Match') == '"' + md_cache_eTag + '"':
        resp = await make_response("", 304)
        resp.headers['cache-control'] = "private, max_age=86400"
        return resp
    resp = await make_response(json.dumps(md_cache))
    resp.headers['ETag'] = '"' + md_cache_eTag + '"';
    resp.headers['content-type'] = "application/json; charset=utf-8"
    resp.headers['cache-control'] = "private, max_age=86400"
    return resp


@app.route("/chuni/player/update_records_html", methods=['POST'])
@login_required
async def update_records_chuni():
    recent = request.args.get("recent", type=int, default=0)
    if recent != 0:
        recent = 1
    raw_data = await request.get_data()
    # with open(f"{time.time_ns()}.html", 'w') as fw:
    #     fw.write(str(raw_data, encoding="utf-8"))
    dicts = {}
    try:
        if recent == 1:
            j = page_parser.chunithm_recent2json(str(raw_data, encoding="utf-8"))
        else:
            j = page_parser.chunithm_genre2json(str(raw_data, encoding="utf-8"))
    except Exception as e:
        return {
                "message": str(e)
            }, 400
    if recent == 0:       
        for record in j:
            title = record['title']
            if title not in md_title_map:
                continue
            m = md_title_map[title]
            cid = m["cids"][record["level"]]
            dicts[cid] = {
                "chart": cid, "player": g.user.id, "fc": record["fc"],
                "score": min(1010000, record["score"]), "recent": False
            }
        rs = ChuniRecord.raw(
            'select * from chunirecord where player_id = %s', g.user.id)
        updates = []
        for r in rs:
            if r.chart_id in dicts and not r.recent:
                r.score = dicts[r.chart_id]["score"]
                r.fc = dicts[r.chart_id]["fc"]
                updates.append(r)
                del dicts[r.chart_id]
        if len(dicts) > 0:
            ChuniRecord.insert_many(dicts.values()).execute()
        if len(updates) > 0:
            ChuniRecord.bulk_update(updates, fields=[
                ChuniRecord.fc, ChuniRecord.score
            ])
    elif recent == 1:
        arr = []
        for record in j:
            title = record['title']
            if title not in md_title_map:
                continue
            m = md_title_map[title]
            arr.append({
                "chart": m["cids"][record["level"]],
                "player": g.user.id,
                "fc": record["fc"],
                "score": min(1010000, record["score"]),
                "recent": True
            })
        ChuniRecord.delete().where((ChuniRecord.player == g.user.id) & (ChuniRecord.recent == 1)).execute()
        ChuniRecord.insert_many(arr).execute()
    return {"message": "更新成功"}


def lerp(x1, x2, y1, y2, x):
    val = (x - x1) / (x2 - x1) * (y2 - y1) + y1
    val = floor(val * 100) / 100
    return val


def single_ra(record: ChuniRecord):
    score = record.score
    level, music = chart_id_map[record.chart_id]
    ds = music['ds'][level]
    if score < 500000:
        return 0.0
    elif score < 800000:
        return max(0, lerp(500000, 800000, 0, (ds - 5) / 2, score))
    elif score < 900000:
        return max(0, lerp(800000, 900000, (ds - 5) / 2, ds - 5, score))
    elif score < 925000:
        return max(0, lerp(900000, 925000, ds - 5, ds - 3, score))
    elif score < 975000:
        return max(0, lerp(925000, 975000, ds - 3, ds, score))
    elif score < 1000000:
        return lerp(975000, 1000000, ds, ds + 1, score)
    elif score < 1005000:
        return lerp(1000000, 1005000, ds + 1, ds + 1.5, score)
    elif score < 1007500:
        return lerp(1005000, 1007500, ds + 1.5, ds + 2, score)
    elif score < 1009000:
        return lerp(1007500, 1009000, ds + 2, ds + 2.15, score)
    else:
        return ds + 2.15


def record_json(record: ChuniRecord):
    level, music = chart_id_map[record.chart_id]
    return {
        "mid": music["id"],
        "cid": music["cids"][level],
        "title": music["title"],
        "level_index": level,
        "level_label": ["Basic", "Advanced", "Expert", "Master", "Ultima", "World's End"][level],
        "level": music["level"][level],
        "score": record.score,
        "fc": record.fc,
        "ra": single_ra(record),
        "ds": music["ds"][level]
    }


def get_b30_and_r10(player: Player):
    b30 = []
    r10 = []
    rs = ChuniRecord.raw('select * from chunirecord where player_id = %s and recent = 0', player.id)
    for r in rs:
        setattr(r, 'ra', single_ra(r))
        b30.append(r)
    b30.sort(key=lambda x: x.ra, reverse=True)
    rs2 = ChuniRecord.raw('select * from chunirecord where player_id = %s and recent = 1', player.id)
    for r in rs2:
        r10.append(r)
    return b30[:30], r10


async def compute_ra(player: Player):
    b30, r10 = get_b30_and_r10(player)
    total = 0.0
    for record in b30:
        total += single_ra(record)
    for record in r10:
        total += single_ra(record)
    player.chuni_rating = total / 40
    player.save()
    

@app.route("/chuni/player/records")
@login_required
async def player_records_chuni():
    rs = ChuniRecord.raw('select * from chunirecord where player_id = %s and recent = 0', g.user.id)
    rs2 = ChuniRecord.raw('select * from chunirecord where player_id = %s and recent = 1', g.user.id)
    await compute_ra(g.user)
    return {
        "records": {
            "best": [record_json(c) for c in rs],
            "r10": [record_json(c) for c in rs2],
        },
        "username": g.username,
        "rating": g.user.chuni_rating
    }


@app.route("/chuni/player/test_data")
async def player_records_chunitest():
    p = Player.get_by_id(636)
    rs = ChuniRecord.raw('select * from chunirecord where player_id = 636 and recent = 0')
    rs2 = ChuniRecord.raw('select * from chunirecord where player_id = 636 and recent = 1')
    await compute_ra(p)
    return {
        "records": {
            "best": [record_json(c) for c in rs],
            "r10": [record_json(c) for c in rs2],
        },
        "username": p.username,
        "rating": p.chuni_rating
    }


@app.route("/chuni/query/player", methods=['POST'])
async def query_player_chuni():
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
            return {"status": "error", "message": "已设置隐私"}, 403
        if token == {}:
            return {"status": "error", "message": "已设置隐私"}, 403
        if token['exp'] < ts():
            return {"status": "error", "message": "会话过期"}, 403
        if token['username'] != obj["username"]:
            return {"status": "error", "message": "已设置隐私"}, 403
    b30, r10 = get_b30_and_r10(p)
    asyncio.create_task(compute_ra(p))
    nickname = p.nickname
    if nickname == "":
        nickname = p.username if len(p.username) <= 8 else p.username[:8] + '…'
    return {
        "username": p.username,
        "rating": p.chuni_rating,
        "nickname": nickname,
        "records": {
            "b30": [record_json(c) for c in b30],
            "r10": [record_json(c) for c in r10]
        }
    }