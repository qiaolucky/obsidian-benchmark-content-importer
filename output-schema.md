# 输出规范

## 目录

```text
内容标题_平台_内容ID/
├── 笔记信息.md
└── 附件/
    ├── 封面.jpg
    ├── 01.jpg / 01.png
    ├── 视频.mp4
    ├── 视频文字.md
    ├── 图片文字.md
    └── 处理记录.json
```

只生成实际存在的附件。根目录禁止出现其他文件。

## 主笔记字段顺序

1. 笔记链接
2. 笔记类型
3. 笔记标题
4. 笔记内容
5. 视频文字/图片文字
6. 点赞量
7. 收藏量
8. 评论量
9. 分享量
10. 博主昵称
11. 笔记视频时长
12. 笔记封面链接
13. 笔记视频

可补充内容 ID、作者、发布时间、数据采集时间，但不得重复已有字段。

完整正文放在 `## 笔记内容`；完整转写和有效 OCR 放在唯一的 `## 视频文字/图片文字`。字段行可写“见下方”，避免正文重复两遍。

## 清单 JSON

`build_entry.py` 接收：

```json
{
  "platform": "公众号",
  "content_id": "example-id",
  "source_url": "https://example.com/item/example-id",
  "content_type": "公众号文章",
  "title": "标题",
  "body_markdown": "完整正文，可含 {{asset:01}} 占位符",
  "extracted_text": "视频或图片文字",
  "metrics": {
    "likes": "平台未公开",
    "favorites": "平台未公开",
    "comments": "未获取",
    "shares": "平台未公开"
  },
  "creator_nickname": "账号昵称",
  "author": "署名作者",
  "published_at": "2026-08-11 21:00",
  "duration": "不适用",
  "cover_url": "https://...",
  "video_url": "",
  "collected_at": "2026-08-12",
  "attachments": [
    {"source": "/absolute/staging/cover.jpg", "name": "封面.jpg", "kind": "cover"},
    {"source": "/absolute/staging/01.png", "name": "01.png", "kind": "image"}
  ]
}
```

附件 `source` 必须是已经下载并验证的本地文件。`{{asset:01}}` 会替换为 `![[附件/01.png]]`；编号对应附件 `name` 的主文件名。

## 缺失值

- 页面明确不展示：`平台未公开`
- 页面可能展示但本次没有成功取得：`未获取`
- 内容类型不适用：`不适用`
- 不用 `0` 代表缺失。
