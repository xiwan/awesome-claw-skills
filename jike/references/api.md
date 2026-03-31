# Jike API Reference

## Base URL

```
https://api.ruguoapp.com
```

## Required Headers

```
Origin: https://web.okjike.com
User-Agent: Mozilla/5.0 (...)
Content-Type: application/json
x-jike-access-token: <access_token>
```

## Authentication

### Create Login Session

```
POST /1.0/readability/createLoginLinkSession
Body: {"uuid": "<uuid>"}
```

### Poll Login Session

```
POST /1.0/readability/loginWithLinkSession
Body: {"uuid": "<uuid>"}

Success Response Headers:
  x-jike-access-token: <new_access_token>
  x-jike-refresh-token: <new_refresh_token>
```

### Refresh Tokens

```
POST /app_auth_tokens.refresh
Headers:
  x-jike-refresh-token: <refresh_token>

Response Headers:
  x-jike-access-token: <new_access_token>
  x-jike-refresh-token: <new_refresh_token>
```

## Feed

### Following Feed

```
POST /1.0/personalUpdate/followingUpdates
Body: {"limit": 20}
```

## Posts

### Create Post

```
POST /1.0/originalPosts/create
Body: {
  "content": "Hello",
  "pictureKeys": []
}
```

### Delete Post

```
POST /1.0/originalPosts/remove
Body: {"id": "<post_id>"}
```

## Comments

### Add Comment

```
POST /1.0/comments/add
Body: {
  "targetType": "ORIGINAL_POST",
  "targetId": "<post_id>",
  "content": "Nice!",
  "syncToPersonalUpdates": false,
  "pictureKeys": [],
  "force": false
}
```

### Delete Comment

```
POST /1.0/comments/remove
Body: {
  "id": "<comment_id>",
  "targetType": "ORIGINAL_POST"
}
```

## Search

```
POST /1.0/search/integrate
Body: {
  "keyword": "AI",
  "limit": 20
}
```

## User

### Get Profile

```
GET /1.0/users/profile?username=<username>
```

### Get User Posts

```
POST /1.0/userPost/listMore
Body: {"username": "<username>"}
```

## Notifications

### Unread Count

```
GET /1.0/notifications/unread
```

### List Notifications

```
POST /1.0/notifications/list
Body: {}
```
