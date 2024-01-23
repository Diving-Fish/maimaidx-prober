import asyncio
import random
import string
from app import app, login_required, mail_config, md5, developer_required
from quart import Quart, request, g, make_response
from tools._jwt import *
from models.maimai import *
from tools.mail import *


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
        a.save(force_insert=True)
    return await message_resp()


@app.route("/feedback", methods=['POST'])
async def feedback():
    j = await request.get_json()
    FeedBack.insert(j).execute()
    return {"message": "提交成功"}


@app.route("/login", methods=['POST'])
async def login():
    j = await request.get_json()
    username = j["username"]
    password = j["password"]
    try:
        user: Player = Player.get(Player.username == username)
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
    player = Player.select().where(Player.username == j["username"])
    if player.exists():
        return {
            "errcode": -1,
            "message": "此用户名已存在",
        }, 400
    salt = ''.join(random.sample(string.ascii_letters + string.digits, 16))
    Player.create(username=j["username"], salt=salt,
                  password=md5(j["password"] + salt))
    resp = await make_response({"message": "注册成功"})
    resp.set_cookie('jwt_token', username_encode(j["username"]))
    return resp


@app.route("/player/change_password", methods=['POST'])
@login_required
async def change_password():
    password = (await request.json)["password"]
    # if len(password) >= 30:
    #     return {"message": "密码不能大于30位"}, 400
    g.user.password = md5(password + g.user.salt)
    g.user.save()
    return {"message": "success"}


@app.route("/recovery", methods=['POST'])
async def recovery():
    qq = request.args.get("qq", type=str, default="")
    try:
        player = Player.get(Player.bind_qq == qq)
    except Exception:
        return {"message": "重置邮件已发送到您的QQ邮箱，请按照指引进行操作"}
    ts = int(time.time())
    try:
        email_reset: EmailReset = EmailReset.get((EmailReset.player == player) & (EmailReset.timeout_stamp > ts))
        random_token = email_reset.token
    except Exception:
        random_token = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(128)])
        EmailReset.create(player=player, token=random_token, timeout_stamp=1800 + int(ts))
    asyncio.create_task(send_mail(
        payload={
            "sender": "舞萌 DX 查分器",
            "to": f"{qq}@qq.com",
            "body": f"""<p>请点击此链接来设置您的查分器账户：<a href="https://www.diving-fish.com/maimaidx/recovery?token={random_token}">网页链接</a></p>
<p>该链接将在 30 分钟内有效，过期请重新申请。</p>""",
            "subject": "舞萌 DX 查分器账户重置",
            "type": "html"
        },
        mail_config=mail_config
    ))
    return {"message": "重置邮件已发送到您的QQ邮箱，请按照指引进行操作"}


@app.route("/do_recovery", methods=['GET', 'POST'])
async def do_recovery():
    token = request.args.get("token", type=str, default="")
    ts = int(time.time())
    try:
        email_reset: EmailReset = EmailReset.get((EmailReset.token == token) & (EmailReset.timeout_stamp > ts))
    except Exception:
        return {"message": "此链接无效或已过期"}, 400
    if request.method == "GET":
        p: Player = email_reset.player
        return {"username": p.username}
    else:
        p: Player = email_reset.player
        j = await request.json
        if j["operation"] == "unbind_qq":
            p.bind_qq = ""
        elif j["operation"] == "reset_password":
            p.password = md5(j["password"] + p.salt)
        p.save()
        email_reset.timeout_stamp = 0;
        email_reset.save()
        return {"message": "success"}


@app.route('/channel_to_qq', methods=['GET', 'POST'])
@developer_required
async def channel_to_qq():
    cuid = request.args.get("cuid", type=str, default="")
    if request.method == 'GET':
        try:
            player = Player.get(Player.qq_channel_uid == cuid)
        except Exception:
            return {"qq": ""}
        return {"qq": player.bind_qq}
    else:
        qq = (await request.json)["qq"]
        try:
            player = Player.get(Player.qq_channel_uid == cuid)
        except Exception:
            try:
                player = Player.get(Player.bind_qq == qq)
            except Exception:
                return {"message": "failed"}, 400
        player.qq_channel_uid = cuid
        player.bind_qq = qq
        player.save()
        return {"message": "success"}

@app.route('/token_available', methods=['GET'])
async def token_available():
    t = request.args.get('token', type=str, default='')
    if t == "":
        return {"message": "non-exist"}, 404
    try:
        player = Player.get(Player.import_token == t)
        return {"message": "ok"}, 200
    except Exception:
        return {"message": "non-exist"}, 404
