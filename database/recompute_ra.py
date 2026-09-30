"""
批量重算所有玩家的 maimai rating。

复用 routes/maimai.py 中 compute_ra / get_dx_and_sd_for50 的算法，对数据库中
所有玩家跑一遍，利用 peewee_async 的连接池开多个连接并发执行，并显示进度条。

用法:
    python recompute_ra.py                # 处理所有玩家
    python recompute_ra.py --concurrency 16
    python recompute_ra.py --only-with-records   # 只处理有 maimai 成绩的玩家
    python recompute_ra.py --dry-run      # 只计算不写库

说明:
    - rating 字段即 maimai rating。没有 maimai 成绩的玩家会被算成 0。
    - 与 compute_ra 不同，本脚本 **不会** 改写 access_time（避免把全库的
      最后访问时间刷成当前时间），只更新 rating 和 maimai_new_rating。
      如需完全复刻 compute_ra 的行为，把 --touch-access-time 打开即可。
"""
import argparse
import asyncio
import sys
import time

# 复用现有模型与算法（models.maimai 会在 import 时建表并加载配置）
from models.maimai import db, Player, NewRecord, ScoreCoefficient

SQL_FOR50 = (
    'select newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore, '
    'chart.ds as ds, chart.level as level, chart.difficulty as diff, '
    'music.type as `type`, music.id as `id`, music.is_new as is_new, music.title as title '
    'from newrecord, chart, music '
    'where player_id = %s and chart_id = chart.id and chart.music_id = music.id '
    'and chart.music_id < 100000'
)


async def compute_ra_for(player_id: int, touch_access_time: bool, dry_run: bool):
    """复刻 get_dx_and_sd_for50 + compute_ra，返回 (rating, new_rating)。"""
    rows = await NewRecord.raw(SQL_FOR50, player_id).aio_execute()
    sd = []   # 旧版本 (b35)
    dx = []   # 新版本 (b15)
    for r in rows:
        setattr(r, 'ra', ScoreCoefficient(r.achievements).ra(r.ds))
        if r.is_new:
            dx.append(r)
        else:
            sd.append(r)
    sd.sort(key=lambda x: (x.ra, x.ds, x.achievements), reverse=True)
    dx.sort(key=lambda x: (x.ra, x.ds, x.achievements), reverse=True)
    sd = sd[:35]
    dx = dx[:15]

    new_rating = sum(int(t.ra) for t in dx)
    rating = new_rating + sum(int(t.ra) for t in sd)

    if not dry_run:
        update = {
            Player.rating: rating,
            Player.maimai_new_rating: new_rating,
            Player.maimai_legacy_count: len(sd),
            Player.maimai_new_count: len(dx),
        }
        if touch_access_time:
            update[Player.access_time] = time.time()
        await Player.update(update).where(Player.id == player_id).aio_execute()

    return rating, new_rating


def render_progress(done: int, total: int, start: float, width: int = 40):
    frac = done / total if total else 1.0
    filled = int(width * frac)
    bar = '█' * filled + '░' * (width - filled)
    elapsed = time.time() - start
    rate = done / elapsed if elapsed > 0 else 0
    eta = (total - done) / rate if rate > 0 else 0
    sys.stdout.write(
        f'\r[{bar}] {done}/{total} ({frac*100:5.1f}%)  '
        f'{rate:6.1f}/s  ETA {eta:5.0f}s'
    )
    sys.stdout.flush()


async def worker(queue: asyncio.Queue, counter: dict, opts):
    while True:
        pid = await queue.get()
        if pid is None:
            queue.task_done()
            return
        try:
            await compute_ra_for(pid, opts.touch_access_time, opts.dry_run)
        except Exception as e:
            counter['errors'] += 1
            # 换行避免和进度条串行
            sys.stdout.write(f'\n[warn] player {pid} failed: {e}\n')
        finally:
            counter['done'] += 1
            queue.task_done()


async def main(opts):
    await db.aio_connect()

    if opts.only_with_records:
        rows = await Player.raw(
            'select distinct player_id as id from newrecord'
        ).aio_execute()
    else:
        rows = await Player.raw('select id from player').aio_execute()
    player_ids = [r.id for r in rows]
    if opts.limit:
        player_ids = player_ids[:opts.limit]
    total = len(player_ids)
    print(f'共 {total} 位玩家待处理，并发连接数 {opts.concurrency}'
          f'{"（dry-run，不写库）" if opts.dry_run else ""}')
    if total == 0:
        return

    queue: asyncio.Queue = asyncio.Queue()
    for pid in player_ids:
        queue.put_nowait(pid)
    for _ in range(opts.concurrency):
        queue.put_nowait(None)  # 结束信号

    counter = {'done': 0, 'errors': 0}
    start = time.time()

    workers = [asyncio.create_task(worker(queue, counter, opts))
               for _ in range(opts.concurrency)]

    # 进度条刷新协程
    async def ticker():
        while counter['done'] < total:
            render_progress(counter['done'], total, start)
            await asyncio.sleep(0.2)
        render_progress(counter['done'], total, start)

    tick = asyncio.create_task(ticker())
    await queue.join()
    await asyncio.gather(*workers)
    await tick
    print()  # 进度条换行

    elapsed = time.time() - start
    print(f'完成：{total} 位玩家，用时 {elapsed:.1f}s，错误 {counter["errors"]} 个')
    await db.aio_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='批量重算所有玩家的 maimai rating')
    parser.add_argument('-c', '--concurrency', type=int, default=16,
                        help='并发连接数（数据库连接池大小），默认 16')
    parser.add_argument('--only-with-records', action='store_true',
                        help='只处理有 maimai 成绩的玩家')
    parser.add_argument('--touch-access-time', action='store_true',
                        help='同时把 access_time 刷成当前时间（完全复刻 compute_ra）')
    parser.add_argument('--dry-run', action='store_true',
                        help='只计算不写库')
    parser.add_argument('--limit', type=int, default=0,
                        help='只处理前 N 位玩家（用于测试/分批），0 表示全部')
    opts = parser.parse_args()

    # 调大异步连接池上限，让并发真正用上多连接
    db.pool_params['maxsize'] = max(opts.concurrency, db.pool_params.get('minsize', 1))
    db.pool_params['minsize'] = 1

    asyncio.run(main(opts))
