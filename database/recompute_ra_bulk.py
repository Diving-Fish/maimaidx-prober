"""
批量重算所有玩家的 maimai rating —— 单次扫描版本（快）。

与 recompute_ra.py 逐玩家跑 compute_ra（每位玩家一条三表 join 查询）不同，本脚本：

  1. 先把 chart/music 两张小表读进内存，建 chart_id -> (ds, is_new) 映射；
  2. 按 player.id 分片，对 newrecord 做 **不带 join** 的原始扫描，直接取回
     (player_id, chart_id, achievements) 元组（跳过 peewee 的逐行建模开销）；
  3. 在 Python 里用 ScoreCoefficient 复刻单曲 ra，按玩家取 Top35(旧)/Top15(新)
     求和，同时统计参与谱面数量；
  4. 每片用一条 CASE UPDATE 写回。

这样只对 newrecord 做一次顺序扫描，查询数量从 ~13 万条降到「分片数 × 2」几十条。
计算逻辑与 recompute_ra.compute_ra_for 逐位一致（已在多个 id 区间上比对，0 处不一致）。

写回的字段:
    rating               = 旧版 Top35 ra 之和 + 新版 Top15 ra 之和
    maimai_new_rating    = 新版 Top15 ra 之和
    maimai_legacy_count  = 实际参与计算的旧版谱面数（<=35）
    maimai_new_count     = 实际参与计算的新版谱面数（<=15）

用法:
    python recompute_ra_bulk.py                 # 全部（有 b50 成绩的）玩家
    python recompute_ra_bulk.py --chunk 3000    # 每片 player.id 跨度
    python recompute_ra_bulk.py --dry-run       # 只算不写

说明:
    - 只更新有 music_id<100000 成绩的玩家；只玩宴谱/只玩 chuni 的玩家不会被动到，
      access_time 也不会被改写。
"""
import argparse
import asyncio
import sys
import time
from collections import defaultdict

from models.maimai import db, ScoreCoefficient


async def _fetch_all(cur):
    return await cur.fetchall()


async def load_chart_map():
    """chart_id -> (ds, is_new)，仅含 music_id < 100000（b50 计算范围）。"""
    rows = await db.aio_execute_sql(
        "SELECT chart.id, chart.ds, music.is_new "
        "FROM chart JOIN music ON chart.music_id = music.id "
        "WHERE chart.music_id < 100000",
        None, _fetch_all,
    )
    return {cid: (ds, bool(is_new)) for cid, ds, is_new in rows}


def compute_chunk(rows, cmap):
    """把一片原始成绩行汇总成 pid -> (rating, new_rating, legacy_count, new_count)。"""
    # pid -> [旧版 ra 列表, 新版 ra 列表]
    buckets = defaultdict(lambda: ([], []))
    for pid, cid, ach in rows:
        info = cmap.get(cid)
        if info is None:      # 宴谱或未知谱面，不计入 b50
            continue
        ds, is_new = info
        ra = ScoreCoefficient(ach).ra(ds)
        legacy_list, new_list = buckets[pid]
        (new_list if is_new else legacy_list).append(ra)

    result = {}
    for pid, (legacy_list, new_list) in buckets.items():
        # 只按 ra 排序即可：Top-N 之和 / 数量对同 ra 的并列取舍不敏感
        legacy_list.sort(reverse=True)
        new_list.sort(reverse=True)
        legacy_top = legacy_list[:35]
        new_top = new_list[:15]
        new_rating = sum(new_top)
        rating = new_rating + sum(legacy_top)
        result[pid] = (rating, new_rating, len(legacy_top), len(new_top))
    return result


def build_update_sql(result):
    """把一片结果拼成一条 CASE UPDATE（所有值均为整数，可安全内联）。"""
    ids = ",".join(str(pid) for pid in result)
    cases = [[], [], [], []]  # rating, new_rating, legacy_count, new_count
    for pid, vals in result.items():
        for i, v in enumerate(vals):
            cases[i].append(f"WHEN {pid} THEN {v}")
    joined = [" ".join(c) for c in cases]
    return (
        "UPDATE player SET "
        f"rating = CASE id {joined[0]} END, "
        f"maimai_new_rating = CASE id {joined[1]} END, "
        f"maimai_legacy_count = CASE id {joined[2]} END, "
        f"maimai_new_count = CASE id {joined[3]} END "
        f"WHERE id IN ({ids})"
    )


def render_progress(done, total, start, updated, width=40):
    frac = done / total if total else 1.0
    filled = int(width * frac)
    bar = '█' * filled + '░' * (width - filled)
    elapsed = time.time() - start
    eta = (total - done) / (done / elapsed) if done and elapsed > 0 else 0
    sys.stdout.write(
        f'\r[{bar}] chunk {done}/{total} ({frac*100:5.1f}%)  '
        f'players {updated}  {elapsed:5.0f}s  ETA {eta:5.0f}s'
    )
    sys.stdout.flush()


async def main(opts):
    db.pool_params['maxsize'] = 4
    await db.aio_connect()

    print('加载 chart/music 映射...')
    cmap = await load_chart_map()
    print(f'  {len(cmap)} 个谱面（music_id<100000）')

    row = (await db.aio_execute_sql(
        "SELECT MIN(id), MAX(id) FROM player", None, _fetch_all))[0]
    lo, hi = row
    if lo is None:
        print('没有玩家')
        return
    chunks = [(s, min(s + opts.chunk - 1, hi)) for s in range(lo, hi + 1, opts.chunk)]
    total = len(chunks)
    print(f'player.id 区间 {lo}~{hi}，分 {total} 片，每片跨度 {opts.chunk}'
          f'{"（dry-run，不写库）" if opts.dry_run else ""}')

    start = time.time()
    updated = 0
    for i, (a, b) in enumerate(chunks, 1):
        rows = await db.aio_execute_sql(
            "SELECT player_id, chart_id, achievements FROM newrecord "
            "WHERE player_id BETWEEN %s AND %s",
            (a, b), _fetch_all,
        )
        result = compute_chunk(rows, cmap)
        if result and not opts.dry_run:
            await db.aio_execute_sql(build_update_sql(result))
        updated += len(result)
        render_progress(i, total, start, updated)
    print()
    print(f'完成：{total} 片，{"命中" if opts.dry_run else "更新"} {updated} 位玩家，'
          f'用时 {time.time() - start:.1f}s')
    await db.aio_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='批量重算所有玩家 maimai rating（单次扫描）')
    parser.add_argument('--chunk', type=int, default=3000,
                        help='每片 player.id 跨度，默认 3000（越大越快但越吃内存）')
    parser.add_argument('--dry-run', action='store_true', help='只算不写库')
    opts = parser.parse_args()
    asyncio.run(main(opts))
