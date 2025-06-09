from app import app, ci_access_required, mail_config
from quart import Quart, request, g, make_response
import json
import asyncio
import random
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


find_root = '''location /maimaidx/prober/ {
        proxy_pass http://localhost:8080/;
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
            await run_command("sudo systemctl restart nginx")
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
            await run_command("sudo systemctl restart nginx")
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
                res.append({
                    'username': player.username,
                    'token': developer.token,
                    # 'reason': developer.reason,
                    # 'pic': json.loads(developer.pic),
                    'level': developer.level,
                    'available': developer.available or developer.confirm_token != '',
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
                player: Player = developer.player
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
        developer.bind_qq = developer.player.bind_qq
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
