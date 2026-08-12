#!/usr/bin/env python3
import argparse
import json
import re
from datetime import date
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Parse an acquired Xiaohongshu HTML page")
    parser.add_argument("html", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-url", required=True)
    args = parser.parse_args()
    text = args.html.read_text(encoding="utf-8")
    id_match = re.search(r"(?:item|explore)/([0-9a-f]{24})", args.source_url)
    if not id_match:
        raise SystemExit("note id not found in source URL")
    note_id = id_match.group(1)
    match = re.search(r"<script>window\.__INITIAL_STATE__=(.*?)</script>", text, re.S)
    if not match:
        raise SystemExit("initial state not found; use an authenticated page or export")
    state = json.loads(re.sub(r"\bundefined\b", "null", match.group(1)))
    note = state["note"]["noteDetailMap"][note_id]["note"]
    video = note.get("video") or {}
    duration_ms = video.get("media", {}).get("video", {}).get("duration")
    duration = "不适用"
    if duration_ms:
        total = round(duration_ms / 1000) if duration_ms > 10000 else round(duration_ms)
        duration = f"{total // 60:02d}:{total % 60:02d}"
    images = note.get("imageList") or []
    cover = (images[0].get("urlDefault") or images[0].get("urlPre")) if images else ""
    info = note.get("interactInfo") or {}
    result = {
        "platform": "小红书", "content_id": note_id, "source_url": args.source_url,
        "content_type": "视频" if note.get("type") == "video" else "图文",
        "title": note.get("title") or "未命名", "body_markdown": note.get("desc") or "",
        "extracted_text": "", "metrics": {"likes": info.get("likedCount"), "favorites": info.get("collectedCount"), "comments": info.get("commentCount"), "shares": info.get("shareCount")},
        "creator_nickname": note.get("user", {}).get("nickname"), "duration": duration,
        "cover_url": cover, "video_url": "", "collected_at": date.today().isoformat(),
        "attachments": [], "remote_assets": []
    }
    for index, image in enumerate(images, 1):
        url = image.get("urlDefault") or image.get("urlPre")
        if url:
            name = "封面.jpg" if note.get("type") == "video" and index == 1 else f"{index:02d}.jpg"
            kind = "cover" if index == 1 else "image"
            result["remote_assets"].append({"url": url, "suggested_name": name, "kind": kind})
            if note.get("type") != "video":
                result["body_markdown"] += f"\n\n{{{{asset:{Path(name).stem}}}}}"
    streams = video.get("media", {}).get("stream", {})
    for variants in streams.values():
        if isinstance(variants, list):
            for variant in variants:
                url = variant.get("masterUrl")
                if url:
                    result["video_url"] = url
                    result["remote_assets"].append({"url": url, "suggested_name": "视频.mp4", "kind": "video"})
                    break
        if result["video_url"]:
            break
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
