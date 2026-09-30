"""Install an authenticated static HTML release without touching Docker or Nginx."""
import fcntl
from concurrent.futures import ThreadPoolExecutor
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import urlopen
from uuid import uuid4

CONFIG = json.loads((Path(__file__).resolve().parents[2] / 'web/deploy/config.json').read_text())
ROOT = Path(os.environ.get("PROBER_WEB_ROOT", CONFIG['webRoot']))
CDN = CONFIG['cdnBase'] + CONFIG['objectPrefix']
LOCAL_PREFIX = CONFIG['localAssetPrefix']
MAX_HTML_BYTES = 256 * 1024
MAX_ASSET_BYTES = 16 * 1024 * 1024
MAX_RELEASE_BYTES = 64 * 1024 * 1024
MAX_DEPLOY_SECONDS = 240



class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []
        self.scripts = 0
        self.styles = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('src'):
            self.assets.append(attrs['src'])
            self.scripts += 1
        if tag == 'link' and 'stylesheet' in attrs.get('rel', '').split():
            self.assets.append(attrs.get('href', ''))
            self.styles += 1


def validate(release, html):
    if not re.fullmatch(r'[0-9a-f]{40}-[0-9]+-[0-9]+', release):
        raise ValueError('Invalid release ID')
    if not html or len(html) > MAX_HTML_BYTES:
        raise ValueError('HTML must be between 1 and 262144 bytes')
    try:
        text = html.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError('HTML must be UTF-8') from None
    parser = AssetParser()
    parser.feed(text)
    if not parser.scripts or not parser.styles:
        raise ValueError('Expected built HTML with scripts and stylesheets')
    base = CDN + release + '/'
    for url in parser.assets:
        if not url.startswith(base) or '..' in urlsplit(url).path.split('/'):
            raise ValueError('All scripts and stylesheets must reference the selected CDN release')
    return {'release': release, 'commit': release[:40], 'assetBase': base,
            'htmlSha256': hashlib.sha256(html).hexdigest()}


def download(url, limit):
    # No browser is involved, so font CORS does not apply. Hash validation below
    # also prevents a CDN error page from being installed as a script or font.
    with urlopen(url, timeout=30) as response:
        body = response.read(limit + 1)
    if len(body) > limit:
        raise ValueError('CDN response exceeded its expected size')
    return body


def download_release(stage, release, html, fetch):
    base = CDN + release + '/'
    local_base = LOCAL_PREFIX + release + '/'
    manifest = json.loads(fetch(base + 'asset-manifest.json', MAX_HTML_BYTES))
    if not isinstance(manifest, dict):
        raise ValueError('Invalid CDN release manifest')
    entries = manifest.get('files')
    if manifest.get('release') != release or not isinstance(entries, list) or not 1 <= len(entries) <= 256:
        raise ValueError('Invalid CDN release manifest')
    paths = set()
    total = 0
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Invalid CDN asset entry')
        name, size, digest = entry.get('path', ''), entry.get('size'), entry.get('sha256', '')
        if (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_./-]+', name)
                or any(part in ('', '.', '..') or part.startswith('.') for part in name.split('/'))
                or name in paths or name in ('index.local.html', 'release.json', 'asset-manifest.json')):
            raise ValueError('Unsafe or duplicate asset path')
        if (not isinstance(size, int) or not 0 <= size <= MAX_ASSET_BYTES
                or not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest)):
            raise ValueError('Invalid asset size or digest')
        paths.add(name)
        total += size
    if total > MAX_RELEASE_BYTES or 'index.html' not in paths:
        raise ValueError('Invalid release size or missing HTML')
    parser = AssetParser()
    parser.feed(html.decode('utf-8'))
    if any(url[len(base):] not in paths for url in parser.assets):
        raise ValueError('Manifest is missing an HTML dependency')

    def save(entry):
        name = entry['path']
        content = html if name == 'index.html' else fetch(base + name, entry['size'])
        if len(content) != entry['size'] or hashlib.sha256(content).hexdigest() != entry['sha256']:
            raise ValueError('Asset checksum mismatch: ' + name)
        # Local styles must also resolve their embedded font/image URLs locally.
        if name.endswith('.css'):
            content = content.replace(base.encode(), local_base.encode())
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        target.chmod(0o644)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(save, entries))
    (stage / 'index.local.html').write_bytes(html.replace(base.encode(), local_base.encode()))
    (stage / 'index.local.html').chmod(0o644)


def install(release, html, root=None, fetch=download):
    metadata = validate(release, html)
    started = time.monotonic()
    root = Path(root) if root is not None else ROOT
    releases = root / 'releases'
    releases.mkdir(parents=True, exist_ok=True)
    # Four Hypercorn workers can handle deployments; serialize across processes.
    with (root / '.deploy.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if time.monotonic() - started > MAX_DEPLOY_SECONDS:
            raise TimeoutError('Deployment waited too long for the lock')
        target = releases / release
        if target.exists():
            if (target / 'index.html').read_bytes() != html:
                raise ValueError('A different HTML file already exists for this release')
            if not (target / 'index.local.html').is_file():
                raise ValueError('Existing release has no complete local fallback')
        else:
            stage = Path(tempfile.mkdtemp(prefix='.staging-', dir=releases))
            try:
                download_release(stage, release, html, fetch)
                metadata['localAssetBase'] = LOCAL_PREFIX + release + '/'
                (stage / 'release.json').write_text(json.dumps(metadata, indent=2) + '\n')
                (stage / 'release.json').chmod(0o644)
                stage.chmod(0o755)
                os.replace(stage, target)
            finally:
                shutil.rmtree(stage, ignore_errors=True)
        if time.monotonic() - started > MAX_DEPLOY_SECONDS:
            raise TimeoutError('Deployment exceeded its time limit; not activating it')
        link = root / ('.current-' + uuid4().hex)
        try:
            link.symlink_to(Path('releases') / release, target_is_directory=True)
            os.replace(link, root / 'current')
        finally:
            link.unlink(missing_ok=True)
    return json.loads((target / 'release.json').read_text())
