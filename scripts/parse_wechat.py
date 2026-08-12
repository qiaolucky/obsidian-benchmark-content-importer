#!/usr/bin/env python3
import argparse
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    from bs4 import BeautifulSoup
    from markdownify import markdownify
except ImportError as exc:
    raise SystemExit("Install beautifulsoup4 and markdownify in an isolated environment") from exc


def main():
    parser = argparse.ArgumentParser(description="Parse an acquired WeChat article HTML page")
    parser.add_argument("html", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-url")
    args = parser.parse_args()
    html = args.html.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    body = soup.select_one("#js_content")
    if body is None:
        raise SystemExit("article body not found; page may require verification")
    source_url = args.source_url or (soup.select_one('meta[property="og:url"]') or {}).get("content") or ""
    content_id = source_url.rstrip("/").rsplit("/", 1)[-1]
    remote_assets = []
    for image in body.find_all("img"):
        url = image.get("data-src") or image.get("src")
        if not url or url.startswith("data:"):
            image.decompose(); continue
        index = len(remote_assets) + 1
        url = url.replace("&amp;", "&")
        fmt = parse_qs(urlparse(url).query).get("wx_fmt", [""])[0].lower()
        suffix = fmt if fmt in {"jpg", "jpeg", "png", "gif", "webp"} else "jpg"
        remote_assets.append({"url": url, "suggested_name": f"{index:02d}.{suffix}", "kind": "image"})
        image.replace_with(f"{{{{asset:{index:02d}}}}}")
    for tag in body.find_all(["script", "style", "mp-common-videosnap"]):
        tag.decompose()
    body_md = markdownify(str(body), heading_style="ATX").replace("\xa0", " ")
    body_md = re.sub(r"[ \t]+\n", "\n", body_md)
    body_md = re.sub(r"\n{3,}", "\n\n", body_md).strip()
    for marker in ("（完）", "(完)", "全文完"):
        if marker in body_md:
            body_md = body_md.split(marker, 1)[0].rstrip()
            break
    used_assets = {int(value) for value in re.findall(r"\{\{asset:(\d+)\}\}", body_md)}
    remote_assets = [item for index, item in enumerate(remote_assets, 1) if index in used_assets]
    title = soup.select_one("#activity-name")
    account = soup.select_one("#js_name")
    author = soup.select_one("#js_author_name_text")
    cover = (soup.select_one('meta[property="og:image"]') or {}).get("content") or ""
    if cover:
        remote_assets.append({"url": cover, "suggested_name": "封面.jpg", "kind": "cover"})
    published = re.search(r"create_time:\s*'([^']+)'", html)
    result = {
        "platform": "公众号", "content_id": content_id, "source_url": source_url,
        "content_type": "公众号文章", "title": title.get_text(" ", strip=True) if title else "未命名",
        "body_markdown": body_md, "extracted_text": "",
        "metrics": {"likes": "微信公众号网页未返回可读取数值", "favorites": "平台未公开", "comments": "微信公众号网页未返回可读取数值", "shares": "平台未公开"},
        "creator_nickname": account.get_text(" ", strip=True) if account else "未获取",
        "author": author.get_text(" ", strip=True) if author else "",
        "published_at": published.group(1) if published else "", "duration": "不适用",
        "cover_url": cover, "video_url": "", "collected_at": date.today().isoformat(),
        "attachments": [], "remote_assets": remote_assets
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
