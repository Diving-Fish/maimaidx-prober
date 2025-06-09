import math
from models.base import *


class Music(BaseModel):
    id = IntegerField(primary_key=True)
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


class NewRecord(BaseModel):
    # A new, robust store strategy for record.
    # Maybe you need query and join it with other table?
    player = ForeignKeyField(Player)
    chart = ForeignKeyField(Chart)
    achievements = DoubleField()
    dxScore = IntegerField()
    fc = CharField()
    fs = CharField()


class VoteResult(BaseModel):
    music_id = CharField()
    down_vote = IntegerField()
    total_vote = IntegerField()


# class RecordAnalysis(BaseModel):
#     chart = ForeignKeyField(Chart)
#     count = IntegerField()
#     avg = DoubleField()
#     avg_dx_score = IntegerField()
#     d_count = IntegerField()
#     c_count = IntegerField()
#     b_count = IntegerField()
#     bb_count = IntegerField()
#     bbb_count = IntegerField()
#     a_count = IntegerField()
#     aa_count = IntegerField()
#     aaa_count = IntegerField()
#     s_count = IntegerField()
#     sp_count = IntegerField()
#     ss_count = IntegerField()
#     ssp_count = IntegerField()
#     sss_count = IntegerField()
#     sssp_count = IntegerField()
#     fc_count = IntegerField()
#     fcp_count = IntegerField()
#     ap_count = IntegerField()
#     app_count = IntegerField()


db.create_tables([Music, NewRecord, Chart, Player, EmailReset,
                 FeedBack, Views, Message, NewDeveloper, Developer, DeveloperLog, NewDeveloperLog, RequestLog, VoteResult])

SCORE_COEFFICIENT_TABLE = [
    [0, 0, 'd'],
    [10, 1.6, 'd'],
    [20, 3.2, 'd'],
    [30, 4.8, 'd'],
    [40, 6.4, 'd'],
    [50, 8.0, 'c'],
    [60, 9.6, 'b'],
    [70, 11.2, 'bb'],
    [75, 12.0, 'bbb'],
    [79.9999, 12.8, 'bbb'],
    [80, 13.6, 'a'],
    [90, 15.2, 'aa'],
    [94, 16.8, 'aaa'],
    [96.9999, 17.6, 'aaa'],
    [97, 20.0, 's'],
    [98, 20.3, 'sp'],
    [98.9999, 20.6, 'sp'],
    [99, 20.8, 'ss'],
    [99.5, 21.1, 'ssp'],
    [99.9999, 21.4, 'ssp'],
    [100, 21.6, 'sss'],
    [100.4999, 22.2, 'sss'],
    [100.5, 22.4, 'sssp']
]

class ScoreCoefficient:
    def __init__(self, achievements):
        for i in range(len(SCORE_COEFFICIENT_TABLE)):
            if i == len(SCORE_COEFFICIENT_TABLE) - 1 or achievements < SCORE_COEFFICIENT_TABLE[i + 1][0]:
                self.r = SCORE_COEFFICIENT_TABLE[i][2]
                self.c = SCORE_COEFFICIENT_TABLE[i][1]
                self.min = SCORE_COEFFICIENT_TABLE[i][0]
                self.a = achievements
                return

    def ra(self, ds):
        return int(self.c * ds * min(100.5, self.a) / 100)


def get_plate_name(version, plate_type):
    return {
        "maimai PLUS": "真",
        "maimai GreeN": "超",
        "maimai GreeN PLUS": "檄",
        "maimai ORANGE": "橙",
        "maimai ORANGE PLUS": "暁",
        "maimai PiNK": "桃",
        "maimai PiNK PLUS": "櫻",
        "maimai MURASAKi": "紫",
        "maimai MURASAKi PLUS": "菫",
        "maimai MiLK": "白",
        "MiLK PLUS": "雪",
        "maimai FiNALE": "輝",
        "ALL FiNALE": "舞",
        "maimai でらっくす": "熊",
        "maimai でらっくす PLUS": "華",
        "maimai でらっくす Splash": "爽",
        "maimai でらっくす Splash PLUS": "煌",
        "maimai でらっくす UNiVERSE": "宙",
        "maimai でらっくす UNiVERSE PLUS": "星",
        "maimai でらっくす FESTiVAL": "祭",
        "maimai でらっくす FESTiVAL PLUS": "祝"
    }[version]+{
        1: "極",
        2: "将",
        4: "舞舞",
        8: "神",
    }[plate_type]


def verify_plate(player, version, plate_type) -> Tuple[bool, str]:
    try:
        if version == "无":
            return True, ""
        plate_name = get_plate_name(version, plate_type)
        if plate_name == "真将":
            return False, ""
        return True, plate_name
    except Exception:
        return False, ""
    

def get_masked_achievement(achievements: float, fc: str, ds: float, sc: ScoreCoefficient, ra: int):
    if achievements >= 100.5:
        if fc == "ap" or fc == "app":
            return 101
        return math.floor(achievements * 10) / 10
    if sc.c == 0:
        return 0
    acc = ra * 100 / sc.c / ds
    if acc < sc.min:
        acc = sc.min
    else:
        acc = math.ceil(acc * 1000) / 1000
    return acc


def record_json(record: NewRecord, masked: bool):
    sc = ScoreCoefficient(record.achievements)
    ra = sc.ra(record.ds)
    data = {
        "title": record.title,
        "level": record.diff,
        "level_index": record.level,
        "level_label": ["Basic", "Advanced", "Expert", "Master", "Re:MASTER"][record.level],
        "type": record.type,
        "dxScore": 0 if masked else record.dxScore,
        "achievements": get_masked_achievement(record.achievements, record.fc, record.ds, sc, ra) if masked else record.achievements,
        "rate": sc.r,
        "fc": record.fc,
        "fs": record.fs,
        "ra": ra,
        "ds": record.ds,
        "song_id": record.id
    }
    if data["song_id"] >= 100000:
        data["ra"] = 0
        data["level_label"] = "Utage"
    return data


def platerecord_json(platerecord: NewRecord, masked: bool):
    sc = ScoreCoefficient(platerecord.achievements)
    ra = sc.ra(platerecord.ds)
    data = {
        "id": platerecord.id,
        "title": platerecord.title,
        "level": platerecord.diff,
        "level_index": platerecord.level,
        "type": platerecord.type,
        "achievements": get_masked_achievement(platerecord, sc, ra) if masked else platerecord.achievements,
        "fc": platerecord.fc,
        "fs": platerecord.fs
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
            notes = [c.tap_note, c.hold_note,
                     c.slide_note, c.touch_note, c.break_note]
        dct['charts'].append({
            'notes': notes, "charter": c.charter
        })
    data.append(dct)
    data.sort(key=lambda x: int(x['id']))
    return data


def t_equal(s1, s2):
    return s1.replace(' ', '').replace('\u3000', '') == s2.replace(' ', '').replace('\u3000', '')


def get_music_by_title(md, t, tp):
    tpl = (t, tp)
    if tpl in md:
        return md[tpl]
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
            if not in_or_equal(chart.level, level):
                continue
            # if not in_or_equal(chart.ds,ds):
                # continue
            # if not in_or_equal(chart.genre,genre):
                # continue
            if not in_or_equal(chart.diff, diff):
                continue
            if not in_or_equal(chart.version, version):
                continue
            temp.append(chart)
        return temp


def std_fc(fc: str):
    if fc in ("fc", "fcp", "ap", "app", ""):
        return fc
    return ""

def std_fs(fs: str):
    if fs in ("fs", "fsp", "fsd", "fsdp", "sync", ""):
        return fs
    if fs == "fdx":
        return "fsd"
    if fs == "fdxp":
        return "fsdp"
    return ""
