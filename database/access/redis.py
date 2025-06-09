from redis import asyncio as aioredis

redis = aioredis.Redis(host='localhost', port=6379, db=0)
