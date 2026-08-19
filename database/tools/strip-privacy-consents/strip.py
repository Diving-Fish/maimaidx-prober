"""撤掉 backfill 误建给「从未授权」用户的授权。

**为什么这些行是错的。** dev_backfill.py 扫 newdeveloperlog 判断「这个用户被
这个应用查过」，而 developer_required 是**先写日志再执行**：bot 查一个
privacy=1 的用户，查分器返回 403，日志照样留了一行。脚本不看 privacy，
于是把一次被拒绝的调用当成了实际的调用关系，给建了 consent。

这批用户当初的表态恰好是相反的——勾 privacy 等于「谁都别查我」，
accept_agreement=0 则是连用户协议都没同意。他们没有点过任何同意页，
却在授权表里有了一条有效授权。保留 username: 寻址之后，这等于让他们
从「谁都读不到」变成「该应用的任意用户都能按用户名查到」。

**范围。** 只动 source='legacy_developer' 的行——用户自己在同意页点出来的
授权一律不碰，哪怕他也开着 privacy：那是他自己的选择，本脚本无权代他反悔。

默认只预演。--apply 才写库，同时产出 CSV 与回滚 SQL。
"""

import argparse
import csv
import json
import re
import time
from pathlib import Path

import pymysql

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent.parent / "config.json"

SELECT_SQL = """
SELECT c.id            AS consent_id,
       c.client_id     AS client_id,
       cl.name         AS app_name,
       c.user_id       AS user_id,
       p.username      AS username,
       p.privacy       AS privacy,
       p.accept_agreement AS accept_agreement,
       c.scope         AS consent_scope,
       c.granted_at    AS granted_at,
       s.id            AS subject_id,
       s.subject_hash  AS subject_hash,
       s.label         AS subject_label,
       s.source        AS subject_source,
       s.created_at    AS subject_created_at,
       s.last_used_at  AS subject_last_used_at
  FROM oauth_consent c
  JOIN player p        ON p.id = c.user_id
  LEFT JOIN oauth_client cl ON cl.client_id = c.client_id
  LEFT JOIN oauth_client_subject s
         ON s.client_id = c.client_id AND s.user_id = c.user_id
 WHERE c.source = 'legacy_developer'
   AND c.revoked_at IS NULL
   AND (p.privacy = 1 OR p.accept_agreement = 0)
 ORDER BY c.client_id, c.user_id
"""


def connect():
    url = json.loads(CONFIG.read_text(encoding="utf-8"))["mysql_url"]
    m = re.match(r"mysql\+?\w*://([^:]+):([^@]*)@([^:/]+):?(\d*)/(\w+)", url)
    if not m:
        raise SystemExit(f"看不懂的 mysql_url：{url}")
    user, pwd, host, port, db = m.groups()
    return pymysql.connect(host=host, port=int(port or 3306), user=user,
                           password=pwd, database=db, charset="utf8mb4",
                           cursorclass=pymysql.cursors.DictCursor)


def sql_str(value):
    if value is None:
        return "NULL"
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def write_rollback(path, rows, ts):
    """回滚脚本：把撤销撤回去，再把删掉的映射原样插回来。

    consent 用 id 精确匹配，且要求 revoked_at 等于本次时间戳——避免把
    此前（比如剥离扫库那次）撤销的行一起复活。
    """
    consent_ids = sorted({r["consent_id"] for r in rows})
    subjects = [r for r in rows if r["subject_id"] is not None]
    with path.open("w", encoding="utf-8") as fw:
        fw.write(f"-- 回滚 {time.strftime('%Y%m%d-%H%M%S', time.localtime(ts))} "
                 f"的 privacy / 未同意协议授权剥离。按顺序执行即可还原。\n")
        fw.write("-- 只还原本次改动的行（revoked_at 精确匹配本次时间戳）。\n\n")
        for start in range(0, len(consent_ids), 500):
            chunk = ",".join(str(i) for i in consent_ids[start:start + 500])
            fw.write("UPDATE oauth_consent SET revoked_at=NULL, updated_at=granted_at\n"
                     f"  WHERE id IN ({chunk}) AND revoked_at={ts};\n")
        fw.write("\n")
        if subjects:
            fw.write("INSERT INTO oauth_client_subject "
                     "(client_id,subject_hash,user_id,label,source,created_at,last_used_at) VALUES\n")
            values = [
                "  (" + ",".join(sql_str(r[k]) for k in (
                    "client_id", "subject_hash", "user_id", "subject_label",
                    "subject_source", "subject_created_at", "subject_last_used_at")) + ")"
                for r in subjects
            ]
            fw.write(",\n".join(values) + ";\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真的写库（默认只预演）")
    args = ap.parse_args()

    conn = connect()
    with conn.cursor() as cur:
        cur.execute(SELECT_SQL)
        rows = cur.fetchall()

    if not rows:
        print("没有需要处理的行。")
        return

    consents = {r["consent_id"] for r in rows}
    subjects = [r for r in rows if r["subject_id"] is not None]
    privacy_only = {r["consent_id"] for r in rows if r["privacy"]}
    noagree_only = {r["consent_id"] for r in rows if not r["accept_agreement"]}
    clients = {r["client_id"] for r in rows}
    users = {r["user_id"] for r in rows}

    print(f"待撤销授权 {len(consents)} 条，涉及 {len(clients)} 个应用、{len(users)} 个用户")
    print(f"  其中 privacy=1 的 {len(privacy_only)} 条，"
          f"未同意用户协议的 {len(noagree_only)} 条"
          f"（两者重叠 {len(privacy_only & noagree_only)} 条）")
    print(f"待删除绑定映射 {len(subjects)} 条")

    ts = int(time.time())
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(ts))
    csv_path = HERE / f"revoked-{stamp}.csv"
    sql_path = HERE / f"rollback-{stamp}.sql"

    with csv_path.open("w", encoding="utf-8", newline="") as fw:
        writer = csv.DictWriter(fw, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    write_rollback(sql_path, rows, ts)
    print(f"名单 → {csv_path.name}\n回滚 → {sql_path.name}")

    if not args.apply:
        print("\n预演结束，没有写库。确认无误后加 --apply 执行。")
        return

    with conn.cursor() as cur:
        ids = sorted(consents)
        for start in range(0, len(ids), 500):
            chunk = ids[start:start + 500]
            cur.execute(
                "UPDATE oauth_consent SET revoked_at=%s, updated_at=%s "
                f"WHERE id IN ({','.join(['%s'] * len(chunk))}) AND revoked_at IS NULL",
                [ts, ts, *chunk],
            )
        sids = sorted({r["subject_id"] for r in subjects})
        for start in range(0, len(sids), 500):
            chunk = sids[start:start + 500]
            cur.execute(
                f"DELETE FROM oauth_client_subject WHERE id IN ({','.join(['%s'] * len(chunk))})",
                chunk,
            )
    conn.commit()
    print(f"\n已执行：撤销 {len(consents)} 条授权，删除 {len(sids)} 条映射，时间戳 {ts}")


if __name__ == "__main__":
    main()
