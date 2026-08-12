#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


FIELDS = ["笔记链接", "笔记类型", "笔记标题", "笔记内容", "视频文字/图片文字", "点赞量", "收藏量", "评论量", "分享量", "博主昵称", "笔记视频时长", "笔记封面链接", "笔记视频"]


def image_kind(path: Path):
    header = path.read_bytes()[:16]
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "webp"
    return None


def main():
    parser = argparse.ArgumentParser(description="Validate one generated Obsidian entry")
    parser.add_argument("entry", type=Path)
    args = parser.parse_args()
    root = args.entry.resolve()
    errors = []
    if {p.name for p in root.iterdir()} != {"笔记信息.md", "附件"}:
        errors.append("root must contain only 笔记信息.md and 附件")
    note_path = root / "笔记信息.md"
    note = note_path.read_text(encoding="utf-8") if note_path.is_file() else ""
    for field in FIELDS:
        if note.count(f"- {field}：") != 1:
            errors.append(f"field must occur once: {field}")
    if note.count("## 视频文字/图片文字") != 1:
        errors.append("视频文字/图片文字 section must occur once")
    for ref in re.findall(r"!\[\[附件/([^\]]+)\]\]", note):
        path = root / "附件" / ref
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty attachment: {ref}")
    for path in (root / "附件").glob("*"):
        if path.stat().st_size == 0:
            errors.append(f"empty attachment: {path.name}")
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
            actual = image_kind(path)
            expected = "jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else path.suffix.lower()[1:]
            if actual != expected:
                errors.append(f"image type mismatch: {path.name} is {actual}")
    record = root / "附件" / "处理记录.json"
    if record.is_file():
        try:
            json.loads(record.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("处理记录.json is invalid")
    if errors:
        print("FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(f"PASS: {root}")


if __name__ == "__main__":
    main()
