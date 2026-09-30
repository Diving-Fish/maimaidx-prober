from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch
import verify_cdn
from upload_oss import release_base

RELEASE = 'a' * 40 + '-1-1'


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'index.html').write_text(release_base(RELEASE))
        (self.root / 'font.woff2').write_bytes(b'font')
        patcher = patch('verify_cdn.time.sleep')
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def response(headers):
        response = MagicMock()
        response.__enter__.return_value.headers = headers
        return response

    def test_font_missing_cors_warns_but_allows_local_fallback(self):
        with patch('verify_cdn.urlopen', side_effect=[
            self.response({'Content-Type': 'font/woff2'}),
            self.response({'Content-Type': 'text/html'}),
        ]), patch('builtins.print') as output:
            verify_cdn.verify(self.root, RELEASE)
        self.assertTrue(any('local fallback' in str(call) for call in output.call_args_list))

    def test_public_font_and_html_are_accepted(self):
        with patch('verify_cdn.urlopen', side_effect=[
            self.response({'Content-Type': 'font/woff2', 'Access-Control-Allow-Origin': '*'}),
            self.response({'Content-Type': 'text/html; charset=utf-8'}),
        ]):
            verify_cdn.verify(self.root, RELEASE)

    def test_html_fallback_for_asset_is_rejected(self):
        with patch('verify_cdn.urlopen', return_value=self.response({'Content-Type': 'text/html'})):
            with self.assertRaisesRegex(ValueError, 'Content-Type'):
                verify_cdn.verify(self.root, RELEASE)
