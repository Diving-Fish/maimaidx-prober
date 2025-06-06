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
from access.maimai import *
from access.redis import redis
import random
from tools.maidle import Maidle, maidle_data as maidle_cache, songs_id_map as maidle_map


cs_need_update = True
cs_cache = {}
cs_cache_eTag = md5(json.dumps(cs_cache, ensure_ascii=False))
md_cache_eTag = md5(json.dumps(md_cache))

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
    records_dict = await maimai_get_records(g.user, False)
    records = []
    for sub_records in records_dict.values():
        records += sub_records
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
    user = Player.get(Player.id == 636)
    records_dict = await maimai_get_records(user, False)
    records = []
    for sub_records in records_dict.values():
        records += sub_records
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
            player: Player = Player.get(Player.username == username)
        else:
            player: Player = Player.by_qq(qq)
    except Exception:
        return {"message": "no such user"}, 400
    if player.privacy or not player.accept_agreement:
        return {"status": "error", "message": "已设置隐私或未同意用户协议"}, 403
    records_dict = await maimai_get_records(player, player.mask)
    records = []
    for sub_records in records_dict.values():
        records += sub_records
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
            p: Player = Player.by_qq(obj["qq"])
        else:
            username = obj["username"]
            p: Player = Player.get(Player.username == username)
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
    
    records_dict = await maimai_get_records(p, p.mask)
    records = defaultdict()
    for music_id in music_ids:
        records[music_id] = records_dict[music_id] if music_id in records_dict.keys() else []
    return records


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
        charts = await maimai_get_dx_and_sd_for50(p)
    else:
        charts = await maimai_get_dx_and_sd(p)
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
        "charts": charts,
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
    vl = await maimai_get_plate_list(p, v)
    return {"verlist": vl}


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
    if type(j) != type([]):
        return {"message": "导入数据格式有误"}, 404
    elif len(j) == 0:
        return {"message": "更新成功"}
    data = record_json_list_for_input(md_title_type_map, j)
    await maimai_update_records_cache(g.user, data)
    return {
        "message": "更新成功",
        "updates": -1,
        "creates": -1
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
    data = record_json_list_for_input(md_cache, j)
    await maimai_update_records_cache(g.user, data)
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
    r.achievements = min(record['achievements'], max_achievements(m))
    r.fc = std_fc(record['fc'])
    r.fs = std_fs(record['fs'])
    r.save()
    await maimai_compute_ra(g.user)
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
    await maimai_compute_ra(g.user)
    return {
        "message": nums
    }


def get_hot_music_data():
    cursor = NewRecord.raw(
        'select chart.music_id as music_id, sum(record.c) as cnt from (select chart_id, count(id) as c from newrecord group by chart_id) as record join chart on chart.id = chart_id group by chart.music_id ;'
    )
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
    hot_music = get_hot_music_data()
    await redis.set("maimaidxprober_hot_music", json.dumps(hot_music), ex=86400)
    return hot_music


async def get_random_hot(value):
    hot = await hot_music()
    for key, val in hot.items():
        if value < val:
            return key
        value -= val
    return 0


def up_vote(music_id):
    try:
        m = VoteResult.get(VoteResult.music_id == music_id)
        m.total_vote += 1
        m.save()
    except Exception:
        VoteResult.create(music_id=music_id, total_vote=1, up_vote=1)


def down_vote(music_id):
    try:
        m = VoteResult.get(VoteResult.music_id == music_id)
        m.down_vote += 1
        m.total_vote += 1
        m.save()
    except Exception:
        VoteResult.create(music_id=music_id, total_vote=1, down_vote=1)


@app.route("/vote_result", methods=['GET'])
async def vote_result():
    """
    返回投票结果。
    """
    results = VoteResult.select()
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
            up_vote(left)
            down_vote(right)
        if vote == 2:
            down_vote(left)
            up_vote(right)
        if vote == 3:
            down_vote(left)
            down_vote(right)
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
