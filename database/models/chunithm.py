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

# 页面解析出来的 fc 图标名，也是库里实际存在的全部取值
CHUNI_FC_VALUES = ("", "fullcombo", "alljustice", "fullchain", "fullchain2")

MAX_CHUNI_SCORE = 1010000


def std_chuni_fc(fc: str):
    """把上传上来的 fc 归一到已知取值，认不出当作没有。"""
    if not isinstance(fc, str):
        return ""
    fc = fc.strip().lower()
    if fc in CHUNI_FC_VALUES:
        return fc
    # 常见的等价写法
    return {"fc": "fullcombo", "aj": "alljustice", "full combo": "fullcombo",
            "all justice": "alljustice"}.get(fc, "")


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