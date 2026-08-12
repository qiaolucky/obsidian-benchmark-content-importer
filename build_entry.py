#!/usr/bin/env python3
import argparse
import json
import re
import shutil
from pathlib import Path


INVALID = re.compile(r'[/:*?"<>|\\]')


def safe_name(value: str) -> str:
    value = INVALID.sub("／", value).strip().rstrip(".")
    return re.sub(r"\s+", " ", value) or "未命名"


def display(value, fallback="未获取"):
    if value is None or value == "":
        return fallback
    return str(value)


def replace_assets(text: str, attachments: list[dict]) -> str:
    names = {Path(item["name"]).stem: item["name"] for item in attachments}
    for key, name in names.items():
        text = text.replace(f"{{{{asset:{key}}}}}", f"![[附件/{name}]]")
    return text


def main():
    parser = argparse.ArgumentParser(description="Build one Obsidian benchmark-content entry")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--update", action="store_true", help="Allow replacing an existing matching entry")
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    required = ["platform", "content_id", "source_url", "content_type", "title"]
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise SystemExit("missing manifest fields: " + ", ".join(missing))

    folder = safe_name(f"{data['title']}_{data['platform']}_{data['content_id']}")
    target = args.output_dir / folder
    if target.exists() and not args.update:
        raise SystemExit(f"target already exists; duplicate or update required: {target}")
    attachment_dir = target / "附件"
    attachment_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for item in data.get("attachments", []):
        source = Path(item["source"]).expanduser().resolve()
        if not source.is_file() or source.stat().st_size == 0:
            raise SystemExit(f"invalid attachment source: {source}")
        name = safe_name(item["name"])
        destination = attachment_dir / name
        shutil.copy2(source, destination)
        copied.append({**item, "name": name, "bytes": destination.stat().st_size})

    body = replace_assets(data.get("body_markdown", "").strip(), copied)
    extracted = data.get("extracted_text", "").strip() or "不适用"
    metrics = data.get("metrics") or {}
    cover_file = next((i["name"] for i in copied if i.get("kind") == "cover"), None)
    video_file = next((i["name"] for i in copied if i.get("kind") == "video"), None)
    cover_embed = f"![[附件/{cover_file}]]\n\n" if cover_file else ""
    video_value = f"![[附件/{video_file}]]" if video_file else "不适用"

    lines = [
        f"# {data['title']}", "", cover_embed.rstrip(), "",
        "## 笔记信息", "",
        f"- 笔记链接：[{data['source_url']}]({data['source_url']})",
        f"- 笔记类型：{data['content_type']}",
        f"- 笔记标题：{data['title']}",
        "- 笔记内容：见下方“笔记内容”",
        "- 视频文字/图片文字：见下方“视频文字/图片文字”",
        f"- 点赞量：{display(metrics.get('likes'))}",
        f"- 收藏量：{display(metrics.get('favorites'))}",
        f"- 评论量：{display(metrics.get('comments'))}",
        f"- 分享量：{display(metrics.get('shares'))}",
        f"- 博主昵称：{display(data.get('creator_nickname'))}",
        f"- 笔记视频时长：{display(data.get('duration'), '不适用')}",
        f"- 笔记封面链接：{display(data.get('cover_url'))}",
        f"- 笔记视频：{video_value}",
        f"- 内容ID：{data['content_id']}",
    ]
    if data.get("author"):
        lines.append(f"- 作者：{data['author']}")
    if data.get("published_at"):
        lines.append(f"- 发布时间：{data['published_at']}")
    if data.get("collected_at"):
        lines.append(f"- 数据采集时间：{data['collected_at']}")
    lines += ["", "## 视频文字/图片文字", "", extracted, "", "## 笔记内容", "", body or "未获取", ""]
    note = "\n".join(part for part in lines if part is not None).replace("\n\n\n", "\n\n")
    (target / "笔记信息.md").write_text(note, encoding="utf-8")

    if extracted != "不适用":
        kind = "视频文字" if video_file else "图片文字"
        (attachment_dir / f"{kind}.md").write_text(f"# {kind}\n\n{extracted}\n", encoding="utf-8")
    record = {
        "platform": data["platform"],
        "content_id": data["content_id"],
        "source_url": data["source_url"],
        "collected_at": data.get("collected_at"),
        "attachments": copied,
        "missing_metrics_are_not_zero": True,
    }
    (attachment_dir / "处理记录.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target.resolve())


if __name__ == "__main__":
    main()
