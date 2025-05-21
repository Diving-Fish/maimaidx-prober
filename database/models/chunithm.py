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


md_cache = chuni_music_data()
md_map = {}
md_title_map = {}
md_title_we_map = {}
chart_id_map = {}
for music in md_cache:
    md_map[music['id']] = music
    if music['id'] >= 8000:
        md_title_we_map[music['title']] = music
    else:
        md_title_map[music['title']] = music
    for i, cid in enumerate(music['cids']):
        chart_id_map[cid] = (i, music)


def lerp(x1, x2, y1, y2, x):
    val = (x - x1) / (x2 - x1) * (y2 - y1) + y1
    val = floor(val * 100) / 100
    return val


def single_ra(record: ChuniRecord):
    score = record.score
    level, music = chart_id_map[record.chart_id]
    ds = music['ds'][level]
    if score < 500000:
        return 0.0
    elif score < 800000:
        return max(0, lerp(500000, 800000, 0, (ds - 5) / 2, score))
    elif score < 900000:
        return max(0, lerp(800000, 900000, (ds - 5) / 2, ds - 5, score))
    elif score < 925000:
        return max(0, lerp(900000, 925000, ds - 5, ds - 3, score))
    elif score < 975000:
        return max(0, lerp(925000, 975000, ds - 3, ds, score))
    elif score < 1000000:
        return lerp(975000, 1000000, ds, ds + 1, score)
    elif score < 1005000:
        return lerp(1000000, 1005000, ds + 1, ds + 1.5, score)
    elif score < 1007500:
        return lerp(1005000, 1007500, ds + 1.5, ds + 2, score)
    elif score < 1009000:
        return lerp(1007500, 1009000, ds + 2, ds + 2.15, score)
    else:
        return ds + 2.15


def record_json(record: ChuniRecord):
    level, music = chart_id_map[record.chart_id]
    return {
        "mid": music["id"],
        "cid": music["cids"][level],
        "title": music["title"],
        "level_index": level,
        "level_label": ["Basic", "Advanced", "Expert", "Master", "Ultima", "World's End"][level],
        "level": music["level"][level],
        "score": record.score,
        "fc": record.fc,
        "ra": single_ra(record),
        "ds": music["ds"][level]
    }
