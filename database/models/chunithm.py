from math import floor
from models.base import *


class ChuniMusic(BaseModel):
    id = IntegerField(primary_key=True)
    title = CharField()
    artist = CharField()
    genre = CharField()
    version = CharField()
    bpm = IntegerField()


class ChuniChart(BaseModel):
    music = ForeignKeyField(ChuniMusic)
    level = IntegerField()
    difficulty = CharField()
    combo = IntegerField()
    ds = DoubleField()
    charter = CharField()


class ChuniRecord(BaseModel):
    player = ForeignKeyField(Player)
    chart = ForeignKeyField(ChuniChart)
    score = IntegerField()
    fc = CharField()
    recent = BooleanField()


db.create_tables([ChuniMusic, ChuniChart, ChuniRecord])


def chuni_music_data():
    data = []
    dct = None
    music = ChuniMusic.select(ChuniMusic, ChuniChart).join(ChuniChart)
    prev_music_id = 0
    for m in music:
        m: ChuniMusic
        if m.id != prev_music_id:
            if dct:
                data.append(dct)
            prev_music_id = m.id
            value = vars(m)['__data__']
            dct = {
                "id": value["id"],
                "title": value["title"],
                "ds": [],
                "level": [],
                "cids": [],
                "charts": [],
                "basic_info": {
                    "title": value["title"],
                    "artist": value["artist"],
                    "genre": value["genre"],
                    "bpm": value["bpm"],
                    "from": value["version"],
                }
            }
        c: ChuniChart = m.chunichart
        dct['cids'].append(c.get_id())
        dct['ds'].append(c.ds)
        dct['level'].append(c.difficulty)
        dct['charts'].append({
            'combo': c.combo, "charter": c.charter
        })
    data.append(dct)
    return data