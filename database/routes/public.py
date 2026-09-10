import asyncio
import random
import re
import string
import json
from app import (app, login_required, mail_config, md5, developer_required,
                 APPLICATION_DOC_URL, MIGRATION_DOC_URL, developer_token_sunset_ts)
from quart import Quart, request, g, make_response
from tools._jwt import *
from models.maimai import *
from tools.mail import *


advertisements_data = []
with open('advertisement.json') as ad:
    advertisements_data = json.load(ad)

#: 用户名格式，与 IdP 的 app/validators.py 保持一致（那边是唯一权威，
#: 改动请两处一起改）。这个端点前端已不用，但第三方 uni-app 客户端还在调，
#: 而它历来不做任何校验，两条注册路的政策因此长期不一致。
#:
#: 特别地：带空白的用户名会绕过下面的重名检查，因为 username 列的
#: utf8mb4_0900_ai_ci 是 NO PAD 排序规则，'名字 ' 与 '名字' 是两个不同的
#: 值；注册完之后本人还必须一字不差地连空格一起输入才登得上。库里已经
#: 这样攒下 1311 个账号，修补在 diving-fish-auth 的 login_candidates。
USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{2,24}$")
USERNAME_RULE = "用户名为 2~24 位，仅可包含字母、数字、下划线和连字符"


@app.route("/count_view", methods=['GET'])
async def count_view():
    v: Views = await Views.aio_get()
    v.prober += 1
    await v.aio_save()
    return {"views": v.prober}


async def message_resp():
    today_ts = int((time.time() + 8 * 3600) / 86400) * 86400 - 8 * 3600
    results = await Message.select(Message, Player).join(
        Player).where(Message.ts >= today_ts).aio_execute()
    l = []
    for r in results:
        l.append({"text": r.text, "username": r.player.username,
                 "ts": r.ts, "nickname": r.nickname})
    resp = await make_response(json.dumps(l, ensure_ascii=False))
    resp.headers['content-type'] = "application/json; charset=utf-8"
    return resp


@app.route("/alive_check", methods=['GET'])
async def alive_check():
    return {"message": "ok"}


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
        await a.aio_save(force_insert=True)
    return await message_resp()


@app.route("/advertisements", methods=['GET'])
async def advertisements():
    return advertisements_data


@app.route("/feedback", methods=['POST'])
async def feedback():
    j = await request.get_json()
    await FeedBack.aio_create(**j)
    return {"message": "提交成功"}


@app.route("/login", methods=['POST'])
async def login():
    j = await request.get_json()
    username = j["username"]
    password = j["password"]
    try:
        user: Player = await Player.aio_get(Player.username == username)
        if md5(password + user.salt) == user.password:
            resp = await make_response({"message": "登录成功"})
            resp.set_cookie('jwt_token', username_encode(
                username), max_age=30 * 86400)
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
    username = j["username"]
    # isinstance 一并挡住非字符串：这个端点从来不校验入参，
    # 不加这个判断，传个数字进来会变成 500 而不是 400
    if not isinstance(username, str) or not USERNAME_RE.match(username):
        return {
            "errcode": -2,
            "message": USERNAME_RULE,
        }, 400
    player = await Player.select().where(Player.username == username).aio_execute()
    if len(player) > 0:
        return {
            "errcode": -1,
            "message": "此用户名已存在",
        }, 400
    salt = ''.join(random.sample(string.ascii_letters + string.digits, 16))
    await Player.aio_create(username=username, salt=salt,
                  password=md5(j["password"] + salt))
    resp = await make_response({"message": "注册成功"})
    resp.set_cookie('jwt_token', username_encode(username))
    return resp


@app.route("/player/change_password", methods=['POST'])
@login_required
async def change_password():
    password = (await request.json)["password"]
    # if len(password) >= 30:
    #     return {"message": "密码不能大于30位"}, 400
    g.user.password = md5(password + g.user.salt)
    await g.user.aio_save()
    return {"message": "success"}


@app.route('/channel_to_qq', methods=['GET', 'POST'])
@developer_required
async def channel_to_qq():
    cuid = request.args.get("cuid", type=str, default="")
    if request.method == 'GET':
        try:
            player = await Player.aio_get(Player.qq_channel_uid == cuid)
        except Exception:
            return {"qq": ""}
        return {"qq": player.bind_qq}
    else:
        qq = (await request.json)["qq"]
        try:
            player = await Player.aio_get(Player.qq_channel_uid == cuid)
        except Exception:
            try:
                player = await Player.aio_get(Player.bind_qq == qq)
            except Exception:
                return {"message": "failed"}, 400
        player.qq_channel_uid = cuid
        player.bind_qq = qq
        await player.aio_save()
        return {"message": "success"}

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

@app.route('/token_available', methods=['GET'])
async def token_available():
    t = request.args.get('token', type=str, default='')
    if t == "":
        return {"message": "non-exist"}, 404
    try:
        player = await Player.aio_get(Player.import_token == t)
        return {"message": "ok"}, 200
    except Exception:
        return {"message": "non-exist"}, 404


@app.route('/developer_token', methods=['GET', 'POST', 'PUT'])
@login_required
async def developer_token():
    # **停止签发新的开发者 token。** GET 保留——存量开发者要能继续看到
    # 自己手上那些 token 的状态和额度，把它一起关掉只会让人一头雾水；
    # 而 POST/PUT（申请、改额度）指向新的应用申请入口。
    #
    # 为什么必须停：一个 developer token 能按 QQ 号读全库任意用户的成绩，
    # 用户从未对某个 bot 做过授权，也无从撤销。新模型下第三方拿到的是
    # 「某个用户授权我读他的成绩」，范围只减不增。
    if request.method in ('POST', 'PUT'):
        return {
            "message": "开发者 token 已停止申请，请改为申请「应用」："
                       f"{APPLICATION_DOC_URL}",
            "migration": APPLICATION_DOC_URL,
        }, 410

    if request.method == 'GET': # get all tokens of this account
        res = []
        for developer in await NewDeveloper.select().where(NewDeveloper.player == g.user).aio_execute():
            res.append({
                'token': developer.token,
                # 'reason': developer.reason,
                # 'pic': json.loads(developer.pic),
                'level': developer.level,
                'available': developer.available,
                'comment': developer.comment,
                # 这个 token 哪天停。GET 之所以留着就是为了让存量开发者看到
                # 自己手上 token 的状态，日落时间是眼下最要紧的那一项；
                # 单独续期过的人在这里能看到自己那个日期，不是全局的
                'sunset': developer_token_sunset_ts(developer),
                'migration': MIGRATION_DOC_URL,
            })
        return res
    elif request.method == 'POST': # create a new token for this account
        body = await request.json
        for developer in await NewDeveloper.select().where(NewDeveloper.player == g.user).aio_execute():
            if not developer.available:
                return {"message": "目前用户已有申请中的 token，请联系水鱼处理后再重新申请"}, 400
            
        if g.user.bind_qq == "":
            return {"message": "请先绑定 QQ 以查收邮件"}, 400

        try:
            if body['level'] not in [0, 1, 2, 3, 4]:
                return {"message": "无效 Level"}, 400

            if 'token' in body and body['token'] != '': # migrate from legacy developer token
                try:
                    developer = await Developer.aio_get(Developer.token == body['token'])
                    await NewDeveloper.aio_create(
                        player=g.user,
                        token=body['token'],
                        reason=body['reason'],
                        pic=json.dumps(body['pic']), # base64 image list
                        level=body['level'],
                        available=False,
                        confirm_token='',
                        comment=''
                    )
                except Exception:
                    return {"message": "不存在此旧 Token！"}, 400
            else:
                await NewDeveloper.aio_create(
                    player=g.user,
                    token=''.join(random.sample(string.digits + string.ascii_letters, 32)),
                    reason=body['reason'],
                    pic=json.dumps(body['pic']), # base64 image list
                    level=body['level'],
                    available=False,
                    confirm_token='',
                    comment=''
                )
            return {"message": "ok"}, 200
        except Exception:
            return {"message": "请求无效"}, 400
    elif request.method == 'PUT': # change token level of this account
        body = await request.json
        try:
            if body['level'] not in [0, 1, 2, 3, 4]:
                return {"message": "无效 Level"}, 400
            
            developer = await NewDeveloper.aio_get((NewDeveloper.token == body['token']) & (NewDeveloper.player == g.user))
            developer.level = body['level']
            developer.reason = body['reason']
            developer.pic = json.dumps(body['pic'])
            developer.available = False
            developer.confirm_token = ''
            await developer.aio_save()

            return {"message": "ok"}, 200
        except Exception:
            return {"message": "请求无效"}, 400


@app.route('/dev/token_activate')
async def token_activate():
    try:
        token = request.args.get('token', default='')
        if token == '':
            raise Exception()
        developer: NewDeveloper = await NewDeveloper.aio_get(NewDeveloper.confirm_token == token)
        developer.confirm_token = ''
        developer.available = True
        await developer.aio_save()
        return "Token 激活完成", 200
    except Exception:
        return "", 405
