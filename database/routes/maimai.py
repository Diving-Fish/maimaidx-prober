"""
Author: Diving-Fish

这个文件的目录会被反向代理映射到
https://www.diving-fish.com/api/maimaidxprober/*
例如 /player/profile 可以通过 https://www.diving-fish.com/api/maimaidxprober/player/profile 访问。
"""
import asyncio
import time
from collections import defaultdict
from app import app, developer_required, login_required, login_or_token_required, md5, is_developer, chart_stat_updated
from quart import Quart, request, g, make_response
from tools._jwt import *
from models.maimai import *
import tools.page_parser as page_parser
import tools.maimai_analysis_curve as maimai_analysis
from tools.analysis_template import return_template
import random
from access.redis import redis
from tools.maidle import Maidle, maidle_data as maidle_cache, songs_id_map as maidle_map


cs_cache = {}
cs_cache_eTag = md5(json.dumps(cs_cache, ensure_ascii=False))
md_cache = music_data()
md_cache_eTag = md5(json.dumps(md_cache))
md_map = {}
md_title_type_map = {}
for music in md_cache:
    md_map[music['id']] = music
    md_title_type_map[(music["title"], music["type"])] = music

maidle_cache_eTag = md5(json.dumps(maidle_cache, ensure_ascii=False))

def get_ds(r: Dict):
    t = (r["title"], r["type"])
    if t in md_title_type_map:
        return md_title_type_map[t]["ds"][r["level_index"]]
    return 0


page_parser.get_ds = get_ds


def is_new(r: Dict):
    t = (r["title"], r["type"])
    if t in md_title_type_map:
        return md_title_type_map[t]["is_new"]
    return False


@app.route("/player/agreement", methods=['GET', 'POST'])
@login_required
async def agreement():
    """
    *需要登录
    获取用户是否同意过用户协议
    """
    if request.method == 'GET':
        u: Player = g.user
        return {"accept_agreement": u.accept_agreement}
    else:
        obj = await request.json
        if "accept_agreement" in obj:
            g.user.accept_agreement = obj["accept_agreement"]
            await g.user.aio_save()
        return {"message": "success"}


@app.route("/player/profile", methods=['GET', 'POST'])
@login_required
async def profile():
    """
    *需要登录
    更新或获取您的用户资料，取决于请求是 POST 还是 GET。
    """
    if request.method == 'GET':
        u: Player = g.user
        return u.user_json()
    else:
        try:
            obj = await request.json
            # handle plate there.
            if "plate" in obj:
                d = obj["plate"]
                version = d["version"]
                plate_type = d["plate_type"]
                verified, plate_label = verify_plate(g.user, version, plate_type)
                if verified:
                    g.user.__setattr__("plate", plate_label)
                del obj["plate"]

            if "bind_qq" in obj:
                # check duplicate
                bind_qq = obj["bind_qq"]
                if bind_qq != "":
                    try:
                        player = await Player.aio_get((Player.bind_qq == bind_qq) & (Player.id != g.user.id))
                        # Not found -> except
                        return {
                        "message": f"此 QQ 号已经被用户名为{player.username}的用户绑定，请先解绑再进行操作~"
                        }, 400
                    except Exception:
                        pass

            if "qq_channel_uid" in obj:
                # check duplicate
                qq_channel_uid = obj["qq_channel_uid"]
                if qq_channel_uid != "":
                    try:
                        player = await Player.aio_get((Player.qq_channel_uid == qq_channel_uid) & (Player.id != g.user.id))
                        # Not found -> except
                        return {
                        "message": f"此频道 ID 已经被用户名为{player.username}的用户绑定，请先解绑再进行操作~"
                        }, 400
                    except Exception:
                        pass

            for key in obj:
                if key in ("nickname", "bind_qq", "additional_rating", "privacy", "qq_channel_uid", "accept_agreement", "mask"):
                    g.user.__setattr__(key, obj[key])
                if key == "user_general_data":
                    g.user.__setattr__(key, json.dumps(obj[key]))
            await g.user.aio_save()
            u: Player = g.user
            return u.user_json()

        except Exception as e:
            # print(e)
            return {
                "message": "error"
            }, 400


@app.route("/player/import_token", methods=['PUT'])
@login_required
async def import_token():
    """
    *需要登录
    生成一个新的导入 Token，并覆盖旧 Token。
    """
    return {
        "token": await g.user.generate_import_token()
    }


@app.route("/music_data", methods=['GET'])
async def get_music_data():
    """
    获取 maimai 的歌曲数据。
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


@app.route("/player/records", methods=['GET'])
@login_or_token_required
async def get_records():
    """
    *需要登录
    获取用户的成绩信息。
    """
    r = await NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', g.user.id).aio_execute()
    await compute_ra(g.user)
    records = []
    for record in r:
        elem = record_json(record, False)
        records.append(elem)
    return {
        "username": g.username,
        "rating": g.user.rating,
        "additional_rating": g.user.additional_rating,
        "nickname": g.user.nickname,
        "plate": g.user.plate,
        "records": records
    }


@app.route("/player/test_data", methods=['GET'])
async def get_records_test():
    r = await NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', '636').aio_execute()
    user = await Player.aio_get(Player.id == 636)
    await compute_ra(user)
    records = []
    for record in r:
        elem = record_json(record, False)
        records.append(elem)
    return {
        "username": "DivingFish",
        "rating": user.rating,
        "additional_rating": user.additional_rating,
        "nickname": user.nickname,
        "plate": user.plate,
        "records": records
    }


@app.route("/dev/player/records", methods=['GET'])
@developer_required
async def dev_get_records():
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
    r = await NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id).aio_execute()
    await compute_ra(player)
    records = []
    for record in r:
        elem = record_json(record, player.mask)
        records.append(elem)
    return {
        "username": player.username,
        "rating": player.rating,
        "additional_rating": player.additional_rating,
        "nickname": player.nickname,
        "plate": player.plate,
        "records": records
    }

@app.route("/dev/player/record", methods=['POST'])
@developer_required
async def dev_get_record():
    """
    *需要开发者
    获取某个用户的单曲成绩信息。
    请求体为 JSON，参数需包含 `username` 或 `qq` 和 `music_id` (可以为单个值或列表）。
    """
    obj = await request.json
    try:
        if "qq" in obj:
            p: Player = await Player.by_qq(obj["qq"])
        else:
            username = obj["username"]
            p: Player = await Player.aio_get(Player.username == username)
    except Exception:
        return {"message": "no such user"}, 400
        
    if p.privacy or not p.accept_agreement:
        return {"status": "error", "message": "已设置隐私或未同意用户协议"}, 403
    music_ids = []
    if isinstance(obj['music_id'], str):
        music_ids.append(obj['music_id'])
    else:
        try:
            for elem in obj['music_id']:
                music_ids.append(str(elem))
        except Exception:
            pass

    music_ids = list(filter(lambda elem: elem in md_map, music_ids))

    query_str = f'({",".join(["%s"] * len(music_ids))})'
    
    r = await NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and music.id in ' + query_str + ' and chart_id = chart.id and chart.music_id = music.id', p.id, *music_ids).aio_execute()
    records = defaultdict(lambda: [])
    for record in r:
        elem = record_json(record, p.mask)
        records[record.id].append(elem)
    return records


async def get_dx_and_sd(player):
    l = await NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id).aio_execute()
    l1 = []
    l2 = []
    for r in l:
        setattr(r, 'ra', ScoreCoefficient(r.achievements).ra(r.ds))
        if r.is_new:
            l2.append(r)
        else:
            l1.append(r)
    l1.sort(key=lambda x: (x.ra, x.ds, x.achievements), reverse=True)
    l2.sort(key=lambda x: (x.ra, x.ds, x.achievements), reverse=True)
    return l1[:25], l2[:15]


async def get_dx_and_sd_for50(player):
    l = await NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id and chart.music_id < 100000', player.id).aio_execute()
    l1 = []
    l2 = []
    for r in l:
        setattr(r, 'ra', ScoreCoefficient(r.achievements).ra(r.ds))
        if r.is_new:
            l2.append(r)
        else:
            l1.append(r)
    l1.sort(key=lambda x: (x.ra, x.ds, x.achievements), reverse=True)
    l2.sort(key=lambda x: (x.ra, x.ds, x.achievements), reverse=True)
    return l1[:35], l2[:15]


async def getplatelist(player, version: List[Dict]):
    l = await NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.version as `version`, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id).aio_execute()
    fl = recordList()
    vl = []
    for r in l:
        fl.append(r)
    for i in range(0, len(version)):
        vl += fl.filter(version=version[i])
    return vl


@app.route("/query/player", methods=['POST'])
async def query_player():
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
    if p.privacy or not p.accept_agreement:
        try:
            token = decode(request.cookies['jwt_token'])
        except KeyError:
            return {"status": "error", "message": "已设置隐私或未同意用户协议"}, 403
        if token == {}:
            return {"status": "error", "message": "已设置隐私或未同意用户协议"}, 403
        if token['exp'] < ts():
            return {"status": "error", "message": "会话过期"}, 403
        if token['username'] != obj["username"]:
            return {"status": "error", "message": "已设置隐私或未同意用户协议"}, 403
    if "b50" in obj:
        sd, dx = await get_dx_and_sd_for50(p)
    else:
        sd, dx = await get_dx_and_sd(p)
    await compute_ra(p)
    nickname = p.nickname
    if nickname == "":
        nickname = p.username if len(p.username) <= 8 else p.username[:8] + '…'
    try:
        user_general_data = json.loads(p.user_general_data)
    except Exception:
        user_general_data = None
    obj = {
        "username": p.username,
        "rating": p.rating,
        "additional_rating": p.additional_rating,
        "nickname": nickname,
        "plate": p.plate,
        "charts": {
            "sd": [record_json(c, p.mask) for c in sd],
            "dx": [record_json(c, p.mask) for c in dx]
        },
        "user_general_data": user_general_data,
    }
    return obj


@app.route("/query/plate", methods=['POST'])
@developer_required
async def query_plate():
    """
    获取某个用户的牌子信息。
    请求体为 JSON，参数需包含 `username` 或 `qq` 中的一项和 `version`。
    """
    obj = await request.json
    try:
        if "qq" in obj:
            p: Player = await Player.by_qq(obj["qq"])
        else:
            username = obj["username"]
            p: Player = await Player.aio_get(Player.username == username)
    except Exception:
        return {"message": "user not exists"}, 400
    if p.privacy or not p.accept_agreement:
        try:
            token = decode(request.cookies['jwt_token'])
        except KeyError:
            return {"status": "error", "message": "已设置隐私或未同意用户协议"}, 403
        if token == {}:
            return {"status": "error", "message": "已设置隐私或未同意用户协议"}, 403
        if token['exp'] < ts():
            return {"status": "error", "message": "会话过期"}, 403
        if token['username'] != obj["username"]:
            return {"status": "error", "message": "已设置隐私或未同意用户协议"}, 403
    v: List[Dict] = obj["version"]
    vl = await getplatelist(p, v)
    return {
        "verlist": [platerecord_json(c, p.mask) for c in vl]
    }


async def compute_ra(player: Player):
    rating = 0
    sd, dx = await get_dx_and_sd_for50(player)
    for t in sd:
        rating += int(t.ra)
    for t in dx:
        rating += int(t.ra)
    player.rating = rating
    player.access_time = time.time()
    await player.aio_save()
    return rating


@app.route("/player/update_records", methods=['POST'])
@login_or_token_required
async def update_records():
    """
    *需要登录
    更新用户的成绩信息
    请求体为 JSON List，格式可以参考 `/player/records` 接口返回的数据。
    """
    j = await request.get_json()
    dicts = {}
    if type(j) != type([]):
        return {"message": "导入数据格式有误"}, 404
    elif len(j) == 0:
        return {"message": "更新成功"}
    for record in j:
        # print(time.time())
        title = record['title']
        _type = record['type']
        level = record['level_index']
        m = get_music_by_title(md_title_type_map, title, _type)
        if m is None or level >= len(m["cids"]):
            continue
        cid = m["cids"][level]
        dicts[cid] = (min(record["achievements"], max_achievements(m)), std_fc(record.get("fc", "")),
                        std_fs(record.get("fs", "")), record["dxScore"])
    rs = await NewRecord.raw(
        'select * from newrecord where player_id = %s', g.user.id).aio_execute()
    updates = []
    creates = []
    for r in rs:
        # print(r.chart_id)
        if r.chart_id in dicts:
            v = dicts[r.chart_id]
            r.achievements = v[0]
            r.fc = std_fc(v[1])
            r.fs = std_fs(v[2])
            r.dxScore = v[3]
            updates.append(r)
            del dicts[r.chart_id]
    # print(len(dicts))
    for k in dicts:
        v = dicts[k]
        creates.append({"chart": k, "player": g.user.id,
                       "fc": std_fc(v[1]), "fs": std_fs(v[2]), "dxScore": v[3], "achievements": v[0]})
    if len(creates) > 0:
        await NewRecord.insert_many(creates).aio_execute()
    if len(updates) > 0:
        await NewRecord.aio_bulk_update(updates, fields=[
                            NewRecord.achievements, NewRecord.fc, NewRecord.fs, NewRecord.dxScore])
    await compute_ra(g.user)
    return {
        "message": "更新成功",
        "updates": len(updates),
        "creates": len(creates)
    }


@app.route("/player/update_records_html", methods=['POST'])
@login_or_token_required
async def update_records_html():
    """
    *需要登录
    通过 html 格式的数据更新您的舞萌 DX 查分器数据。
    """
    try:
        token = decode(request.cookies['jwt_token'])
        if token == {}:
            return {"status": "error", "message": "尚未登录"}, 403
        if token['exp'] < ts():
            return {"status": "error", "message": "会话过期"}, 403
    except KeyError:
        username = request.headers.get("username", default="")
        password = request.headers.get("password", default="")
        try:
            if username != "":
                g.user: Player = await Player.aio_get(Player.username == username)
                g.username = username
                if md5(password + g.user.salt) != g.user.password:
                    raise Exception()
        except Exception:
            return {"status": "error", "message": "尚未登录或密码错误"}, 403

    raw_data = await request.get_data()
    dicts = {}
    try:
        j = page_parser.wmdx_html2json(str(raw_data, encoding="utf-8"))
    except Exception as e:
        return {
                "message": str(e)
            }, 400
    # print(j)
    for record in j:
        # print(time.time())
        title = record['title']
        _type = record['type']
        level = record['level_index']
        m = get_music_by_title(md_title_type_map, title, _type)
        if m is None or level >= len(m["cids"]):
            continue
        cid = m["cids"][level]
        dicts[cid] = (min(record["achievements"], max_achievements(m)), std_fc(record.get("fc", "")),
                        std_fs(record.get("fs", "")), record["dxScore"])
    rs = await NewRecord.raw(
        'select * from newrecord where player_id = %s', g.user.id).aio_execute()
    updates = []
    creates = []
    for r in rs:
        # print(r.chart_id)
        if r.chart_id in dicts:
            v = dicts[r.chart_id]
            r.achievements = v[0]
            r.fc = std_fc(v[1])
            r.fs = std_fs(v[2])
            r.dxScore = v[3]
            updates.append(r)
            del dicts[r.chart_id]
    # print(len(dicts))
    for k in dicts:
        v = dicts[k]
        creates.append({"chart": k, "player": g.user.id,
                       "fc": std_fc(v[1]), "fs": std_fs(v[2]), "dxScore": v[3], "achievements": v[0]})
    if len(creates) > 0:
        await NewRecord.insert_many(creates).aio_execute()
    # print(updates)
    if len(updates) > 0:
        await NewRecord.aio_bulk_update(updates, fields=[
                          NewRecord.achievements, NewRecord.fc, NewRecord.fs, NewRecord.dxScore])
    await compute_ra(g.user)
    return {
        "message": "更新成功",
        "updates": len(updates),
        "creates": len(creates)
    }


@app.route("/player/update_record", methods=['POST'])
@login_or_token_required
async def update_record():
    """
    *需要登录
    更新单曲数据，请求体为 JSON，格式可以参考 `/player/records` 返回的 JSON List 中的一项。
    """
    record = await request.get_json()
    title = record['title']
    _type = record['type']
    level = record['level_index']
    m = get_music_by_title(md_title_type_map, title, _type)
    if m is None:
        return
    cid = m["cids"][level]
    r: NewRecord = await NewRecord.aio_get(
        (NewRecord.player == g.user.id) & (NewRecord.chart == cid))
    assert r
    r.achievements = min(record['achievements'], max_achievements(m))
    r.fc = std_fc(record['fc'])
    r.fs = std_fs(record['fs'])
    await r.aio_save()
    await compute_ra(g.user)
    return {
        "message": "更新成功",
    }


@app.route("/player/delete_records", methods=['DELETE'])
@login_or_token_required
async def delete_records():
    """
    *需要登录
    清除所有舞萌 DX 的歌曲成绩记录。
    """
    nums = await NewRecord.delete().where(NewRecord.player == g.user.id).aio_execute()
    await compute_ra(g.user)
    return {
        "message": nums
    }


async def get_hot_music_data():
    cursor = await NewRecord.raw(
        'select chart.music_id as music_id, sum(record.c) as cnt from (select chart_id, count(id) as c from newrecord group by chart_id) as record join chart on chart.id = chart_id group by chart.music_id ;'
    ).aio_execute()
    all_count = 0
    hot_music = defaultdict(lambda: 0)
    for elem in cursor:
        music_id = elem.music_id
        # 如果有标准谱则一起统计
        if str(music_id - 10000) in md_map:
            music_id -= 10000
        music = md_map[str(music_id)]
        cnt = float(elem.cnt)
        # 跳过宴谱
        if music_id > 100000:
            continue
        # 如果是最新版本则权重 × 2
        if music["basic_info"]["is_new"]:
            cnt *= 2
        # 如果有至少一个难度高于等级 13 则权重 × 2，有至少一个难度高于等级 13+ 则权重 × 3
        highest_ds = max(music["ds"])
        if highest_ds >= 13.7:
            cnt *= 3
        elif highest_ds >= 13:
            cnt *= 2
        all_count += cnt
        hot_music[str(music_id)] += cnt
    for key in hot_music:
        hot_music[key] /= all_count
    return hot_music


@app.route("/hot_music", methods=['GET'])
async def hot_music():
    """
    返回热门歌曲数据。
    """
    # check redis cache
    hot_music = await redis.get("maimaidxprober_hot_music")
    if hot_music is not None:
        return json.loads(hot_music)
    hot_music = await get_hot_music_data()
    await redis.set("maimaidxprober_hot_music", json.dumps(hot_music), ex=86400)
    return hot_music


async def get_random_hot(value):
    hot = await hot_music()
    for key, val in hot.items():
        if value < val:
            return key
        value -= val
    return 0


async def up_vote(music_id):
    try:
        m = await VoteResult.aio_get(VoteResult.music_id == music_id)
        m.total_vote += 1
        await m.aio_save()
    except Exception:
        await VoteResult.aio_create(music_id=music_id, total_vote=1, up_vote=1)


async def down_vote(music_id):
    try:
        m = await VoteResult.aio_get(VoteResult.music_id == music_id)
        m.down_vote += 1
        m.total_vote += 1
        await m.aio_save()
    except Exception:
        await VoteResult.aio_create(music_id=music_id, total_vote=1, down_vote=1)


@app.route("/vote_result", methods=['GET'])
async def vote_result():
    """
    返回投票结果。
    """
    results = await VoteResult.select().aio_execute()
    data = []
    for result in results:
        data.append({
            "music_id": result.music_id,
            "total_vote": result.total_vote,
            "down_vote": result.down_vote
        })
    return data


@app.route("/vote_box", methods=['GET', 'POST'])
async def vote_box():
    """
    返回投票箱数据。
    """
    if request.method == 'GET':
        left = await get_random_hot(random.random())
        right = left
        while right == left:
            right = await get_random_hot(random.random())
        token = md5(str(time.time()))
        await redis.set("maimaidxprober_vote_box_" + token, json.dumps({"left": left, "right": right}), ex=120)
        return {
            "left": left,
            "right": right,
            "token": token
        }
    if request.method == 'POST':
        obj = await request.json
        token = obj["token"]
        vote = obj["vote"]
        data = await redis.get("maimaidxprober_vote_box_" + token)
        if data is None:
            return {
                "message": "这个投票似乎已经消失了……"
            }, 400
        data = json.loads(data)
        left = data["left"]
        right = data["right"]
        await redis.delete("maimaidxprober_vote_box_" + token)
        if vote == 1:
            await up_vote(left)
            await down_vote(right)
        if vote == 2:
            await down_vote(left)
            await up_vote(right)
        if vote == 3:
            await down_vote(left)
            await down_vote(right)
        # get rank of left and right
        results = sorted(await vote_result(), key=lambda x: x["down_vote"] / x["total_vote"])
        left_rank = 1
        right_rank = 1
        rank = 1
        last_rate = 0
        for i, result in enumerate(results):
            rate = result["down_vote"] / result["total_vote"]
            if rate != last_rate:
                last_rate = rate
                rank = i + 1
            if result["music_id"] == left:
                left_rank = rank
            if result["music_id"] == right:
                right_rank = rank
        return {
            "result": [left_rank, right_rank]
        }
    

@app.route("/rating_ranking", methods=['GET'])
async def rating_ranking():
    """
    返回 rating 排行榜（设置隐私的用户不包含在内）。
    """
    players = await Player.select().where((Player.rating != 0) & (Player.privacy == False)).aio_execute()
    data = []
    for player in players:
        data.append({"username": player.username, "ra": player.rating})
    resp = await make_response(json.dumps(data, ensure_ascii=False))
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp


@app.route("/chart_stats", methods=['GET'])
async def chart_stats():
    """
    返回谱面的相对难度等数据。
    """
    global cs_cache
    global cs_cache_eTag

    if chart_stat_updated:
        cs_cache = {}
        cs_cache_eTag = None
        
    if len(cs_cache) > 0:
        if request.headers.get('If-None-Match') == '"' + cs_cache_eTag + '"':
            resp = await make_response("", 304)
            resp.headers['cache-control'] = "private, max_age=86400"
            return resp
        resp = await make_response(json.dumps(cs_cache, ensure_ascii=False, default=float))
        resp.headers['ETag'] = '"' + cs_cache_eTag + '"';
        resp.headers['content-type'] = "application/json; charset=utf-8"
        resp.headers['cache-control'] = "private, max_age=86400"
        return resp
    cursor2 = await NewRecord.raw('''select c.difficulty as diff,
        SUM(recordanalysis.sum_achievements) / SUM(recordanalysis.cnt) as ach,
        SUM(recordanalysis.d) / SUM(recordanalysis.cnt) as d,
        SUM(recordanalysis.c) / SUM(recordanalysis.cnt) as c,
        SUM(recordanalysis.b) / SUM(recordanalysis.cnt) as b,
        SUM(recordanalysis.bb) / SUM(recordanalysis.cnt) as bb,
        SUM(recordanalysis.bbb) / SUM(recordanalysis.cnt) as bbb,
        SUM(recordanalysis.a) / SUM(recordanalysis.cnt) as a,
        SUM(recordanalysis.aa) / SUM(recordanalysis.cnt) as aa,
        SUM(recordanalysis.aaa) / SUM(recordanalysis.cnt) as aaa,
        SUM(recordanalysis.s) / SUM(recordanalysis.cnt) as s,
        SUM(recordanalysis.sp) / SUM(recordanalysis.cnt) as sp,
        SUM(recordanalysis.ss) / SUM(recordanalysis.cnt) as ss,
        SUM(recordanalysis.ssp) / SUM(recordanalysis.cnt) as ssp,
        SUM(recordanalysis.sss) / SUM(recordanalysis.cnt) as sss,
        SUM(recordanalysis.sssp) / SUM(recordanalysis.cnt) as sssp,
        SUM(recordanalysis.fc) / SUM(recordanalysis.cnt) as fc,
        SUM(recordanalysis.fcp) / SUM(recordanalysis.cnt) as fcp,
        SUM(recordanalysis.ap) / SUM(recordanalysis.cnt) as ap,
        SUM(recordanalysis.app) / SUM(recordanalysis.cnt) as app
        from recordanalysis join chart c on recordanalysis.chart_id = c.id group by c.difficulty;''').aio_execute()
    diff_data = {}
    for elem in cursor2:
        diff_data[elem.diff] = {
            "achievements": elem.ach,
            "dist": [elem.d, elem.c, elem.b, elem.bb, elem.bbb, elem.a, elem.aa, elem.aaa, elem.s, elem.sp, elem.ss, elem.ssp, elem.sss, elem.sssp],
            "fc_dist": [1 - float(elem.fc) - float(elem.fcp) - float(elem.ap) - float(elem.app), float(elem.fc), elem.fcp, elem.ap, elem.app]
        }

    cursor = await NewRecord.raw(
        '''select recordanalysis.*, rst.std_dev as std_dev, c2.music_id as mid, c2.level as level, c2.difficulty as diff from recordanalysis
        join record_stddev_table rst on recordanalysis.chart_id = rst.c
        join chart c2 on recordanalysis.chart_id = c2.id;'''
    ).aio_execute()
    charts = []
    charts = defaultdict(lambda: [{}, {}, {}, {}, {}])
    for elem in cursor:
        data2 = diff_data[elem.diff]
        charts[elem.mid][elem.level] = {
            "cnt": elem.cnt,
            "diff": elem.diff,
            "fit_diff": maimai_analysis.get_diff(
                elem.diff,
                elem.sum_achievements / elem.cnt - data2["achievements"],
                ((elem.s + elem.sp + elem.ss + elem.ssp + elem.sss + elem.sssp) / elem.cnt - sum(data2["dist"][8:])) / sum(data2["dist"][8:]),
                ((elem.sss + elem.sssp) / elem.cnt - sum(data2["dist"][12:])) / sum(data2["dist"][12:]),
                (elem.sssp / elem.cnt - data2["dist"][13]) / data2["dist"][13],
                ),
            "avg": elem.sum_achievements / elem.cnt,
            "avg_dx": elem.sum_dx_score / elem.cnt,
            "std_dev": elem.std_dev,
            "dist": [elem.d, elem.c, elem.b, elem.bb, elem.bbb, elem.a, elem.aa, elem.aaa, elem.s, elem.sp, elem.ss, elem.ssp, elem.sss, elem.sssp],
            "fc_dist": [elem.cnt - int(elem.fc) - int(elem.fcp) - int(elem.ap) - int(elem.app), int(elem.fc), elem.fcp, elem.ap, elem.app]
        }

    data = {"charts": charts, "diff_data": diff_data}
    cs_cache = data
    cs_cache_eTag = md5(json.dumps(cs_cache, ensure_ascii=False, default=float))
    resp = await make_response(json.dumps(data, ensure_ascii=False, default=float))
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp


@app.route("/maidle/data", methods=['GET'])
async def get_maidle_data():
    """
    获取 maidle 的歌曲数据。
    """
    if request.headers.get('If-None-Match') == '"' + maidle_cache_eTag + '"':
        resp = await make_response("", 304)
        resp.headers['cache-control'] = "private, max_age=86400"
        return resp
    resp = await make_response(json.dumps(maidle_cache))
    resp.headers['ETag'] = '"' + maidle_cache_eTag + '"';
    resp.headers['content-type'] = "application/json; charset=utf-8"
    resp.headers['cache-control'] = "private, max_age=86400"
    return resp


@app.route('/maidle/single', methods=['POST'])
async def maidle_single():
    """
    进行一次 Maidle 游戏。
    请求体为 JSON，为第一次猜测的歌曲 ID。
    """
    obj = await request.json
    uuid = obj.get('uuid', '')
    guess_id = obj.get('guess_id', 0)
    lists = obj.get('lists', [])
    if guess_id == 0 or guess_id not in maidle_map:
        return {
            "message": "歌曲 ID 不存在"
        }, 400
    
    maidle = None
    if uuid != '':
        # check redis cache
        music_id = await redis.get("maidle_" + uuid)
        if music_id is not None:
            maidle = Maidle(id=int(music_id))

    if maidle is None:
        # create a new session
        maidle = Maidle(id_range=lists, id=None)
        music_id = maidle.music['id']
        uuid = md5(str(time.time()) + str(random.random()))
        await redis.set("maidle_" + uuid, str(music_id), ex=900) # 15 min

    return {
        "uuid": uuid,
        "test": maidle.maidle_test(maidle_map[guess_id])
    }


@app.route('/maidle/answer', methods=['POST'])
async def maidle_answer():
    """
    获取 Maidle 答案。
    """
    obj = await request.json
    uuid = obj.get('uuid', '')
    if uuid != '':
        # check redis cache
        music_id = await redis.get("maidle_" + uuid)
        if music_id is not None:
            maidle = Maidle(id=int(music_id))
            return {
                "title": maidle.music['title'],
                "artist": maidle.music['artist'],
                "id": maidle.music['id'],
            }
    
    return {
        "msg": "error"
    }, 400


# Vote 2025
@app.route("/vote2025/data", methods=['GET'])
async def vote2025_data():
    data = []
    for cursor in await Vote2025.select().aio_execute():
        body = json.loads(cursor.vote_body)
        player = await Player.aio_get(Player.id == cursor.player_id)
        body['player'] = player.nickname if player.nickname else player.username
        data.append(body)
    return data


with open('music_data_2024_last.json', 'r', encoding='utf-8') as f:
    vote2025_md = json.load(f)
    vote2025_md_etag = md5(json.dumps(vote2025_md, ensure_ascii=False))
    vote2025_md_map = {}
    for elem in vote2025_md:
        vote2025_md_map[str(elem['id'])] = elem
    # print(vote2025_md_map.keys())

@app.route("/vote2025/music_data", methods=['GET'])
async def vote2025_music_data():
    # Return the content of music_data_2024_last.json with proper cache headers
    try:
        # Check if we can return 304 Not Modified
        if request.headers.get('If-None-Match') == f'"{vote2025_md_etag}"':
            resp = await make_response("", 304)
            resp.headers['cache-control'] = "private, max_age=86400"
            return resp
            
        # Otherwise return the full response with cache headers
        resp = await make_response(json.dumps(vote2025_md, ensure_ascii=False))
        resp.headers['ETag'] = f'"{vote2025_md_etag}"'
        resp.headers['content-type'] = "application/json; charset=utf-8"
        resp.headers['cache-control'] = "private, max_age=86400"
        return resp
    except Exception as e:
        return {"message": f"Error loading music data: {str(e)}"}, 500


@app.route("/vote2025", methods=['GET', 'POST'])
@login_required
async def vote2025():
    """
    获取、提交用户的投票信息。
    """
    if request.method == 'GET':
        # 获取用户的投票信息
        try:
            vote = await Vote2025.aio_get(Vote2025.player == g.user.id)
            return json.loads(vote.vote_body)
        except Exception:
            return {
                "unvoted": False
            }
    elif request.method == 'POST':
        return {
            "message": "投票已结束"
        }
        try: 
            vote = await Vote2025.aio_get(Vote2025.player == g.user.id)
            return {
                "message": "您已经投过票了，请勿重复投票"
            }, 400
        except Exception:
            pass
        obj = await request.json
        vote_list = obj.get("vote_list", [])
        if len(vote_list) > 40:
            return {
                "message": "最多只能投 40 首歌"
            }, 400
        vote_list = list(set(vote_list))
        for vote_id in vote_list:
            if str(vote_id) not in vote2025_md_map:
                return {
                    "message": f"歌曲 ID {vote_id} 不存在"
                }, 400
        suggest_id = obj.get("suggest_id", 0)
        if str(suggest_id) not in vote2025_md_map:
            return {
                "message": "真爱歌曲 ID 不存在"
            }, 400
        suggest_comment = obj.get("suggest_comment", "")
        remote_addr = request.remote_addr
        xip = request.headers.get("X-Real-IP", default="")
        if xip != "":
            remote_addr = xip
        ts = int(time.time_ns() / 1e6)
        await Vote2025.aio_create(
            player=g.user.id,
            vote_body=json.dumps({
                "vote_list": vote_list,
                "suggest_id": suggest_id,
                "suggest_comment": suggest_comment
            }, ensure_ascii=False),
            remote_addr=remote_addr,
            timestamp=ts
        )
        return {
            "message": "投票成功"
        }