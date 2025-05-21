# This file is for accessing data in mysql database, and profiling / caching the data.
import asyncio
from access.redis import *
from models.maimai import *


md_cache = music_data()
md_map = {}
md_title_type_map = {}
for music in md_cache:
    md_map[music['id']] = music
    md_title_type_map[(music["title"], music["type"])] = music


@query_with_cache(by_access_time)
async def maimai_get_records(player: Player, masked: bool):
    r = NewRecord.raw('select newrecord.achievements, newrecord.chart_id, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id)
    records = defaultdict(lambda: [])
    for record in r:
        elem = record_json(record, masked)
        records[str(record.id)].append(elem)
    return records


async def generate_b40_b50_cache(player: Player, records_map, access_time: int):
    l1 = []
    l2 = []
    for k, records in records_map.items():
        for record in records:
            if md_map[str(record['song_id'])]['basic_info']['is_new']:
                l2.append(record)
            else:
                l1.append(record)
    l1.sort(key=lambda x: x['ra'], reverse=True)
    l2.sort(key=lambda x: x['ra'], reverse=True)
    b40 = {
        "sd": l1[:25],
        "dx": l2[:15]
    }
    b50 = {
        "sd": l1[:35],
        "dx": l2[:15]
    }
    return b40, b50


# data should be filtered rightly
async def maimai_update_records_cache(player: Player, data: List[Dict]):
    access_time = int(time.time())
    r = await maimai_get_records(player, False)
    d = {}
    for k, records in r.items():
        for record in records:
            d[record['cid']] = record
    for record in data:
        d[record['cid']] = record
    records = defaultdict(lambda: [])
    for k, v in d.items():
        records[str(v['song_id'])].append(v)
    # update cache
    await redis.set(f"maimai_get_records({str(player.id)}, False){{}}", json.dumps(records), ex=86400)
    await redis.set(f"maimai_get_records({str(player.id)}, False){{}}_time", access_time + 1, ex=86400)

    b40 = {}
    b50 = {}
    if not player.mask:
        # update maimai_get_dx_and_sd cache
        b40, b50 = await generate_b40_b50_cache(player, records, access_time)

    # update masked
    for lst in records:
        for record in records[lst]:
            record['dxScore'] = 0
            sc = ScoreCoefficient(record['achievements'])
            record['achievements'] = get_masked_achievement(record['achievements'], record['fc'], record['ds'], sc, record['ra']) 
    await redis.set(f"maimai_get_records({str(player.id)}, True){{}}", json.dumps(records), ex=86400)
    await redis.set(f"maimai_get_records({str(player.id)}, True){{}}_time", access_time + 1, ex=86400)

    if player.mask:
        # update maimai_get_dx_and_sd cache
        b40, b50 = await generate_b40_b50_cache(player, records, access_time)
        
    # update maimai_get_dx_and_sd cache
    await redis.set(f"maimai_get_dx_and_sd({str(player.id)},){{}}", json.dumps(b40), ex=86400)
    await redis.set(f"maimai_get_dx_and_sd({str(player.id)},){{}}_time", access_time + 1, ex=86400)
    
    # update maimai_get_dx_and_sd_for50 cache
    await redis.set(f"maimai_get_dx_and_sd_for50({str(player.id)},){{}}", json.dumps(b50), ex=86400)
    await redis.set(f"maimai_get_dx_and_sd_for50({str(player.id)},){{}}_time", access_time + 1, ex=86400)

    # add flush tag
    await redis.set("maimai_update_records_cache_" + str(player.id), 1)
    # update access time
    player.access_time = access_time
    ra = 0
    for record in b50['sd']:
        ra += int(record['ra'])
    for record in b50['dx']:
        ra += int(record['ra']) 
    player.rating = ra
    player.save()


async def flush_update_cache():
    lock = redis.lock("flush_update_cache", timeout=60)
    if not await lock.acquire(blocking=False):
        print("Flush update cache is already running")
        return
    print("Flushing update cache")
    dicts = {}
    f = open('update_cache_log.txt', 'a')
    for k in await redis.keys("maimai_update_records_cache_*"):
        player_id = str(k, encoding='utf-8').split("_")[-1]
        records_key = f"maimai_get_records({str(player_id)}, False){{}}"
        if await redis.exists(records_key):
            ns = time.time_ns()
            records_map = json.loads(await redis.get(records_key))
            for _, records in records_map.items():
                for record in records:
                    dicts[record['cid']] = (record["achievements"], record["fc"], record["fs"], record["dxScore"])
            rs = NewRecord.raw(
                'select * from newrecord where player_id = %s', player_id)
            updates = []
            creates = []
            for r in rs:
                # print(r.chart_id)
                if r.chart_id in dicts:
                    v = dicts[r.chart_id]
                    r.achievements = v[0]
                    r.fc = std_fc(v[1])
                    r.fs = std_fs(v[2])
                    r.dxScore = v[3]
                    updates.append(r)
                    del dicts[r.chart_id]
            # print(len(dicts))
            for k in dicts:
                v = dicts[k]
                creates.append({"chart": k, "player": player_id,
                            "fc": std_fc(v[1]), "fs": std_fs(v[2]), "dxScore": v[3], "achievements": v[0]})
            if len(creates) > 0:
                NewRecord.insert_many(creates).execute()
            # print(updates)
            if len(updates) > 0:
                NewRecord.bulk_update(updates, fields=[
                                NewRecord.achievements, NewRecord.fc, NewRecord.fs, NewRecord.dxScore])
            await maimai_compute_ra(Player.get(Player.id == player_id))
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] Updated {len(updates)} records and created {len(creates)} records for player {player_id}, took {(time.time_ns() - ns) / 1e6} ms\n")
            await redis.delete(k)
    f.close()
    await lock.release()


@query_with_cache(by_access_time)
async def maimai_get_dx_and_sd(player: Player):
    l = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id', player.id)
    l1 = []
    l2 = []
    for r in l:
        setattr(r, 'ra', ScoreCoefficient(r.achievements).ra(r.ds))
        if r.is_new:
            l2.append(r)
        else:
            l1.append(r)
    l1.sort(key=lambda x: x.ra, reverse=True)
    l2.sort(key=lambda x: x.ra, reverse=True)
    return {
        "sd": [record_json(c, player.mask) for c in l1[:25]],
        "dx": [record_json(c, player.mask) for c in l2[:15]]
    }


def __get_dx_and_sd_for50(player: Player):
    l = NewRecord.raw('select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, chart.ds as ds, chart.level as level, chart.difficulty as diff, music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title from newrecord, chart, music where player_id = %s and chart_id = chart.id and chart.music_id = music.id and chart.music_id < 100000', player.id)
    l1 = []
    l2 = []
    for r in l:
        setattr(r, 'ra', ScoreCoefficient(r.achievements).ra(r.ds))
        if r.is_new:
            l2.append(r)
        else:
            l1.append(r)
    l1.sort(key=lambda x: x.ra, reverse=True)
    l2.sort(key=lambda x: x.ra, reverse=True)
    return l1[:35], l2[:15]


@query_with_cache(by_access_time)
async def maimai_get_dx_and_sd_for50(player: Player):
    sd, dx = __get_dx_and_sd_for50(player)
    return {
        "sd": [record_json(c, player.mask) for c in sd],
        "dx": [record_json(c, player.mask) for c in dx]
    }


async def maimai_get_plate_list(player: Player, version: List[Dict]):
    records_map = await maimai_get_records(player, player.mask)
    verlist = []
    for k, records in records_map.items():
        music = md_map[k]
        if in_or_equal(music['basic_info']['from'], version):
            for record in records:
                data = {
                    "id": music['id'],
                    "title": music['title'],
                    "level": record['level'],
                    "level_index": record['level_index'],
                    "type": record['type'],
                    "achievements": record['achievements'],
                    "fc": record['fc'],
                    "fs": record['fs']
                }
                verlist.append(data)
    return verlist


async def maimai_compute_ra(player: Player):
    rating = 0
    sd, dx = __get_dx_and_sd_for50(player)
    for t in sd:
        rating += int(t.ra)
    for t in dx:
        rating += int(t.ra)
    player.rating = rating
    player.access_time = int(time.time())
    player.save()
    return rating


async def get_profile_data():
    profile_data = {}
    for n, v in globals().items():
        if inspect.isfunction(v):
            if n.startswith('maimai_'):
                if await redis.exists("profile_hit_" + n):
                    profile_data[n] = (int(await redis.get("profile_hit_" + n)), int(await redis.get("profile_miss_" + n)))
    return profile_data
