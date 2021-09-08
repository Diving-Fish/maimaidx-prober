import json
import time
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


class NewRecord(BaseModel):
    # A new, robust store strategy for record.
    # Maybe you need query and join it with other table?
    player = ForeignKeyField(Player)
    chart = ForeignKeyField(Chart)
    achievements = DoubleField()
    dxScore = IntegerField()
    fc = CharField()
    fs = CharField()


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


db.create_tables([Music, NewRecord, Chart, Player, Record, FeedBack, Views, Message])


def get_idx(achievements):
    t = (50, 60, 70, 75, 80, 90, 94, 97, 98, 99, 99.5, 100, 100.5, 200)
    for i in range(len(t)):
        if achievements < t[i]:
            break
    return i


def get_l(rate):
    return [0, 5, 6, 7, 7.5, 8.5, 9.5, 10.5, 12.5, 12.7, 13, 13.2, 13.5, 14][get_idx(rate)]


def get_rate(rate):
    return ["d", "c", "b", "bb", "bbb", "a", "aa", "aaa", "s", "sp", "ss", "ssp", "sss", "sssp"][get_idx(rate)]


def record_json(record: NewRecord):
    data = {
        "title": record.title,
        "level": record.diff,
        "level_index": record.level,
        "level_label": ["Basic", "Advanced", "Expert", "Master", "Re:MASTER"][record.level],
        "type": record.type,
        "dxScore": record.dxScore,
        "achievements": record.achievements,
        "rate": get_rate(record.achievements),
        "fc": record.fc,
        "fs": record.fs,
        "ra": int(get_l(record.achievements) * min(record.achievements, 100.5) * record.ds / 100),
        "ds": record.ds,
        "song_id": record.id
    }
    return data

def record_json_output(record: NewRecord):
    t1 = time.time()
    chart = record.chart
    print(time.time() - t1)
    music = chart.music
    print(time.time() - t1)
    return {
        "title": music.title,
        "level": chart.level,
        "level_index": chart.level,
        "type": music.type,
        "dxScore": record.dxScore,
        "achievements": record.achievements,
        "rate": get_rate(record.achievements),
        "fc": record.fc,
        "fs": record.fs,
    }

def platerecord_json(platerecord: NewRecord):
    data = {
        "id" : platerecord.id,
        "title": platerecord.title,
        "level": platerecord.diff,
        "level_index" : platerecord.level,
        "type" : platerecord.type,
        "achievements": platerecord.achievements,
        "fc" : platerecord.fc,
        "fs" : platerecord.fs
    }
    return data

def music_data():
    data = []
    dct = None
    music = Music.select(Music, Chart).join(Chart)
    prev_music_id = 0
    for m in music:
        m: Music
        if m.id != prev_music_id:
            if dct:
                data.append(dct)
            prev_music_id = m.id
            value = vars(m)['__data__']
            dct = {
                "id": str(value["id"]),
                "title": value["title"],
                "type": value["type"],
                "ds": [],
                "level": [],
                "cids": [],
                "charts": [],
                "basic_info": {
                    "title": value["title"],
                    "artist": value["artist"],
                    "genre": value["genre"],
                    "bpm": value["bpm"],
                    "release_date": value["release_date"],
                    "from": value["version"],
                    "is_new": value["is_new"]
                }
            }
        c: Chart = m.chart
        dct['cids'].append(c.get_id())
        dct['ds'].append(c.ds)
        dct['level'].append(c.difficulty)
        if m.type == 'SD':
            notes = [c.tap_note, c.hold_note, c.slide_note, c.break_note]
        else:
            notes = [c.tap_note, c.hold_note, c.slide_note, c.touch_note, c.break_note]
        dct['charts'].append({
            'notes': notes, "charter": c.charter
        })
    data.append(dct)
    return data


def t_equal(s1, s2):
    return s1.replace(' ', '').replace('\u3000', '') == s2.replace(' ', '').replace('\u3000', '')


def get_music_by_title(md, t, tp):
    for m in md:
        if t_equal(m["title"], t) and m["type"] == tp:
            return m
    return None

def in_or_equal(checker: Any, elem: Optional[Union[Any, List[Any]]]):
        if elem is Ellipsis:
            return True
        if isinstance(elem, List):
            return checker in elem
        elif isinstance(elem, Tuple):
            return elem[0] <= checker <= elem[1]
        else:
            return checker == elem

class recordList(List[NewRecord]):
    def filter(self,
                level: Optional[Union[str, List[str]]] = ...,
                ds: Optional[Union[float, List[float], Tuple[float, float]]] = ...,
                genre: Optional[Union[str, List[str]]] = ...,
                diff: Optional[List[int]] = ...,
                version: Optional[Union[str, List[str]]] = ...,
                ):
        temp = recordList()
        for chart in self:
            if not in_or_equal(chart.level,level):
                continue
            if not in_or_equal(chart.ds,ds):
                continue
            if not in_or_equal(chart.genre,genre):
                continue
            if not in_or_equal(chart.diff,diff):
                continue
            if not in_or_equal(chart.version,version):
                continue
            temp.append(chart)
        return temp
