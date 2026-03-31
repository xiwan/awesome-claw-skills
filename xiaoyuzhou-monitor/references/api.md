# 小宇宙 API Reference

## Base URLs

| API | URL | 用途 |
|-----|-----|------|
| 公开 API | `https://api.xiaoyuzhoufm.com` | 播客内容、评论 |
| 主播 API | `https://podcaster-api.xiaoyuzhoufm.com` | 订阅者、统计数据 |
| 认证 API | `https://api.ruguoapp.com` | Token 刷新（与即刻共用） |

## Required Headers

```
x-jike-access-token: <access_token>
x-jike-refresh-token: <refresh_token>
Content-Type: application/json
Origin: https://www.xiaoyuzhoufm.com
```

主播 API 额外需要：
```
x-pid: <podcast_id>
```

## Authentication

### Refresh Tokens

```
POST https://api.ruguoapp.com/app_auth_tokens.refresh
Headers:
  x-jike-refresh-token: <refresh_token>

Response Headers:
  x-jike-access-token: <new_access_token>
  x-jike-refresh-token: <new_refresh_token>
```

## Podcaster API (主播后台)

### Episode List

获取单集列表（含播放统计）

```
POST /v1/episode/list
Body: {
  "pid": "<podcast_id>",
  "limit": 20
}

Response:
{
  "data": [
    {
      "eid": "...",
      "title": "...",
      "stats": {
        "playCount": 123,
        "clapCount": 10,
        "commentCount": 5,
        "favoriteCount": 3
      }
    }
  ],
  "total": 16
}
```

### Subscriber List

获取订阅者列表

```
POST /v1/subscriber/list
Body: {
  "pid": "<podcast_id>",
  "skip": 0,
  "limit": 100
}

Response:
{
  "data": [
    {
      "uid": "...",
      "nickname": "...",
      "avatar": "...",
      "gender": "MALE",
      "province": "广东",
      "subscribedAt": "2026-01-15T..."
    }
  ],
  "total": 209
}
```

## Public API

### Podcast Info

```
GET /v1/podcast/<podcast_id>

Response:
{
  "data": {
    "pid": "...",
    "title": "...",
    "description": "...",
    "subscriptionCount": 209,
    "episodeCount": 16
  }
}
```

### Episode Comments

```
POST /v1/comment/listPrimary
Body: {
  "eid": "<episode_id>",
  "order": "HOT",
  "limit": 20
}
```

## Notes

1. **Token 有效期**：Access Token 约 1 小时，Refresh Token 几个月
2. **完播率**：API 不返回完播率，需要从主播后台手动导出 Excel
3. **订阅者隐私**：部分用户可能隐藏地区等信息
