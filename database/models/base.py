import json
import time
import hashlib
from typing import List, Optional, Dict, Text, Union, Any, Tuple

from peewee import Model, CharField, IntegerField, BigIntegerField, BooleanField, ForeignKeyField, DoubleField, TextField
from playhouse.db_url import connect

with open('config.json', encoding='utf-8') as fr:
    config = json.load(fr)
    mysql_url = config["mysql_url"]

db = connect(mysql_url)


class BaseModel(Model):
    class Meta:
        database = db


class RequestLog(BaseModel):
    year = IntegerField()
    month = IntegerField()
    day = IntegerField()
    hour = IntegerField()
    path = CharField()
    times = IntegerField()


class Player(BaseModel):
    username = CharField()
    password = CharField()
    salt = CharField()
    rating = IntegerField()
    additional_rating = IntegerField()
    chuni_rating = DoubleField()
    nickname = CharField()
    bind_qq = CharField()
    qq_channel_uid = CharField()
    plate = CharField()
    privacy = BooleanField()
    mask = BooleanField()
    accept_agreement = BooleanField()
    user_id = IntegerField()
    user_data = TextField()
    user_general_data = TextField()
    access_time = BigIntegerField()
    import_token = CharField()

    def user_json(self):
        try:
            j = json.loads(self.user_general_data)
        except Exception:
            j = None
        return {
            "username": self.username,
            "nickname": self.nickname,
            "additional_rating": self.additional_rating,
            "bind_qq": self.bind_qq,
            "qq_channel_uid": self.qq_channel_uid,
            "privacy": self.privacy,
            "mask": self.mask,
            "accept_agreement": self.accept_agreement,
            "plate": self.plate,
            "user_general_data": j,
            "import_token": self.import_token
        }

    def generate_import_token(self):
        self.import_token = hashlib.sha512((self.username + str(time.time())).encode()).hexdigest()
        self.save()
        return self.import_token

    @staticmethod
    def by_qq(qq):
        fail1 = False
        fail2 = False
        try:
            player = Player.get(Player.bind_qq == qq)
            return player
        except Exception:
            fail1 = True
        try:
            player = Player.get(Player.qq_channel_uid == qq)
            return player
        except Exception:
            fail2 = True
        if fail1 and fail2:
            raise Exception("Player not found")
        return None


class Developer(BaseModel):
    nickname = CharField()
    token = CharField()
    reason = TextField()
    available = BooleanField()


class DeveloperLog(BaseModel):
    developer = ForeignKeyField(Developer)
    function = CharField()
    remote_addr = CharField()
    timestamp = DoubleField()


class FeedBack(BaseModel):
    message = TextField()


class Views(BaseModel):
    prober = IntegerField()


class Message(BaseModel):
    text = CharField()
    player = ForeignKeyField(Player)
    nickname = CharField()
    ts = IntegerField()


class EmailReset(BaseModel):
    # class for reset username and password.
    player = ForeignKeyField(Player)
    token = CharField()
    timeout_stamp = BigIntegerField()

    def timeout(self):
        return int(time.time()) > self.timeout_stamp

    def reset(self):
        self.timeout_stamp = 4102444800