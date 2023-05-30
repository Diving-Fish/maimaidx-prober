from app import app, ci_access_required
from quart import Quart, request, g, make_response
import json
import asyncio
import random

IMAGE_NAME = "divingfish/maimaidx-prober"
ci_status = ...

with open('ci_status.json') as f:
    ci_status = json.load(f)

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
    return await make_response(ci_status, 200)


@app.route("/ci/production", methods=['GET'])
@ci_access_required
async def prod():
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
