"""Check the uploaded assets, including cross-origin fonts, before activating HTML."""
import argparse
from pathlib import Path
import time
from urllib.request import Request, urlopen
from upload_oss import plan, CDN

ORIGIN = 'https://maimai.diving-fish.com'


def verify(directory, release):
    for path, key, expected in plan(directory, release):
        url = CDN + key
        for attempt in range(3):
            try:
                req = Request(url, method='HEAD', headers={'Origin': ORIGIN, 'Accept-Encoding': 'br, gzip'})
                with urlopen(req, timeout=30) as response:
                    mime = response.headers.get('Content-Type', '').split(';')[0]
                    if mime != expected['Content-Type']:
                        raise ValueError(f'Unexpected Content-Type for {path.name}: {mime}')
                    if path.suffix in ('.woff', '.woff2', '.ttf', '.otf'):
                        allowed = response.headers.get('Access-Control-Allow-Origin')
                        if allowed not in ('*', ORIGIN):
                            print('::warning::CDN font CORS missing for ' + ORIGIN + '; browsers will use the local fallback')
                    if path.suffix in ('.js', '.css') and not response.headers.get('Content-Encoding'):
                        print(f'::warning::Enable Brotli/gzip on CDN for {path.name}')
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        print('Verified: ' + url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--release', required=True)
    args = parser.parse_args()
    verify(args.directory, args.release)
