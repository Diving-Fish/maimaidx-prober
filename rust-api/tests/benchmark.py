"""Alternate direct Python/Rust requests without proxies; save timings, never tokens."""
import argparse
import json
import math
import os
import statistics
import time
from pathlib import Path

import httpx
from parity import ROOT, connect


def summarize(samples):
    ordered = sorted(samples)
    return {"median_ms": round(statistics.median(samples), 3),
            "p95_ms": round(ordered[math.ceil(len(samples) * .95) - 1], 3)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=20)
    parser.add_argument('--output', default=str(ROOT / 'rust-api/benchmark-results.json'))
    args = parser.parse_args()
    if args.samples < 1:
        parser.error('samples must be positive')
    config = json.loads((ROOT / 'database/config.json').read_text())
    connection = connect(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT import_token FROM player WHERE username=%s', ('DivingFish',))
            token = cursor.fetchone()['import_token']
    finally:
        connection.close()
    cases = [
        ('player/records', 'GET', '/player/records', {'headers': {'Import-Token': token}}),
        ('query/player B50', 'POST', '/query/player', {'json': {'username': 'DivingFish', 'b50': True}}),
        ('dev/player/records', 'GET', '/dev/player/records?username=DivingFish',
         {'headers': {'developer-token': os.environ['PARITY_DEVELOPER_TOKEN']}}),
    ]
    targets = {'python': 'http://127.0.0.1:8333', 'rust': 'http://127.0.0.1:8345'}
    report = {'username': 'DivingFish', 'samples': args.samples, 'warmup_pairs': 3,
              'proxy': False, 'method': 'alternating loopback HTTP requests', 'interfaces': {}}
    with httpx.Client(trust_env=False, timeout=35) as client:
        for label, method, path, kwargs in cases:
            samples = {name: [] for name in targets}
            for index in range(args.samples + 3):
                bodies = {}
                order = ['python', 'rust'] if index % 2 == 0 else ['rust', 'python']
                for name in order:
                    client.cookies.clear()
                    start = time.perf_counter()
                    response = client.request(method, targets[name] + path, **kwargs)
                    elapsed = (time.perf_counter() - start) * 1000
                    assert response.status_code == 200, f'{label}: {name} status {response.status_code}'
                    bodies[name] = response.json()
                    if index >= 3:
                        samples[name].append(elapsed)
                assert bodies['python'] == bodies['rust'], f'{label}: response differs'
                time.sleep(.05)
            report['interfaces'][label] = {
                'response_equal': True,
                'summary': {name: summarize(values) for name, values in samples.items()},
                'raw_ms': samples,
            }
            print(label, report['interfaces'][label]['summary'], flush=True)
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
