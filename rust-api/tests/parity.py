"""Compare Rust and Python using a disposable account. Credentials never leave memory.

Requires the existing database/venv Python environment. Creates and finally deletes
one temporary player and a few records. OAuth tokens are read-only, scoped to that
account, and expire after five minutes. No existing user's privacy/data is modified.
"""
import argparse
import json
import os
import secrets
import time
from pathlib import Path
from urllib.parse import urlparse, unquote

import httpx
import jwt
import pymysql
from jwt.algorithms import RSAAlgorithm

ROOT = Path(__file__).resolve().parents[2]


def connect(config):
    parsed = urlparse(config['mysql_url'])
    return pymysql.connect(host=parsed.hostname, port=parsed.port or 3306,
                           user=unquote(parsed.username or ''), password=unquote(parsed.password or ''),
                           database=parsed.path.lstrip('/'), charset='utf8mb4', autocommit=True,
                           cursorclass=pymysql.cursors.DictCursor, connect_timeout=5, read_timeout=15)


def create_player(connection, username, import_token):
    with connection.cursor() as cursor:
        cursor.execute('SHOW COLUMNS FROM player')
        fields = cursor.fetchall()
        values = {}
        for field in fields:
            name, kind = field['Field'], field['Type'].lower()
            if name == 'id':
                continue
            values[name] = 0 if any(word in kind for word in ('int', 'double', 'float', 'decimal')) else ''
        values.update(username=username, nickname='Rust 兼容测试', import_token=import_token,
                      accept_agreement=1, user_general_data='{"benchmark":true}')
        columns = ','.join(f'`{name}`' for name in values)
        cursor.execute(f"INSERT INTO player ({columns}) VALUES ({','.join(['%s'] * len(values))})", tuple(values.values()))
        player_id = cursor.lastrowid
        cursor.execute('SELECT c.id FROM chart c JOIN music m ON m.id=c.music_id '
                       'WHERE c.ds>10 AND m.id<100000 ORDER BY c.id LIMIT 5')
        charts = cursor.fetchall()
        for index, chart in enumerate(charts):
            cursor.execute('INSERT INTO newrecord (player_id,chart_id,achievements,dxScore,fc,fs) '
                           'VALUES (%s,%s,%s,%s,%s,%s)',
                           (player_id, chart['id'], [97.1234, 99.9999, 100.4999, 100.5, 80][index],
                            1234 + index, ['fc', '', 'ap', 'app', ''][index], ''))
        return player_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rust', default='http://127.0.0.1:8345')
    parser.add_argument('--python', default='http://127.0.0.1:8333')
    parser.add_argument('--public', action='append', default=[])
    args = parser.parse_args()
    config = json.loads((ROOT / 'database/config.json').read_text())
    connection = connect(config)
    tag = secrets.token_hex(6)
    username, import_token = '__rustcheck_' + tag, secrets.token_urlsafe(32)
    player_id = None
    checks = 0
    client_id = '__rustcheck_' + tag
    quota_keys = []
    developer_token = os.environ.get('PARITY_DEVELOPER_TOKEN')

    try:
        player_id = create_player(connection, username, import_token)
        cookie = jwt.encode({'username': username, 'exp': int(time.time()) + 300},
                            config['jwt_secret'], algorithm='HS256')
        cookie_headers = {'Cookie': 'jwt_token=' + cookie}
        import_headers = {'Import-Token': import_token}
        key_doc = json.loads((ROOT / 'diving-fish-auth/keys/jwks.json').read_text())
        key_data = next(key for key in key_doc['keys'] if key['kid'] == key_doc['active'])
        signing_key = RSAAlgorithm.from_jwk(json.dumps(key_data))
        issuer = config['idp']['issuer'].rstrip('/')
        audience = config['idp'].get('resource') or 'https://www.diving-fish.com/api/maimaidxprober'

        def bearer(**overrides):
            claims = {'iss': issuer, 'aud': audience, 'sub': str(player_id),
                      'exp': int(time.time()) + 300, 'iat': int(time.time()),
                      'scope': 'prober.records.read', 'client_id': client_id,
                      'df_quota': {'u': 10000, 'c': 10000}}
            claims.update(overrides)
            token = jwt.encode(claims, signing_key, algorithm='RS256', headers={'kid': key_doc['active']})
            return {'Authorization': 'Bearer ' + token}

        targets = [('rust', args.rust)] + [('public', base) for base in args.public]
        with httpx.Client(trust_env=False, timeout=40) as client:
            def compare(label, method, path, expected=200, cookie_expected=False, **kwargs):
                nonlocal checks
                client.cookies.clear()
                reference = client.request(method, args.python + path, **kwargs)
                assert reference.status_code == expected, f'{label}: Python status {reference.status_code}'
                for name, base in targets:
                    client.cookies.clear()
                    response = client.request(method, base + path, **kwargs)
                    assert response.status_code == reference.status_code, f'{label}: {name} status {response.status_code}'
                    if method != 'HEAD' and method != 'OPTIONS':
                        assert response.json() == reference.json(), (f'{label}: {name} JSON differs' + (f' Python={reference.json()} Rust={response.json()}' if expected >= 400 else ''))
                    has_cookie = 'jwt_token=' in response.headers.get('set-cookie', '')
                    assert has_cookie == cookie_expected, f'{label}: unexpected session cookie behavior'
                    for header in ['sunset', 'deprecation', 'link']:
                        assert response.headers.get(header) == reference.headers.get(header), f'{label}: {header} differs'
                    if name == 'public':
                        assert response.headers.get('x-prober-backend') == 'rust', f'{label}: public traffic did not reach Rust'
                    checks += 1
                print('PASS', label, flush=True)

            compare('missing auth', 'GET', '/player/records', expected=403)
            compare('invalid import token', 'GET', '/player/records', expected=400, headers={'Import-Token':'__invalid__'})
            compare('malformed bearer takes precedence', 'GET', '/player/records', expected=401,
                    headers={**import_headers, 'Authorization':'Bearer broken'})
            compare('invalid cookie', 'GET', '/player/records', expected=403, headers={'Cookie':'jwt_token=broken'})
            compare('import token records', 'GET', '/player/records', headers=import_headers)
            compare('cookie records and renewal', 'GET', '/player/records', headers=cookie_headers, cookie_expected=True)
            compare('oauth records', 'GET', '/player/records', headers=bearer())
            compare('oauth wrong audience', 'GET', '/player/records', expected=401, headers=bearer(aud='other-resource'))
            compare('oauth wrong issuer', 'GET', '/player/records', expected=401, headers=bearer(iss='https://invalid.example'))
            compare('oauth expired', 'GET', '/player/records', expected=401, headers=bearer(exp=int(time.time()) - 20))
            compare('oauth missing scope', 'GET', '/player/records', expected=403, headers=bearer(scope='openid'))
            compare('oauth unknown user', 'GET', '/player/records', expected=400, headers=bearer(sub='-1'))

            queries = [
                'ds=10..15', 'achievements=99..100.5', 'fc=', 'fc=ap,app',
                'music_id=1&id=2&song_id=3', 'difficulty=3,4', 'is_new=false',
                'type=dx&level=14', 'plate=真将', 'plate=舞舞舞',
                'plate=舞&version=maimai', 'rate=sss,sssp', 'unknown=ignored',
                'dx_score=1234..1235', 'ds=10..,15', 'ds=1_0..15',
            ]
            for query in queries:
                compare('filter ' + query, 'GET', '/player/records?' + query, headers=import_headers)
            for query in ['ds=..', 'ds=15..10', 'ds=abc', 'is_new=maybe', 'plate=不存在', 'ds=1__0']:
                compare('invalid filter ' + query, 'GET', '/player/records?' + query, expected=400, headers=import_headers)
            compare('HEAD', 'HEAD', '/player/records', headers=import_headers)
            compare('OPTIONS', 'OPTIONS', '/player/records')
            compare('B40', 'POST', '/query/player', json={'username':username})
            compare('B50 presence semantics', 'POST', '/query/player', json={'username':username,'b50':False})
            compare('B50', 'POST', '/query/player', json={'username':username,'b50':True})
            compare('unknown query user', 'POST', '/query/player', expected=400, json={'username':'__not_existing_rustcheck__'})
            compare('oauth ignores requested username', 'POST', '/query/player', headers=bearer(), json={'username':'other','b50':True})

            with connection.cursor() as cursor:
                cursor.execute('UPDATE player SET mask=1,privacy=1 WHERE id=%s', (player_id,))
            compare('private public lookup denied', 'POST', '/query/player', expected=403, json={'username':username,'b50':True})
            compare('private owner cookie allowed', 'POST', '/query/player', headers=cookie_headers, json={'username':username,'b50':True})
            compare('owner import remains unmasked', 'GET', '/player/records', headers=import_headers)
            compare('oauth applies mask', 'GET', '/player/records', headers=bearer())
            compare('oauth filters masked values', 'GET', '/player/records?achievements=97.1234', headers=bearer())
            compare('oauth masked B50', 'POST', '/query/player', headers=bearer(), json={'b50':True})

            if developer_token:
                dev_headers = {'developer-token': developer_token}
                compare('developer private user denied', 'GET', '/dev/player/records?username='+username, expected=403, headers=dev_headers)
                with connection.cursor() as cursor:
                    cursor.execute('UPDATE player SET privacy=0 WHERE id=%s', (player_id,))
                compare('developer masked list', 'GET', '/dev/player/records?username='+username, headers=dev_headers)
                compare('developer DivingFish list', 'GET', '/dev/player/records?username=DivingFish', headers=dev_headers)
            compare('developer missing token', 'GET', '/dev/player/records?username='+username, expected=400)
            compare('developer invalid token', 'GET', '/dev/player/records?username='+username, expected=400, headers={'developer-token':'__invalid__'})

            with connection.cursor() as cursor:
                cursor.execute('UPDATE player SET accept_agreement=0 WHERE id=%s', (player_id,))
            compare('oauth agreement enforced', 'GET', '/player/records', expected=403, headers=bearer())
            compare('owner import agreement bypass preserved', 'GET', '/player/records', headers=import_headers)

            # Match the actual nullable schema, including older imported accounts.
            with connection.cursor() as cursor:
                cursor.execute('UPDATE player SET nickname=NULL,plate=NULL,additional_rating=NULL,'
                               'maimai_legacy_count=NULL,maimai_new_count=NULL,privacy=NULL,mask=NULL,'
                               'access_time=NULL,user_general_data=NULL,accept_agreement=1 WHERE id=%s', (player_id,))
            compare('historical NULL fields records', 'GET', '/player/records', headers=import_headers)
            compare('historical NULL fields B50', 'POST', '/query/player', json={'username':username,'b50':True})
            with connection.cursor() as cursor:
                cursor.execute('UPDATE player SET accept_agreement=NULL WHERE id=%s', (player_id,))
            compare('NULL agreement oauth denied', 'GET', '/player/records', expected=403, headers=bearer())

            # Distinct quota client isolates this test from all actual applications.
            limited_client = client_id + '_limited'
            limited = bearer(client_id=limited_client, df_quota={'u':1,'c':10})
            with connection.cursor() as cursor:
                cursor.execute('UPDATE player SET accept_agreement=1 WHERE id=%s', (player_id,))
            day = time.strftime('%Y%m%d', time.gmtime())
            import redis
            redis_client = redis.Redis(host='127.0.0.1',port=6379,db=0)
            limited_keys = [f'prober:oauth:q:u:{limited_client}:{player_id}:{day}', f'prober:oauth:q:c:{limited_client}:{day}']
            quota_keys.extend(limited_keys)
            for name, base in targets:
                redis_client.delete(*limited_keys)
                client.cookies.clear()
                assert client.get(base+'/player/records',headers=limited).status_code == 200
                assert client.get(base+'/player/records',headers=limited).status_code == 429
                checks += 2
            quota_keys.extend([f'prober:oauth:q:u:{client_id}:{player_id}:{day}', f'prober:oauth:q:c:{client_id}:{day}'])
            print('PASS OAuth quota enforced',flush=True)
            print(f'All {checks} checks passed; no proxy used',flush=True)
    finally:
        if player_id is not None:
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM newrecord WHERE player_id=%s',(player_id,))
                cursor.execute('DELETE FROM player WHERE id=%s AND username=%s',(player_id,username))
        connection.close()
        try:
            import redis
            client = redis.Redis(host='127.0.0.1',port=6379,db=0)
            for key in client.scan_iter(match=f'prober:oauth:q:*:__rustcheck_{tag}*'):
                client.delete(key)
        except Exception:
            pass
        print('Temporary account and records removed',flush=True)


if __name__ == '__main__':
    main()
