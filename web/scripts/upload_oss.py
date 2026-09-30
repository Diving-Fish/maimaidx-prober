"""Upload a versioned web build to the shared Aliyun OSS bucket."""
import argparse
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import sys

CONFIG = json.loads((Path(__file__).resolve().parents[1] / 'deploy/config.json').read_text())
CDN = CONFIG['cdnBase']
PREFIX = CONFIG['objectPrefix']
ENDPOINT = CONFIG['ossEndpoint']
BUCKET = CONFIG['ossBucket']
CACHE = "public, max-age=31536000, immutable"
TYPES = {".js": "application/javascript", ".css": "text/css", ".html": "text/html",
         ".woff": "font/woff", ".woff2": "font/woff2", ".ico": "image/x-icon"}


def release_base(release):
    if not re.fullmatch(r"[0-9a-f]{40}-[0-9]+-[0-9]+", release):
        raise ValueError("Release must be <40-character commit SHA>-<run ID>-<attempt>")
    return CDN + PREFIX + release + "/"


def plan(directory, release):
    base = release_base(release)
    root = Path(directory)
    index = root / "index.html"
    if not index.is_file() or base not in index.read_text(encoding="utf-8"):
        raise ValueError("index.html is missing or does not reference this CDN release")
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Build must not contain symlinks")
        if not path.is_file() or path.suffix == ".map":
            continue
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        content_type = TYPES.get(path.suffix) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        files.append((path, PREFIX + release + "/" + relative, {
            "Content-Type": content_type,
            "Cache-Control": CACHE,
            "x-oss-forbid-overwrite": "true",
            "x-oss-meta-sha256": digest,
        }))
    # Publish the HTML snapshot only after every dependency has succeeded.
    files.sort(key=lambda item: item[0] == index)
    return files


def prepare_manifest(directory, release):
    root = Path(directory)
    files = []
    for path, _, headers in plan(directory, release):
        relative = path.relative_to(root).as_posix()
        if relative == 'asset-manifest.json':
            continue
        files.append({'path': relative, 'size': path.stat().st_size,
                      'sha256': headers['x-oss-meta-sha256']})
    manifest = {'release': release, 'files': files}
    (root / 'asset-manifest.json').write_text(json.dumps(manifest, sort_keys=True) + '\n')


def upload(directory, release, sdk):
    prepare_manifest(directory, release)
    files = plan(directory, release)
    for name in ("OSS_ACCESS_KEY_ID", "OSS_ACCESS_KEY_SECRET"):
        if not os.environ.get(name):
            raise ValueError(f"Missing required secret: {name}")
    bucket = sdk.Bucket(sdk.Auth(os.environ["OSS_ACCESS_KEY_ID"], os.environ["OSS_ACCESS_KEY_SECRET"]),
                        ENDPOINT, BUCKET, connect_timeout=60)
    for path, key, headers in files:
        try:
            bucket.put_object_from_file(key, str(path), headers=headers)
        except sdk.exceptions.ServerError as error:
            if error.status != 409 or error.code != "FileAlreadyExists":
                raise
            existing = bucket.head_object(key)
            if (existing.headers.get("x-oss-meta-sha256") != headers["x-oss-meta-sha256"]
                    or existing.content_length != path.stat().st_size):
                raise ValueError(f"Refusing to replace different content: {key}") from None
        print(f"Uploaded: {key}")
    return release_base(release) + "index.html"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?")
    parser.add_argument("--print-base", action="store_true")
    parser.add_argument("--release", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.print_base:
            print(release_base(args.release))
            return 0
        if not args.directory:
            parser.error("directory is required unless --print-base is used")
        if args.dry_run:
            prepare_manifest(args.directory, args.release)
            for path, key, headers in plan(args.directory, args.release):
                print(json.dumps({"key": key, "size": path.stat().st_size, "headers": headers}))
        else:
            import oss2
            print("HTML snapshot: " + upload(args.directory, args.release, oss2))
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    except Exception:
        # SDK errors may include signed request details; never dump them into Actions logs.
        print("OSS upload failed; check credentials, bucket permissions and connectivity.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
