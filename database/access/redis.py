from redis import asyncio as aioredis
from collections import defaultdict
import time
import json
from typing import Callable, Dict, List, Optional
from models.maimai import Player
import inspect

redis = aioredis.Redis(host='localhost', port=6379, db=0)


async def profile_cache_hit(func_name):
    key = "profile_hit_" + func_name
    if await redis.exists(key):
        await redis.set(key, int(await redis.get(key)) + 1)
    else:
        await redis.set(key, 1)


async def profile_cache_miss(func_name):
    key = "profile_miss_" + func_name
    if await redis.exists(key):
        await redis.set(key, int(await redis.get(key)) + 1)
    else:
        await redis.set(key, 1)


def arg_serializer(*args, **kwargs):
    return str(args) + str(kwargs)


async def get_cache_time(key):
    if await redis.exists(key):
        return int(await redis.get(key))
    return 0


def query_with_cache(cached: Callable[..., bool]):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            args_without_first = (args[0].id, ) + args[1:]
            redis_key = func.__name__ + arg_serializer(*args_without_first, **kwargs)
            # print(redis_key)
            redis_key_time = redis_key + "_time"
            if (await cached(*args, cache_time=await get_cache_time(redis_key_time), **kwargs)):
                if await redis.exists(redis_key):
                    await profile_cache_hit(func.__name__)
                    return json.loads(await redis.get(redis_key))

            cache_val = await func(*args, **kwargs)
            await redis.set(redis_key_time, int(time.time()), ex=86400)
            await redis.set(redis_key, json.dumps(cache_val), ex=86400)
            await profile_cache_miss(func.__name__)
            return cache_val
        return wrapper
    return decorator


async def by_access_time(player: Player, *args, cache_time: int = 0, **kwargs):
    access_time = player.access_time
    return cache_time > access_time and access_time > int(time.time()) - 86400