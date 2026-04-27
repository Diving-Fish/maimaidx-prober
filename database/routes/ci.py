from app import app, ci_access_required, mail_config
from quart import Quart, request, g, make_response
import json
import asyncio
import random
import time
import re
from models.base import *
import string
from tools.mail import send_mail

IMAGE_NAME = "divingfish/maimaidx-prober"
ci_status = ...

def reload_status():
    global ci_status
    with open('ci_status.json') as f:
        ci_status = json.load(f)

reload_status()

def save_status():
    global ci_status
    with open('ci_status.json', 'w') as fw:
        json.dump(ci_status, fw, indent=4)


async def run_command(cmd):
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    return (stdout.decode(), stderr.decode())


async def run_command_with_code(cmd):
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    return (process.returncode, stdout.decode(), stderr.decode())


find_root = '''location /manual {
        alias /var/www/maimaidx/docs;
    }
'''

find_template = '''
    location /maimaidx/prober-test/%s/ {
        proxy_pass http://localhost:%s/;
    }
'''


def add_nginx_conf(sha, port):
    with open('/etc/nginx/conf.d/default.conf', encoding='utf-8') as f:
        val = f.read()
    root_idx = val.find(find_root) + len(find_root)
    val = val[:root_idx] + find_template % (sha, port) + val[root_idx:]
    with open('/etc/nginx/conf.d/default.conf', 'w', encoding='utf-8') as fw:
        fw.write(val)


def del_nginx_conf(sha, port):
    with open('/etc/nginx/conf.d/default.conf', encoding='utf-8') as f:
        val = f.read()
    idx = val.find(find_template % (sha, port))
    val = val[:idx] + val[idx + len(find_template % (sha, port)):]
    with open('/etc/nginx/conf.d/default.conf', 'w', encoding='utf-8') as fw:
        fw.write(val)


def get_available_port():
    l = []
    for k, v in ci_status['active_tests'].items():
        l.append(int(v['port']))
    i = random.randrange(25000, 26000)
    while i in l:
        i = random.randrange(25000, 26000)
    return i


@app.route("/ci/status", methods=['GET'])
@ci_access_required
async def status():
    reload_status()
    return await make_response(ci_status, 200)


@app.route("/ci/production", methods=['GET'])
@ci_access_required
async def prod():
    reload_status()
    sha = request.args.get("sha", type=str, default="")
    s = ci_status["production"]
    if "ps" in s and s["ps"] != "":
        # stop older version
        await run_command(f"docker stop {s['ps']}")
    image_tag = f"{IMAGE_NAME}:{sha}"
    port = 8080
    ot, err = await run_command(f"docker run -d --rm -p {port}:8080 {image_tag}")
    ci_status["production"] = {
        "port": port,
        "image": image_tag,
        "ps": ot.strip()
    }
    save_status()
    return await make_response("OK", 200)


@app.route("/ci/restart_nginx", methods=['POST'])
@ci_access_required
async def restart_nginx():
    stdout, stderr = await run_command("sudo systemctl restart nginx")
    if stderr != "":
        return await make_response(stderr, 500)
    return await make_response(stdout or "OK", 200)


@app.route("/ci/doc_build", methods=['GET'])
@ci_access_required
async def doc_build():
    sha = request.args.get("sha", type=str, default="")
    if sha != "" and re.fullmatch(r"[0-9a-f]{40}", sha) is None:
        return await make_response("Invalid sha", 400)
    checkout_cmd = f"git fetch origin && git restore --source {sha} -- doc" if sha != "" else "git pull --rebase"
    code, stdout, stderr = await run_command_with_code(f"cd .. && {checkout_cmd} && cd doc && bash build.sh")
    if code != 0:
        return await make_response(stdout + stderr, 500)
    return await make_response(stdout or "OK", 200)


@app.route("/ci/tag", methods=['GET', 'DELETE'])
@ci_access_required
async def tag():
    reload_status()
    if request.method == 'GET':
        sha = request.args.get("sha", type=str, default="")
        if sha not in ci_status["active_tests"]:
            image_tag = f"{IMAGE_NAME}:{sha}"
            port = get_available_port()
            ot, err = await run_command(f"docker run -d --rm -p {port}:8080 {image_tag}")
            # print(ot, err)
            # if err != "":
            #     return "ERROR", 400
            ci_status["active_tests"][sha] = {
                "port": port,
                "image": image_tag,
                "ps": ot.strip()
            }
            save_status()
            add_nginx_conf(sha, port)
        return await make_response("OK", 200)
    elif request.method == 'DELETE':
        sha = request.args.get("sha", type=str, default="")
        if sha in ci_status["active_tests"]:
            s = ci_status["active_tests"][sha]
            await run_command(f"docker stop {s['ps']}")
            await run_command(f"docker rmi {s['image']}")
            del ci_status["active_tests"][sha]
            save_status()
            del_nginx_conf(sha, s['port'])
        return await make_response("OK", 200)


@app.route("/ci/developer_token", methods=['GET', 'POST'])
@ci_access_required
async def ci_developer_token():
    if request.method == 'GET':
        token = request.args.get("developer", type=str, default="")
        if token == "":
            res = []
            # return all entries of developer token
            for developer in await NewDeveloper.select().aio_execute():
                player: Player = await Player.aio_get(Player.id == developer.player_id)
                available = 0
                if developer.available:
                    available = 2
                elif developer.confirm_token != '':
                    available = 1
                res.append({
                    'username': player.username,
                    'token': developer.token,
                    'qq': developer.bind_qq,
                    # 'reason': developer.reason,
                    # 'pic': json.loads(developer.pic),
                    'level': developer.level,
                    'available': available,
                    'comment': developer.comment
                })
            return res
        else:
            try:
                try:
                    await Developer.aio_get(Developer.token == token)
                    is_migrate = True
                except Exception:
                    is_migrate = False
                developer: NewDeveloper = await NewDeveloper.aio_get(NewDeveloper.token == token)
                player: Player = await Player.aio_get(developer.player_id == Player.id)
                return {
                    'qq': player.bind_qq,
                    'username': player.username,
                    'token': developer.token,
                    'reason': developer.reason,
                    'pic': json.loads(developer.pic),
                    'level': developer.level,
                    'available': developer.available,
                    'comment': developer.comment,
                    'is_migrate': is_migrate
                }
            except Exception:
                return {}, 400
    if request.method == 'POST':
        j = await request.json
        token = j['token']
        developer: NewDeveloper = await NewDeveloper.aio_get(NewDeveloper.token == token)
        developer.bind_qq = (await Player.aio_get(developer.player_id == Player.id)).bind_qq
        developer.level = j['level']
        developer.comment = j['comment']
        if developer.level > 0: # approved
            developer.confirm_token = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(128)])
            asyncio.create_task(send_mail(
                payload={
                    "sender": "舞萌 DX 查分器",
                    "to": f"{developer.bind_qq}@qq.com",
                    "body": f"""<p>您的开发者 Token 申请已通过，请点击此链接激活您的Token：<a href="https://www.diving-fish.com/api/maimaidxprober/dev/token_activate?token={developer.confirm_token}">网页链接</a></p>
<p>为第一时间同步查分器开发者相关消息，请加入查分器开发者 QQ 群 605800479</p>""",
                    "subject": "舞萌 DX 开发者 Token 申请结果",
                    "type": "html"
                },
                mail_config=mail_config
            ))
        else:
            developer.available = False
            developer.confirm_token = ''
            asyncio.create_task(send_mail(
                payload={
                    "sender": "舞萌 DX 查分器",
                    "to": f"{developer.bind_qq}@qq.com",
                    "body": f"""<p>很遗憾，您的开发者申请未能通过。原因如下：</p>
<p>{developer.comment}</p>
<p>请前往查分器官网尝试重新填写信息后再次申请。""",
                    "subject": "舞萌 DX 开发者 Token 申请结果",
                    "type": "html"
                },
                mail_config=mail_config
            ))
        await developer.aio_save()
        return {"message": "ok"}, 200


@app.route("/ci/generate_reset_link", methods=['GET'])
@ci_access_required
async def generate_reset_link():
    username = request.args.get("username", type=str, default="")
    if username == "":
        return {"message": "用户名不能为空"}, 400
    try:
        player: Player = await Player.aio_get(Player.username == username)
    except Exception:
        return {"message": "用户不存在"}, 404
    ts = int(time.time())
    try:
        email_reset: EmailReset = await EmailReset.aio_get((EmailReset.player == player) & (EmailReset.timeout_stamp > ts))
        email_reset.timeout_stamp = 86400 + ts
        await email_reset.aio_save()
        random_token = email_reset.token
    except Exception:
        random_token = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(128)])
        await EmailReset.aio_create(player=player, token=random_token, timeout_stamp=86400 + ts)
    return {
        "link": f"https://www.diving-fish.com/maimaidx/recovery?token={random_token}",
        "username": player.username,
        "expires_in": 86400
    }
