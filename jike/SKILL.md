---
name: jike
description: >
  Interact with Jike (即刻) social network — QR login, feed reading, posting,
  commenting, searching, and user profile lookup. Use when Claude needs to:
  (1) Log into Jike via QR code scan, (2) Read following/discovery feeds,
  (3) Create, read, or delete posts, (4) Add or remove comments,
  (5) Search content or users, (6) Check notifications.
  Triggers on: "jike", "即刻", "刷即刻", "发即刻", "jike feed", "jike post".
---

# Jike Skill

即刻社交网络客户端 — 给人用，也给 AI agent 用。

## Features

- 🔐 QR 扫码登录（无需密码）
- 📖 刷关注流 / 发现流
- ✍️ 发帖、删帖
- 💬 评论、删评论
- 🔍 搜索内容和用户
- 🔔 查看通知
- 🔄 Token 自动刷新（401 时自动续期）

## Quick Start

### 1. 认证（首次使用）

```bash
python3 scripts/auth.py
```

用即刻 App 扫描终端里的二维码，成功后会输出 `access_token` 和 `refresh_token`。

保存到凭据文件 `~/clawd/secrets/jike.json`：

```json
{
  "access_token": "YOUR_ACCESS_TOKEN",
  "refresh_token": "YOUR_REFRESH_TOKEN"
}
```

### 2. 使用

```bash
# 使用 wrapper（自动加载凭据）
bash scripts/jike-wrapper.sh feed --limit 5
bash scripts/jike-wrapper.sh post --content "Hello"
bash scripts/jike-wrapper.sh search --keyword "AI"

# 或直接使用环境变量
export JIKE_ACCESS_TOKEN="..."
export JIKE_REFRESH_TOKEN="..."
python3 scripts/client.py feed --limit 5
```

## Commands

| Command | Description | Key Args |
|---------|-------------|----------|
| `feed` | 关注流 | `--limit` |
| `post` | 发帖 | `--content` |
| `delete-post` | 删帖 | `--post-id` |
| `comment` | 评论 | `--post-id`, `--content` |
| `delete-comment` | 删评论 | `--comment-id` |
| `search` | 搜索 | `--keyword`, `--limit` |
| `profile` | 用户资料 | `--username` |
| `user-posts` | 用户帖子 | `--username`, `--limit` |
| `notifications` | 通知 | — |

## Token 机制

即刻使用双 Token 机制（OAuth 2.0 风格）：

| Token | 有效期 | 用途 |
|-------|--------|------|
| Access Token | ~1 小时 | 实际 API 调用 |
| Refresh Token | 几个月 | 换新 Access Token |

### 自动刷新

脚本内置 401 自动刷新逻辑：
1. API 返回 401 时，自动用 Refresh Token 换新 Access Token
2. 新 Token 返回在响应 Header 里
3. 更新凭据文件

如果 Refresh Token 也过期了，需要重新扫码登录。

## 凭据文件

默认路径：`~/clawd/secrets/jike.json`

可通过环境变量 `JIKE_SECRETS_FILE` 自定义。

## 依赖

- Python 3.8+
- `requests`（标准库之外唯一依赖）

## 安全

- 无密码认证 — 仅 QR 扫码（与即刻网页版相同）
- 所有请求需要 `Origin: https://web.okjike.com` Header
- Token 自动刷新，仅需持久化 Refresh Token

## License

MIT
