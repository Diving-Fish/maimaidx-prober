import json
import time
import jwt


with open('config.json', encoding='utf-8') as f:
    config = json.load(f)
    secret_key = config["jwt_secret"]
    f.close()


def ts(offset: int = 0):
    return int(time.time() + offset)


def username_encode(username: str):
    data = jwt.encode({'username': username, 'exp': ts(86400)}, secret_key, algorithm='HS256')
    return data


def decode(jwt_str: str):
    try:
        return jwt.decode(jwt_str, secret_key, algorithms=['HS256'])
    except jwt.exceptions.DecodeError:
        return {}
