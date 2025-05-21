# This file is for accessing data in mysql database, and profiling / caching the data.
from access.redis import *
from models.chunithm import *


def __get_b30_and_r10(player: Player):
    b30 = []
    r10 = []
    rs = ChuniRecord.raw('select * from chunirecord where player_id = %s and recent = 0', player.id)
    for r in rs:
        setattr(r, 'ra', single_ra(r))
        b30.append(r)
    b30.sort(key=lambda x: x.ra, reverse=True)
    rs2 = ChuniRecord.raw('select * from chunirecord where player_id = %s and recent = 1', player.id)
    for r in rs2:
        r10.append(r)
    return b30[:30], r10


async def chuni_compute_ra(player: Player):
    b30, r10 = __get_b30_and_r10(player)
    total = 0.0
    for record in b30:
        total += single_ra(record)
    for record in r10:
        total += single_ra(record)
    rating = total / 40
    player.chuni_rating = rating
    player.access_time = time.time()
    player.save()
    return rating


@query_with_cache(by_access_time)
async def chuni_get_b30_and_r10(player: Player):
    b30, r10 = __get_b30_and_r10(player)
    return {
        "b30": [record_json(c) for c in b30],
        "r10": [record_json(c) for c in r10]
    }


@query_with_cache(by_access_time)
async def chuni_get_records(player: Player):
    rs = ChuniRecord.raw('select * from chunirecord where player_id = %s and recent = 0', player.id)
    rs2 = ChuniRecord.raw('select * from chunirecord where player_id = %s and recent = 1', player.id)
    # await compute_ra(g.user)
    return {
        "best": [record_json(c) for c in rs],
        "r10": [record_json(c) for c in rs2],
    }


async def get_profile_data():
    profile_data = {}
    for n, v in globals().items():
        if inspect.isfunction(v):
            if n.startswith('chuni_'):
                if await redis.exists("profile_hit_" + n):
                    profile_data[n] = (int(await redis.get("profile_hit_" + n)), int(await redis.get("profile_miss_" + n)))
    return profile_data