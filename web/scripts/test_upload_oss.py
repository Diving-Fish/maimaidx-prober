import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import upload_oss as publisher

RELEASE = 'a' * 40 + '-1-1'


class ServerError(Exception):
    status = 409
    code = 'FileAlreadyExists'


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'index.html').write_text(f'<script src="{publisher.release_base(RELEASE)}app.js"></script>')
        (self.root / 'app.js').write_text('console.log(1)')
        (self.root / 'app.js.map').write_text('private source')
        (self.root / 'font.woff2').write_bytes(b'font')
        self.bucket = Mock()
        self.sdk = SimpleNamespace(Auth=Mock(), Bucket=Mock(return_value=self.bucket),
                                   exceptions=SimpleNamespace(ServerError=ServerError))
        env = patch.dict(os.environ, OSS_ACCESS_KEY_ID='test', OSS_ACCESS_KEY_SECRET='test')
        env.start()
        self.addCleanup(env.stop)

    def test_plan_omits_maps_sets_mime_and_publishes_html_last(self):
        files = publisher.plan(self.root, RELEASE)
        self.assertEqual([p.name for p, _, _ in files], ['app.js', 'font.woff2', 'index.html'])
        self.assertEqual(files[1][2]['Content-Type'], 'font/woff2')
        self.assertEqual(files[0][2]['Cache-Control'], publisher.CACHE)
        self.assertTrue(all(k.startswith(publisher.PREFIX + RELEASE + '/') for _, k, _ in files))

    def test_wrong_cdn_release_is_rejected_before_network(self):
        with self.assertRaises(ValueError):
            publisher.upload(self.root, 'b' * 40 + '-1-1', self.sdk)
        self.sdk.Bucket.assert_not_called()

    def test_failed_asset_does_not_publish_html(self):
        self.bucket.put_object_from_file.side_effect = RuntimeError('network')
        with self.assertRaises(RuntimeError):
            publisher.upload(self.root, RELEASE, self.sdk)
        self.assertEqual(self.bucket.put_object_from_file.call_count, 1)

    def test_identical_existing_objects_can_be_retried(self):
        publisher.prepare_manifest(self.root, RELEASE)
        files = {key: (p, h) for p, key, h in publisher.plan(self.root, RELEASE)}
        self.bucket.put_object_from_file.side_effect = ServerError()
        self.bucket.head_object.side_effect = lambda k: SimpleNamespace(
            headers={'x-oss-meta-sha256': files[k][1]['x-oss-meta-sha256']},
            content_length=files[k][0].stat().st_size)
        publisher.upload(self.root, RELEASE, self.sdk)
        self.assertEqual(self.bucket.put_object_from_file.call_count, 4)

    def test_different_existing_content_is_not_overwritten(self):
        self.bucket.put_object_from_file.side_effect = ServerError()
        self.bucket.head_object.return_value = SimpleNamespace(headers={}, content_length=0)
        with self.assertRaises(ValueError):
            publisher.upload(self.root, RELEASE, self.sdk)
        self.assertEqual(self.bucket.put_object_from_file.call_count, 1)

    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            publisher.plan(self.root, '../production')


if __name__ == '__main__':
    unittest.main()
