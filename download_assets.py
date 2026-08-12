#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
import urllib.request
from pathlib import Path


def sniff(path: Path):
    header = path.read_bytes()[:16]
    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return ".webp"
    if header[4:8] == b"ftyp" or b"ftyp" in header:
        return ".mp4"
    return None


def main():
    parser = argparse.ArgumentParser(description="Download remote_assets and update manifest attachments")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--staging-dir", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.staging_dir.mkdir(parents=True, exist_ok=True)
    attachments = data.get("attachments") or []
    failures = []
    for index, item in enumerate(data.get("remote_assets") or [], 1):
        suggested = Path(item.get("suggested_name") or f"asset-{index:02d}")
        part = args.staging_dir / (suggested.name + ".part")
        request = urllib.request.Request(item["url"], headers={"User-Agent": "Mozilla/5.0", "Referer": data.get("source_url", "")})
        try:
            with urllib.request.urlopen(request, timeout=60) as response, part.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            if part.stat().st_size == 0:
                raise ValueError("empty response")
            suffix = sniff(part)
            if not suffix:
                guessed = mimetypes.guess_extension(response.headers.get_content_type())
                suffix = guessed if guessed in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4"} else suggested.suffix
            if not suffix:
                raise ValueError("unknown file type")
            final = args.staging_dir / (suggested.stem + (".jpg" if suffix == ".jpeg" else suffix))
            os.replace(part, final)
            attachments.append({"source": str(final.resolve()), "name": final.name, "kind": item.get("kind", "asset")})
        except Exception as exc:
            if part.exists():
                part.unlink()
            failures.append({"url": item["url"], "error": str(exc)})
    data["attachments"] = attachments
    data["download_failures"] = failures
    args.manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"downloaded": len(attachments), "failed": len(failures)}, ensure_ascii=False))
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
