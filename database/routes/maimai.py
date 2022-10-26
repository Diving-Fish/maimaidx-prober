import asyncio
from collections import defaultdict
from app import app, developer_required, login_required, md5
from quart import Quart, request, g, make_response
from tools._jwt import *
from models.maimai import *
import tools.page_parser as page_parser


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


def is_new_2(r: Record):
    t = (r.title, r.type)
    if t in md_title_type_map:
        return md_title_type_map[t]["is_new"]
    return False


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
            "privacy": u.privacy,
            "plate": u.plate
        }
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
            for key in obj:
                if key in ("nickname", "bind_qq", "additional_rating", "privacy"):
                    g.user.__setattr__(key, obj[key])
            g.user.save()
            u: Player = g.user
            return {
                "username": u.username,
                "nickname": u.nickname,
                "additional_rating": u.additional_rating,
                "bind_qq": u.bind_qq,
                "privacy": u.privacy,
                "plate": u.plate
            }
        except Exception as e:
            print(e)
            return {
                "message": "error"
            }, 400


def verify_plate(player, version, plate_type) -> Tuple[bool, str]:
    try:
        if version == "无":
            return True, ""
        plate_name = get_plate_name(version, plate_type)
        if plate_name == "真将":
            return False, ""
        return True, plate_name
    except Exception:
        return False, ""



@app.route("/music_data", methods=['GET'])
async def get_music_data():
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
@login_required
async def get_records():
    r = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', g.user.id)
    await compute_ra(g.user)
    records = []
    for record in r:
        elem = record_json(record)
        records.append(elem)
    return {"records": records, "username": g.username, "additional_rating": g.user.additional_rating}


@app.route("/dev/player/records", methods=['GET'])
@developer_required
async def dev_get_records():
    username = request.args.get("username", type=str, default="")
    if username == "":
        return {"message": "no such user"}, 400
    try:
        player: Player = Player.get(Player.username == username)
    except Exception:
        return {"message": "no such user"}, 400
    r = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id)
    await compute_ra(player)
    records = []
    for record in r:
        elem = record_json(record)
        records.append(elem)
    return {"records": records, "username": player.username, "additional_rating": player.additional_rating}


@app.route("/player/test_data", methods=['GET'])
async def get_test_data():
    r = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', 293)
    records = []
    for record in r:
        elem = record_json(record)
        records.append(elem)
    return {"records": records, "username": "TESTUSER", "additional_rating": "2100"}


def get_dx_and_sd(player):
    l = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id)
    l1 = []
    l2 = []
    for r in l:
        setattr(r, 'ra', r.ds * get_l(r.achievements)
                * min(100.5, r.achievements) / 100)
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
        setattr(r, 'ra', r.ds * get_l(r.achievements)
                * min(100.5, r.achievements) / 100)
        if r.is_new:
            l2.append(r)
        else:
            l1.append(r)
    l1.sort(key=lambda x: x.ra, reverse=True)
    l2.sort(key=lambda x: x.ra, reverse=True)
    return l1[:35], l2[:15]


def getplatelist(player, version: List[Dict]):
    l = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs,chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.version as `version`, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id)
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
    if "b50" in obj:
        sd, dx = get_dx_and_sd_for50(p)
    else:
        sd, dx = get_dx_and_sd(p)
    asyncio.create_task(compute_ra(p))
    nickname = p.nickname
    if nickname == "":
        nickname = p.username if len(p.username) <= 8 else p.username[:8] + '…'
    try:
        user_data = json.loads(p.user_data)
    except Exception:
        user_data = None
    return {
        "username": p.username,
        "rating": p.rating,
        "additional_rating": p.additional_rating,
        "nickname": nickname,
        "plate": p.plate,
        "charts": {
            "sd": [record_json(c) for c in sd],
            "dx": [record_json(c) for c in dx]
        },
        "user_id": p.user_id,
        "user_data": user_data
    }


@app.route("/query/plate", methods=['POST'])
async def query_plate():
    obj = await request.json
    try:
        if "qq" in obj:
            p: Player = Player.get(Player.bind_qq == obj["qq"])
        else:
            username = obj["username"]
            p: Player = Player.get(Player.username == username)
    except Exception:
        return {"message": "user not exists"}, 400
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
    v: List[Dict] = obj["version"]
    vl = getplatelist(p, v)
    return {
        "verlist": [platerecord_json(c) for c in vl]
    }


async def compute_ra(player: Player):
    rating = 0
    sd, dx = get_dx_and_sd(player)
    for t in sd:
        rating += int(t.ra)
    for t in dx:
        rating += int(t.ra)
    player.rating = rating
    player.save()
    return rating


@app.route("/player/update_records", methods=['POST'])
@login_required
async def update_records():
    global cs_need_update
    cs_need_update = True
    j = await request.get_json()
    dicts = {}
    if "userId" in j:
        try:
            for ml in j["userMusicList"]:
                for m in ml["userMusicDetailList"]:
                    if str(m["musicId"]) not in md_map:
                        continue
                    music = md_map[str(m["musicId"])]
                    level = m["level"]
                    achievement = min(1010000, m["achievement"])
                    fc = ["", "fc", "fcp", "ap", "app"][m["comboStatus"]]
                    fs = ["", "fs", "fsp", "fsd", "fsdp"][m["syncStatus"]]
                    dxScore = m["deluxscoreMax"]
                    cid = music["cids"][level]
                    dicts[cid] = (achievement / 10000.0, fc, fs, dxScore)
            g.user.user_id = j["userId"]
            g.user.user_data = json.dumps(j["userData"]) if "userData" in j else ""
            g.user.save()
        except Exception as e:
            raise e
            return {
                "message": str(e)
            }, 400
    else:
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
@login_required
async def update_record():
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
@login_required
async def delete_records():
    global cs_need_update
    cs_need_update = True
    nums = NewRecord.delete().where(NewRecord.player == g.user.id).execute()
    await compute_ra(g.user)
    return {
        "message": nums
    }


@app.route("/rating_ranking", methods=['GET'])
async def rating_ranking():
    players = Player.select().where((Player.rating != 0) & (Player.privacy == False))
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
    results = Message.select(Message, Player).join(
        Player).where(Message.ts >= today_ts)
    l = []
    for r in results:
        l.append({"text": r.text, "username": r.player.username,
                 "ts": r.ts, "nickname": r.nickname})
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
    # return {}
    global cs_need_update
    global cs_cache
    global cs_cache_eTag
    if len(cs_cache) > 0:
        if request.headers.get('If-None-Match') == '"' + cs_cache_eTag + '"':
            resp = await make_response("", 304)
            resp.headers['cache-control'] = "private, max_age=86400"
            return resp
        resp = await make_response(json.dumps(cs_cache, ensure_ascii=False))
        resp.headers['ETag'] = '"' + cs_cache_eTag + '"';
        resp.headers['content-type'] = "application/json; charset=utf-8"
        resp.headers['cache-control'] = "private, max_age=86400"
        return resp
    cursor = NewRecord.raw(
        'select newrecord.chart_id, count(*) as cnt, avg(achievements) as `avg`,'
        ' sum(case when achievements >= 100 then 1 else 0 end) as sssp_count from newrecord group by chart_id'
    )
    data = defaultdict(lambda: [{}, {}, {}, {}, {}])
    for elem in cursor:
        data[elem.chart.music.id][elem.chart.level] = {"count": elem.cnt,
                                                                                  "avg": elem.avg,
                                                                                  "sssp_count": int(elem.sssp_count)
                                                                                  }
    level_dict = defaultdict(lambda: [])
    md = md_cache
    for elem in md:
        key = elem['id']
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
        level_dict[level].sort(
            key=lambda x: x['sssp_count'] / x['count'], reverse=True)
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
    cs_cache_eTag = md5(json.dumps(cs_cache, ensure_ascii=False))
    cs_need_update = False
    resp = await make_response(json.dumps(data, ensure_ascii=False))
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp
