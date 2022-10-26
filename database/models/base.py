import json
import time
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
    plate = CharField()
    privacy = BooleanField()
    user_id = IntegerField()
    user_data = TextField()


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