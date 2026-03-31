---
name: xiaoyuzhou-monitor
description: >
  小宇宙播客数据监控。获取播放量、完播率、订阅变化、评论。
  支持 Token 自动刷新。需要主播账号登录凭据。
  Triggers on: "小宇宙数据", "播客数据", "播放量", "完播率", "订阅者"
---

# 小宇宙监控 Skill

监控播客在小宇宙的播放数据、订阅者、评论等。

## Features

- 📊 单集数据（播放量、完播率、点赞、评论）
- 👥 订阅者列表
- 📈 播客基本信息
- 💬 评论获取
- 🔄 Token 自动刷新（401 时自动续期）

## Quick Start

### 1. 获取凭据

1. 打开 https://podcaster.xiaoyuzhoufm.com（主播后台）
2. 登录
3. F12 → Network → 随便点一下
4. 找 Request Headers 里的 `x-jike-access-token` 和 `x-jike-refresh-token`

### 2. 配置凭据

保存到 `~/clawd/secrets/xiaoyuzhou.json`：

```json
{
  "podcastId": "YOUR_PODCAST_ID",
  "accessToken": "YOUR_ACCESS_TOKEN",
  "refreshToken": "YOUR_REFRESH_TOKEN"
}
```

**获取 Podcast ID**：在小宇宙打开你的播客页面，URL 里的那串 ID 就是。

### 3. 使用

```bash
# 获取单集列表（含播放数据）
python3 scripts/client.py episodes --limit 10

# 获取订阅者
python3 scripts/client.py subscribers --limit 100

# 获取播客信息
python3 scripts/client.py info

# 获取单集评论
python3 scripts/client.py comments --episode-id <eid>

# 手动刷新 token
python3 scripts/client.py refresh
```

## Commands

| Command | Description | Key Args |
|---------|-------------|----------|
| `episodes` | 单集列表（含 stats） | `--limit` |
| `subscribers` | 订阅者列表 | `--skip`, `--limit` |
| `info` | 播客基本信息 | — |
| `comments` | 单集评论 | `--episode-id`, `--limit` |
| `refresh` | 手动刷新 token | — |

## Token 机制

小宇宙使用与即刻相同的双 Token 机制：

| Token | 有效期 | 用途 |
|-------|--------|------|
| Access Token | ~1 小时 | 实际 API 调用 |
| Refresh Token | 几个月 | 换新 Access Token |

### 自动刷新

脚本内置 401 自动刷新逻辑：
1. API 返回 401 时，自动用 Refresh Token 换新 Access Token
2. 新 Token 返回在响应 Header 里
3. 更新凭据文件

如果 Refresh Token 也过期了，需要重新登录主播后台获取新凭据。

## API Endpoints

小宇宙有两套 API：

| API | Base URL | 用途 |
|-----|----------|------|
| 公开 API | `https://api.xiaoyuzhoufm.com` | 播客内容、评论 |
| 主播 API | `https://podcaster-api.xiaoyuzhoufm.com` | 订阅者、详细统计 |

主播 API 需要额外的 `x-pid` Header。

## 数据字段说明

### Episode Stats

```json
{
  "playCount": 123,      // 播放次数
  "clapCount": 10,       // 点赞数
  "commentCount": 5,     // 评论数
  "favoriteCount": 3     // 收藏数
}
```

注意：完播率（finishRate）需要从主播后台导出的 Excel 获取，API 不提供。

## 依赖

- Python 3.8+
- `requests`

## License

MIT
