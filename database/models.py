import json
from typing import List, Optional, Dict

from peewee import *
from playhouse.db_url import connect

with open('config.json', encoding='utf-8') as fr:
    config = json.load(fr)
    mysql_url = config["mysql_url"]

db = connect(mysql_url)


class BaseModel(Model):
    class Meta:
        database = db


class Music(BaseModel):
    id = CharField(primary_key=True)
    title = CharField()
    type = CharField()
    artist = CharField()
    genre = CharField()
    bpm = IntegerField()
    release_date = CharField()
    version = CharField()
    version_cn = CharField()
    is_new = BooleanField()


class Chart(BaseModel):
    music = ForeignKeyField(Music)
    level = IntegerField()
    difficulty = CharField()
    tap_note = IntegerField()
    hold_note = IntegerField()
    slide_note = IntegerField()
    touch_note = IntegerField()
    break_note = IntegerField()
    ds = DoubleField()
    charter = CharField()


class Player(BaseModel):
    username = CharField()
    password = CharField()
    salt = CharField()
    rating = IntegerField()
    additional_rating = IntegerField()
    nickname = CharField()
    bind_qq = CharField()
    privacy = BooleanField()


class Record(BaseModel):
    player = ForeignKeyField(Player)
    title = CharField()
    level = CharField()
    level_index = IntegerField()
    type = CharField()
    achievements = DoubleField()
    dxScore = IntegerField()
    rate = CharField()
    fc = CharField()
    fs = CharField()
    ds = DoubleField()
    level_label = CharField()
    ra = IntegerField()

    def json(self, md: Optional[List] = None):
        data = {
            "title": self.title,
            "level": self.level,
            "level_index": self.level_index,
            "level_label": self.level_label,
            "type": self.type,
            "dxScore": self.dxScore,
            "achievements": self.achievements,
            "rate": self.rate,
            "fc": self.fc,
            "fs": self.fs,
            "ra": self.ra,
            "ds": self.ds
        }
        if md:
            for m in md:
                if m['title'] == self.title:
                    data["song_id"] = m['id']
                    break
        return data

    def json_output(self):
        return {
            "title": self.title,
            "level": self.level,
            "level_index": self.level_index,
            "type": self.type,
            "dxScore": self.dxScore,
            "achievements": self.achievements,
            "rate": self.rate,
            "fc": self.fc,
            "fs": self.fs
        }


class FeedBack(BaseModel):
    message = TextField()


class Views(BaseModel):
    prober = IntegerField()


class Message(BaseModel):
    text = CharField()
    player = ForeignKeyField(Player)
    nickname = CharField()
    ts = IntegerField()


db.create_tables([Music, Chart, Player, Record, FeedBack, Views, Message])
