"""
Author: Diving-Fish

这个文件的目录均为 /chuni/* 的目录，目录会被反向代理映射到
https://www.diving-fish.com/api/chunithmprober/*
例如 /chuni/* 可以通过 https://www.diving-fish.com/api/chunithmprober/* 访问。
"""
import asyncio
import time
from audioop import reverse
from collections import defaultdict
from math import floor
from app import app, developer_required, login_required, login_or_token_required, oauth_or_login_required, md5
from quart import Quart, request, g, make_response
from models.maimai import NewRecord
from tools._jwt import *
from models.chunithm import *
import tools.page_parser as page_parser
import tools.record_filter as record_filter

md_cache = chuni_music_data()
md_cache_eTag = md5(json.dumps(md_cache))
md_map = {}
md_title_map = {}
md_title_we_map = {}
chart_id_map = {}
for music in md_cache:
    md_map[music['id']] = music
    if music['id'] >= 8000:
        md_title_we_map[music['title']] = music
    else:
        md_title_map[music['title']] = music
    for i, cid in enumerate(music['cids']):
        chart_id_map[cid] = (i, music)

latest_version = ('CHUNITHM LUMINOUS PLUS', 'CHUNITHM VERSE')

@app.route("/chuni/music_data")
async def get_music_data_chuni():
    """
    获取所有乐曲的数据。
    """

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
@oauth_or_login_required("chunithm.records.write")
async def update_records_chuni():
    """
    *需要登录
    通过 html 格式的数据更新您的中二查分器数据。
    """

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
    #print(j)
    if recent == 0:       
        for record in j:
            title = record['title']
            if record["level"] < 5:
                if title not in md_title_map:
                    continue
                m = md_title_map[title]
            else:
                if title not in md_title_we_map:
                    continue
                m = md_title_we_map[title]
            try:
                cid = m["cids"][record["level"]]
                dicts[cid] = {
                    "chart": cid, "player": g.user.id, "fc": record["fc"],
                    "score": min(1010000, record["score"]), "recent": False
                }
            except IndexError:
                print(m, record["level"])
        rs = await ChuniRecord.raw(
            'select * from chunirecord where player_id = %s', g.user.id).aio_execute()
        updates = []
        for r in rs:
            if r.chart_id in dicts and not r.recent:
                r.score = dicts[r.chart_id]["score"]
                r.fc = dicts[r.chart_id]["fc"]
                updates.append(r)
                del dicts[r.chart_id]
        #print(dicts)
        #print(updates)
        creates = list(dicts.values())
        if len(creates) > 0:
            await ChuniRecord.insert_many(creates).aio_execute()
        if len(updates) > 0:
            await ChuniRecord.aio_bulk_update(updates, fields=[
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
        await ChuniRecord.delete().where((ChuniRecord.player == g.user.id) & (ChuniRecord.recent == 1)).aio_execute()
        await ChuniRecord.insert_many(arr).aio_execute()
        updates = []
        creates = arr
    
    await compute_ra(g.user)
    return {
        "message": "更新成功",
        "updates": len(updates),
        "creates": len(creates)
    }

def resolve_chuni_chart(record: Dict):
    """把一条上传记录解析到具体谱面，返回 chart id，解析不了返回 None。

    优先信 cid：它唯一确定一个谱面。其次是 mid / title 加 level_index——
    世界末日谱的曲目单独一套 id，且部分只有一个谱面（cids 只有一项），
    这时 level_index 会越界，落到最后一个谱面上，那就是它的 WE 谱。
    """
    cid = record.get("cid")
    if isinstance(cid, int) and cid in chart_id_map:
        return cid

    level = record.get("level_index")
    if not isinstance(level, int) or level < 0:
        return None

    m = None
    mid = record.get("mid", record.get("music_id", record.get("id")))
    if isinstance(mid, int) and mid in md_map:
        m = md_map[mid]
    else:
        title = record.get("title")
        if not isinstance(title, str):
            return None
        if level < 5:
            m = md_title_map.get(title)
        else:
            m = md_title_we_map.get(title)
    if m is None:
        return None

    cids = m["cids"]
    if level < len(cids):
        return cids[level]
    if m["id"] >= 8000 and cids:
        return cids[-1]
    return None


@app.route("/chuni/player/update_records", methods=['POST'])
@oauth_or_login_required("chunithm.records.write")
async def update_records_chuni_json():
    """
    *需要登录
    更新您的中二查分器数据。

    请求体为 JSON List，格式可以参考 `/chuni/player/records` 接口返回的数据，
    也可以直接把该接口的整个返回体发回来（会取其中的 `records.best`）。

    每条记录用 `cid` 定位谱面最稳妥；没有 `cid` 时用 `mid` 或 `title`
    搭配 `level_index`。`score` 必填，`fc` 可选。

    带 `?recent=1` 时写入的是 recent 成绩，语义与 `/chuni/player/update_records_html`
    的同名参数一致：先清空原有 recent 记录再整体写入。
    """
    recent = 1 if request.args.get("recent", type=int, default=0) != 0 else 0

    j = await request.get_json()
    if isinstance(j, dict):
        # 允许直接把 /chuni/player/records 的返回体发回来
        inner = j.get("records")
        if isinstance(inner, dict):
            inner = inner.get("best")
        j = inner if inner is not None else j.get("best")
    if not isinstance(j, list):
        return {"message": "导入数据格式有误"}, 400
    if len(j) == 0:
        return {"message": "更新成功", "updates": 0, "creates": 0}

    dicts = {}
    for record in j:
        if not isinstance(record, dict):
            continue
        cid = resolve_chuni_chart(record)
        if cid is None:
            continue
        score = record.get("score")
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            continue
        dicts[cid] = {
            "chart": cid, "player": g.user.id, "fc": std_chuni_fc(record.get("fc", "")),
            "score": min(MAX_CHUNI_SCORE, max(0, int(score))), "recent": bool(recent)
        }

    if recent:
        creates = list(dicts.values())
        updates = []
        await ChuniRecord.delete().where(
            (ChuniRecord.player == g.user.id) & (ChuniRecord.recent == 1)).aio_execute()
        if len(creates) > 0:
            await ChuniRecord.insert_many(creates).aio_execute()
    else:
        rs = await ChuniRecord.raw(
            'select * from chunirecord where player_id = %s', g.user.id).aio_execute()
        updates = []
        for r in rs:
            if r.chart_id in dicts and not r.recent:
                r.score = dicts[r.chart_id]["score"]
                r.fc = dicts[r.chart_id]["fc"]
                updates.append(r)
                del dicts[r.chart_id]
        creates = list(dicts.values())
        if len(creates) > 0:
            await ChuniRecord.insert_many(creates).aio_execute()
        if len(updates) > 0:
            await ChuniRecord.aio_bulk_update(updates, fields=[
                ChuniRecord.fc, ChuniRecord.score
            ])

    await compute_ra(g.user)
    return {
        "message": "更新成功",
        "updates": len(updates),
        "creates": len(creates)
    }


@app.route("/chuni/player/delete_records", methods=['DELETE'])
@oauth_or_login_required("chunithm.records.write")
async def delete_records_chuni():
    """
    *需要登录
    删除您的中二查分器数据。
    """
    nums = await ChuniRecord.delete().where(ChuniRecord.player == g.user.id).aio_execute()
    await compute_ra(g.user)
    return {
        "message": nums
    }

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


async def get_b50(player: Player):
    old30 = []
    new20 = []
    rs = await ChuniRecord.raw('select * from chunirecord where player_id = %s and recent = 0', player.id).aio_execute()
    for r in rs:
        setattr(r, 'ra', single_ra(r))
        if chart_id_map[r.chart_id][1]['basic_info']['from'] in latest_version:
            new20.append(r)
        else:
            old30.append(r)
    old30.sort(key=lambda x: x.ra, reverse=True)
    new20.sort(key=lambda x: x.ra, reverse=True)
    return old30[:30], new20[:20]


async def compute_ra(player: Player):
    old30, new20 = await get_b50(player)
    total = 0.0
    for record in new20:
        total += single_ra(record)
    player.chuni_new_rating = total / 50
    for record in old30:
        total += single_ra(record)
    rating = total / 50
    player.chuni_rating = rating
    player.access_time = time.time()
    await player.aio_save()
    return rating


# /chuni/player/records 支持的过滤字段，语法见 tools/record_filter.py
RECORD_FILTER_SPEC = {
    "title": record_filter.STR,
    "artist": record_filter.STR,
    "genre": record_filter.STR,
    "charter": record_filter.STR,
    "version": record_filter.STR,
    "level": record_filter.STR,
    "level_label": record_filter.STR,
    "fc": record_filter.STR,
    "song_id": record_filter.NUM,
    "cid": record_filter.NUM,
    "level_index": record_filter.NUM,
    "ds": record_filter.NUM,
    "bpm": record_filter.NUM,
    "combo": record_filter.NUM,
    "score": record_filter.NUM,
    "ra": record_filter.NUM,
}

RECORD_FILTER_ALIASES = {
    "id": "song_id",
    "mid": "song_id",
    "music_id": "song_id",
    "difficulty": "level_index",
}


def record_filter_view(record: ChuniRecord, elem: Dict) -> Dict:
    """一条成绩可供过滤的字段视图：record_json 的输出，加上曲目/谱面元数据。"""
    level, music = chart_id_map[record.chart_id]
    info = music["basic_info"]
    chart = music["charts"][level] if level < len(music["charts"]) else {}
    view = dict(elem)
    view["song_id"] = elem["mid"]
    view["artist"] = info.get("artist")
    view["genre"] = info.get("genre")
    view["bpm"] = info.get("bpm")
    view["version"] = info.get("from")
    view["charter"] = chart.get("charter")
    view["combo"] = chart.get("combo")
    return view


@app.route("/chuni/latest_version")
async def _latest_version():
    return {"version": list(latest_version)}
    

@app.route("/chuni/player/records")
@oauth_or_login_required("chunithm.records.read")
async def player_records_chuni():
    """
    *需要登录
    获取用户的成绩数据，以 JSON 格式返回。

    可以用查询参数在服务端过滤，不带任何参数时行为与过去一致（返回全部成绩）。

    - 数值字段（`song_id` `cid` `level_index` `ds` `bpm` `combo` `score` `ra`）
      支持严格相等与区间：`ds=14`、`ds=13..14`、`ds=14..`、`ds=..13.9`，
      逗号分隔可以并列多个条件，如 `ds=13..13.9,14.5`。
    - 字符串字段（`title` `artist` `genre` `charter` `version` `level`
      `level_label` `fc`）完全匹配且忽略大小写，多值用逗号或重复参数，
      如 `fc=fullcombo,alljustice`。值本身含逗号时请用重复参数。

    不同字段之间取交集，同一字段的多个值取并集。认不出的查询参数会被忽略，
    实际生效的条件在返回体的 `filters` 里回显。
    """
    try:
        matchers, echo = record_filter.build(
            request.args, RECORD_FILTER_SPEC, RECORD_FILTER_ALIASES)
    except record_filter.FilterError as e:
        return {"message": str(e)}, 400

    rs = await ChuniRecord.raw('select * from chunirecord where player_id = %s and recent = 0', g.user.id).aio_execute()
    await compute_ra(g.user)
    best = []
    for c in rs:
        elem = record_json(c)
        if matchers and not record_filter.match(record_filter_view(c, elem), matchers):
            continue
        best.append(elem)
    resp = {
        "records": {
            "best": best,
            "r10": [],
        },
        "username": g.username,
        "nickname": g.user.nickname,
        "rating": g.user.chuni_rating
    }
    if echo:
        resp["filters"] = echo
    return resp


@app.route("/chuni/player/test_data")
async def player_records_chunitest():
    """
    获取测试用户的成绩数据，调试前端时使用。
    """

    p = await Player.aio_get(Player.id == 636)
    rs = await ChuniRecord.raw('select * from chunirecord where player_id = 636 and recent = 0').aio_execute()
    # await compute_ra(p)
    return {
        "records": {
            "best": [record_json(c) for c in rs],
            "r10": [],
        },
        "username": p.username,
        "rating": p.chuni_rating
    }


@app.route("/chuni/query/player", methods=['POST'])
async def query_player_chuni():
    """
    通过 QQ 或用户名查询用户的成绩数据，仅返回 b30 + r10 部分。
    请求体为 JSON 格式，参数需包含 `qq` 或 `username` 中的一项。
    """
    obj = await request.json
    try:
        if "qq" in obj:
            p: Player = await Player.by_qq(obj["qq"])
        else:
            username = obj["username"]
            p: Player = await Player.aio_get(Player.username == username)
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
    old30, new20 = await get_b50(p)
    asyncio.create_task(compute_ra(p))
    nickname = p.nickname
    if nickname == "":
        nickname = p.username if len(p.username) <= 8 else p.username[:8] + '…'
    return {
        "username": p.username,
        "rating": p.chuni_rating,
        "nickname": nickname,
        "records": {
            "b30": [record_json(c) for c in old30],
            "n20": [record_json(c) for c in new20],
            "r10": []
        }
    }


@app.route('/chuni/dev/player/records', methods=['GET'])
@developer_required
async def dev_get_records_chuni():
    """
    *需要开发者
    获取某个用户的成绩信息。
    请求体为 JSON，参数需包含 `username` 或 `qq`。
    """
    username = request.args.get("username", type=str, default="")
    qq = request.args.get("qq", type=str, default="")
    if username == "" and qq == "":
        return {"message": "no such user"}, 400
    try:
        if qq == "":
            player: Player = await Player.aio_get(Player.username == username)
        else:
            player: Player = await Player.by_qq(qq)
    except Exception:
        return {"message": "no such user"}, 400
    if player.privacy or not player.accept_agreement:
        return {"status": "error", "message": "已设置隐私或未同意用户协议"}, 403
    rs = await ChuniRecord.raw('select * from chunirecord where player_id = %s and recent = 0', player.id).aio_execute()
    await compute_ra(player)
    return {
        "records": {
            "best": [record_json(c) for c in rs],
            "r10": [],
        },
        "username": player.username,
        "nickname": player.nickname,
        "rating": player.chuni_rating
    }
