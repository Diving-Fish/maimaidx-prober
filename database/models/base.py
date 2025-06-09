import json
import time
import hashlib
from typing import List, Optional, Dict, Text, Union, Any, Tuple

from peewee import Model, CharField, IntegerField, BigIntegerField, BooleanField, BlobField, ForeignKeyField, DoubleField, TextField, CompositeKey, chunked, Node, Case
from peewee_async import AioModel, PooledMySQLDatabase
from playhouse.db_url import parse

with open('config.json', encoding='utf-8') as fr:
    config = json.load(fr)
    mysql_url = config["mysql_url"]

db_params = parse(mysql_url)
db = PooledMySQLDatabase(**db_params)

class BaseModel(AioModel):
    class Meta:
        database = db

    @classmethod
    async def aio_bulk_update(cls, model_list, fields, batch_size=None):
        if isinstance(cls._meta.primary_key, CompositeKey):
            raise ValueError('bulk_update() is not supported for models with '
                             'a composite primary key.')

        # First normalize list of fields so all are field instances.
        fields = [cls._meta.fields[f] if isinstance(f, str) else f
                  for f in fields]
        # Now collect list of attribute names to use for values.
        attrs = [field.object_id_name if isinstance(field, ForeignKeyField)
                 else field.name for field in fields]

        if batch_size is not None:
            batches = chunked(model_list, batch_size)
        else:
            batches = [model_list]

        n = 0
        pk = cls._meta.primary_key

        for batch in batches:
            id_list = [model._pk for model in batch]
            update = {}
            for field, attr in zip(fields, attrs):
                accum = []
                for model in batch:
                    value = getattr(model, attr)
                    if not isinstance(value, Node):
                        value = field.to_value(value)
                    accum.append((pk.to_value(model._pk), value))
                case = Case(pk, accum)
                update[field] = case

            n += await (cls.update(update)
                  .where(cls._meta.primary_key.in_(id_list))
                  .aio_execute())
        return n


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
    chuni_access_time = BigIntegerField()
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

    async def generate_import_token(self):
        self.import_token = hashlib.sha512((self.username + str(time.time())).encode()).hexdigest()
        await self.aio_save()
        return self.import_token

    @staticmethod
    async def by_qq(qq):
        fail1 = False
        fail2 = False
        try:
            player = await Player.aio_get(Player.bind_qq == qq)
            return player
        except Exception:
            fail1 = True
        try:
            player = await Player.aio_get(Player.qq_channel_uid == qq)
            return player
        except Exception:
            fail2 = True
        if fail1 and fail2:
            raise Exception("Player not found")
        return None
    

class NewDeveloper(BaseModel):
    player = ForeignKeyField(Player)
    token = CharField()
    reason = TextField()
    pic = TextField()
    level = IntegerField() # 0: unavailable, 1: <300/day, 2: 300~1000/day, 3: 1000~3000/day, 4: 3000~10000/day
    available = BooleanField()
    bind_qq = CharField()
    confirm_token = CharField()
    comment = CharField()


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


class NewDeveloperLog(BaseModel):
    developer = ForeignKeyField(NewDeveloper)
    function = CharField()
    remote_addr = CharField()
    timestamp = DoubleField()
    request_args = TextField()
    request_body = TextField()


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