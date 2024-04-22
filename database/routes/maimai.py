"""
Author: Diving-Fish

这个文件的目录会被反向代理映射到
https://www.diving-fish.com/api/maimaidxprober/*
例如 /player/profile 可以通过 https://www.diving-fish.com/api/maimaidxprober/player/profile 访问。
"""
import asyncio
import time
from collections import defaultdict
from app import app, developer_required, login_required, login_or_token_required, md5, is_developer
from quart import Quart, request, g, make_response
from tools._jwt import *
from models.maimai import *
import tools.page_parser as page_parser
import tools.maimai_analysis_curve as maimai_analysis
from tools.analysis_template import return_template


cs_need_update = True
cs_cache = {}
cs_cache_eTag = md5(json.dumps(cs_cache, ensure_ascii=False))
md_cache = music_data()
md_cache_eTag = md5(json.dumps(md_cache))
md_map = {}
md_title_type_map = {}
for music in md_cache:
    md_map[music['id']] = music
    md_title_type_map[(music["title"], music["type"])] = music


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
            g.user.save()
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
                        player = Player.get((Player.bind_qq == bind_qq) & (Player.id != g.user.id))
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
                        player = Player.get((Player.qq_channel_uid == qq_channel_uid) & (Player.id != g.user.id))
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
            g.user.save()
            u: Player = g.user
            return u.user_json()

        except Exception as e:
            print(e)
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
        "token": g.user.generate_import_token()
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
    r = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', g.user.id)
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
            player: Player = Player.get(Player.username == username)
        else:
            player: Player = Player.by_qq(qq)
    except Exception:
        return {"message": "no such user"}, 400
    r = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id)
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

@app.route("/dev/player/record", methods=['GET'])
@developer_required
async def dev_get_record():
    """
    *需要开发者
    获取某个用户的单曲成绩信息。
    请求体为 JSON，参数需包含 `username` 或 `qq` 和 歌曲id。
    """
    username = request.args.get("username", type=str, default="")
    qq = request.args.get("qq", type=str, default="")
    music_id = request.args.get("music_id", type=str, default="")

    if username == "" and qq == "":
        return {"message": "no such user"}, 400
    if music_id == "":
        return {"message": "no such music_id"}, 400
    try:
        if qq == "":
            player: Player = Player.get(Player.username == username)
        else:
            player: Player = Player.by_qq(qq)
    except Exception:
        return {"message": "no such user"}, 400
    r = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and music_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id,int(music_id))
    records = []
    for record in r:
        elem = record_json(record, player.mask)
        records.append(elem)
    return {
        "records": records
    }


def get_dx_and_sd(player):
    l = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id)
    l1 = []
    l2 = []
    for r in l:
        setattr(r, 'ra', ScoreCoefficient(r.achievements).ra(r.ds))
        if r.is_new:
            l2.append(r)
        else:
            l1.append(r)
    l1.sort(key=lambda x: x.ra, reverse=True)
    l2.sort(key=lambda x: x.ra, reverse=True)
    return l1[:25], l2[:15]


def get_dx_and_sd_for50(player):
    l = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id)
    l1 = []
    l2 = []
    for r in l:
        setattr(r, 'ra', ScoreCoefficient(r.achievements).ra(r.ds))
        if r.is_new:
            l2.append(r)
        else:
            l1.append(r)
    l1.sort(key=lambda x: x.ra, reverse=True)
    l2.sort(key=lambda x: x.ra, reverse=True)
    return l1[:35], l2[:15]


def getplatelist(player, version: List[Dict]):
    l = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.version as `version`, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id)
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
            p: Player = Player.by_qq(obj["qq"])
        else:
            username = obj["username"]
            p: Player = Player.get(Player.username == username)
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
        sd, dx = get_dx_and_sd_for50(p)
    else:
        sd, dx = get_dx_and_sd(p)
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
async def query_plate():
    """
    获取某个用户的牌子信息。
    请求体为 JSON，参数需包含 `username` 或 `qq` 中的一项和 `version`。
    """
    obj = await request.json
    try:
        if "qq" in obj:
            p: Player = Player.by_qq(obj["qq"])
        else:
            username = obj["username"]
            p: Player = Player.get(Player.username == username)
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
    vl = getplatelist(p, v)
    return {
        "verlist": [platerecord_json(c, p.mask) for c in vl]
    }


async def compute_ra(player: Player):
    rating = 0
    sd, dx = get_dx_and_sd_for50(player)
    for t in sd:
        rating += int(t.ra)
    for t in dx:
        rating += int(t.ra)
    player.rating = rating
    player.access_time = time.time()
    player.save()
    return rating


@app.route("/player/update_records", methods=['POST'])
@login_or_token_required
async def update_records():
    """
    *需要登录
    更新用户的成绩信息
    请求体为 JSON List，格式可以参考 `/player/records` 接口返回的数据。
    """
    global cs_need_update
    cs_need_update = True
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
        m = get_music_by_title(md_cache, title, _type)
        if m is None or level >= len(m["cids"]):
            continue
        cid = m["cids"][level]
        dicts[cid] = (record["achievements"], record["fc"],
                        record["fs"], record["dxScore"])
    rs = NewRecord.raw(
        'select * from newrecord where player_id = %s', g.user.id)
    updates = []
    creates = []
    for r in rs:
        # print(r.chart_id)
        if r.chart_id in dicts:
            v = dicts[r.chart_id]
            r.achievements = min(v[0], 101)
            r.fc = v[1]
            r.fs = v[2]
            r.dxScore = v[3]
            updates.append(r)
            del dicts[r.chart_id]
    # print(len(dicts))
    for k in dicts:
        v = dicts[k]
        creates.append({"chart": k, "player": g.user.id,
                       "fc": v[1], "fs": v[2], "dxScore": v[3], "achievements": min(v[0], 101)})
    NewRecord.insert_many(creates).execute()
    # print(updates)
    NewRecord.bulk_update(updates, fields=[
                          NewRecord.achievements, NewRecord.fc, NewRecord.fs, NewRecord.dxScore])
    await compute_ra(g.user)
    return {
        "message": "更新成功",
    }


@app.route("/player/update_records_html", methods=['POST'])
async def update_records_html():
    """
    *需要登录
    通过 html 格式的数据更新您的舞萌 DX 查分器数据。
    """
    global cs_need_update
    cs_need_update = True

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
                g.user: Player = Player.get(Player.username == username)
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
        m = get_music_by_title(md_cache, title, _type)
        if m is None or level >= len(m["cids"]):
            continue
        cid = m["cids"][level]
        dicts[cid] = (record["achievements"], record["fc"],
                        record["fs"], record["dxScore"])
    rs = NewRecord.raw(
        'select * from newrecord where player_id = %s', g.user.id)
    updates = []
    creates = []
    for r in rs:
        # print(r.chart_id)
        if r.chart_id in dicts:
            v = dicts[r.chart_id]
            r.achievements = min(v[0], 101)
            r.fc = v[1]
            r.fs = v[2]
            r.dxScore = v[3]
            updates.append(r)
            del dicts[r.chart_id]
    # print(len(dicts))
    for k in dicts:
        v = dicts[k]
        creates.append({"chart": k, "player": g.user.id,
                       "fc": v[1], "fs": v[2], "dxScore": v[3], "achievements": min(v[0], 101)})
    if len(creates) > 0:
        NewRecord.insert_many(creates).execute()
    # print(updates)
    if len(updates) > 0:
        NewRecord.bulk_update(updates, fields=[
                          NewRecord.achievements, NewRecord.fc, NewRecord.fs, NewRecord.dxScore])
    await compute_ra(g.user)
    return {
        "message": "更新成功",
    }


@app.route("/player/update_record", methods=['POST'])
@login_or_token_required
async def update_record():
    """
    *需要登录
    更新单曲数据，请求体为 JSON，格式可以参考 `/player/records` 返回的 JSON List 中的一项。
    """
    # must be update.
    global cs_need_update
    cs_need_update = True
    record = await request.get_json()
    title = record['title']
    _type = record['type']
    level = record['level_index']
    m = get_music_by_title(md_cache, title, _type)
    if m is None:
        return
    cid = m["cids"][level]
    r: NewRecord = NewRecord.get(
        (NewRecord.player == g.user.id) & (NewRecord.chart == cid))
    assert r
    r.achievements = min(record['achievements'], 101)
    r.fc = record['fc']
    r.fs = record['fs']
    r.save()
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
    global cs_need_update
    cs_need_update = True
    nums = NewRecord.delete().where(NewRecord.player == g.user.id).execute()
    await compute_ra(g.user)
    return {
        "message": nums
    }


@app.route("/rating_ranking", methods=['GET'])
async def rating_ranking():
    """
    返回 rating 排行榜（设置隐私的用户不包含在内）。
    """
    players = Player.select().where((Player.rating != 0) & (Player.privacy == False))
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
    global cs_need_update
    global cs_cache
    global cs_cache_eTag
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
    cursor2 = NewRecord.raw('''select c.difficulty as diff,
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
        from recordanalysis join chart c on recordanalysis.chart_id = c.id group by c.difficulty;''')
    diff_data = {}
    for elem in cursor2:
        diff_data[elem.diff] = {
            "achievements": elem.ach,
            "dist": [elem.d, elem.c, elem.b, elem.bb, elem.bbb, elem.a, elem.aa, elem.aaa, elem.s, elem.sp, elem.ss, elem.ssp, elem.sss, elem.sssp],
            "fc_dist": [1 - float(elem.fc) - float(elem.fcp) - float(elem.ap) - float(elem.app), float(elem.fc), elem.fcp, elem.ap, elem.app]
        }

    cursor = NewRecord.raw(
        '''select recordanalysis.*, rst.std_dev as std_dev, c2.music_id as mid, c2.level as level, c2.difficulty as diff from recordanalysis
        join record_stddev_table rst on recordanalysis.chart_id = rst.c
        join chart c2 on recordanalysis.chart_id = c2.id;'''
    )
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
    cs_need_update = False
    resp = await make_response(json.dumps(data, ensure_ascii=False, default=float))
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp
