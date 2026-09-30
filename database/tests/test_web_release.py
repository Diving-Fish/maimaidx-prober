"""CI deployment tests, isolated from the production database and filesystem."""
import ast
import asyncio
from functools import wraps
import hmac
import hashlib
import json
from urllib.parse import urlsplit
from urllib.error import URLError
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from quart import Quart, request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.web_release import install, validate, CDN, MAX_HTML_BYTES

RELEASE = 'a' * 40 + '-1-1'
OTHER = 'b' * 40 + '-2-1'


def html(release=RELEASE):
    base = CDN + release + '/'
    return f'<!doctype html><script src="{base}js/app.js"></script><link rel="stylesheet" href="{base}css/app.css"><div id="app"></div>'.encode()


def mock_download(url, limit):
    release = urlsplit(url).path.split('/')[3]
    base = CDN + release + '/'
    files = {'index.html': html(release), 'js/app.js': b'console.log(1)',
             'css/app.css': ('@font-face{src:url(' + base + 'fonts/icon.woff2)}').encode(),
             'fonts/icon.woff2': b'test-font'}
    if url.endswith('/asset-manifest.json'):
        return json.dumps({'release': release, 'files': [
            {'path': name, 'size': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
            for name, body in files.items()]}).encode()
    return files[url[len(base):]]


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_switch_retains_previous_and_allows_rollback(self):
        install(RELEASE, html(), self.root, fetch=mock_download)
        install(OTHER, html(OTHER), self.root, fetch=mock_download)
        self.assertEqual((self.root / 'current/index.html').read_bytes(), html(OTHER))
        self.assertTrue((self.root / 'releases' / RELEASE / 'index.html').exists())
        install(RELEASE, html(), self.root, fetch=mock_download)
        self.assertEqual((self.root / 'current/index.html').read_bytes(), html())

    def test_local_html_and_css_use_same_origin_assets(self):
        install(RELEASE, html(), self.root, fetch=mock_download)
        local_html = (self.root / 'current/index.local.html').read_bytes()
        css = (self.root / 'current/css/app.css').read_bytes()
        self.assertNotIn(CDN.encode(), local_html)
        self.assertNotIn(CDN.encode(), css)
        self.assertIn(('/web-assets/' + RELEASE + '/').encode(), css)
        self.assertEqual((self.root / 'current/fonts/icon.woff2').read_bytes(), b'test-font')

    def test_failed_or_corrupt_download_never_switches_release(self):
        install(RELEASE, html(), self.root, fetch=mock_download)
        def corrupt(url, limit):
            if url.endswith('/js/app.js'):
                return b'corrupted'
            return mock_download(url, limit)
        with self.assertRaisesRegex(ValueError, 'checksum'):
            install(OTHER, html(OTHER), self.root, fetch=corrupt)
        self.assertEqual((self.root / 'current/index.html').read_bytes(), html())
        self.assertFalse((self.root / 'releases' / OTHER).exists())
        with self.assertRaises(OSError):
            install(OTHER, html(OTHER), self.root, fetch=lambda *_: (_ for _ in ()).throw(OSError('offline')))
        self.assertEqual((self.root / 'current/index.html').read_bytes(), html())

    def test_timed_out_deployment_does_not_switch_late(self):
        install(RELEASE, html(), self.root, fetch=mock_download)
        with patch('tools.web_release.time.monotonic', side_effect=[0, 0, 241]):
            with self.assertRaises(TimeoutError):
                install(OTHER, html(OTHER), self.root, fetch=mock_download)
        self.assertEqual((self.root / 'current/index.html').read_bytes(), html())

    def test_manifest_path_traversal_rejected(self):
        def bad_manifest(url, limit):
            data = json.loads(mock_download(url, limit))
            data['files'][0]['path'] = '../escape'
            return json.dumps(data).encode()
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            install(RELEASE, html(), self.root, fetch=bad_manifest)

    def test_conflicting_release_keeps_current(self):
        install(RELEASE, html(), self.root, fetch=mock_download)
        with self.assertRaises(ValueError):
            install(RELEASE, html() + b'changed', self.root, fetch=mock_download)
        self.assertEqual((self.root / 'current/index.html').read_bytes(), html())

    def test_failed_switch_keeps_current(self):
        install(RELEASE, html(), self.root, fetch=mock_download)
        import os
        replace = os.replace
        def fail_link(src, dst):
            if Path(dst).name == 'current':
                raise OSError('simulated failure')
            return replace(src, dst)
        with patch('tools.web_release.os.replace', side_effect=fail_link):
            with self.assertRaises(OSError):
                install(OTHER, html(OTHER), self.root, fetch=mock_download)
        self.assertEqual((self.root / 'current/index.html').read_bytes(), html())
        self.assertEqual(list(self.root.glob('.current-*')), [])

    def test_invalid_release_or_html_rejected(self):
        for release, data in [('../bad', html()), (RELEASE, html(OTHER)),
                              (RELEASE, b'not html'), (RELEASE, b'x' * (MAX_HTML_BYTES + 1)),
                              (RELEASE, b'\xff')]:
            with self.subTest(release=release, size=len(data)), self.assertRaises(ValueError):
                validate(release, data)


class EndpointTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(__file__).resolve().parents[1]
        self.app = Quart(__name__)
        env = {'app': self.app, 'request': request, 'wraps': wraps, 'hmac': hmac,
               'ci_token': 'test-secret', 'asyncio': asyncio, 'MAX_HTML_BYTES': MAX_HTML_BYTES, 'URLError': URLError,
               'install_web_release': lambda r, h: install(r, h, self.tmp.name, fetch=mock_download)}
        for file, name in [('app.py', 'ci_access_required'), ('routes/ci.py', 'prod')]:
            tree = ast.parse((root / file).read_text())
            node = next(n for n in tree.body if getattr(n, 'name', '') == name)
            exec(compile(ast.Module(body=[node], type_ignores=[]), file, 'exec'), env)
        self.client = self.app.test_client()

    async def test_authentication_and_deployment(self):
        url = '/ci/production?release=' + RELEASE
        resp = await self.client.post(url, data=html(), headers={'Content-Type': 'text/html'})
        self.assertEqual(resp.status_code, 403)
        resp = await self.client.post(url, data=html(), headers={
            'Content-Type': 'text/html', 'Authorization': 'Bearer test-secret'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual((await resp.get_json())['release'], RELEASE)

    async def test_query_token_still_supported(self):
        resp = await self.client.post('/ci/production?release=' + RELEASE + '&token=test-secret',
                                      data=html(), headers={'Content-Type': 'text/html'})
        self.assertEqual(resp.status_code, 200)

    async def test_get_cannot_deploy_and_bad_type_rejected(self):
        resp = await self.client.get('/ci/production?token=test-secret')
        self.assertEqual(resp.status_code, 405)
        resp = await self.client.post('/ci/production?token=test-secret', json={})
        self.assertEqual(resp.status_code, 415)

    async def test_large_body_rejected(self):
        resp = await self.client.post('/ci/production?token=test-secret', data=b'x' * (MAX_HTML_BYTES + 1),
                                      headers={'Content-Type': 'text/html'})
        self.assertEqual(resp.status_code, 413)


if __name__ == '__main__':
    unittest.main()
