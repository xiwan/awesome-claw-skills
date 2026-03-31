#!/usr/bin/env python3
"""
Jike API Client (standalone)
Run directly: python3 scripts/client.py feed --access-token T --refresh-token T
No pip install required — only needs `requests`.

Author: Claude Opus 4.5
"""

import argparse
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Optional, List

import requests

API_BASE = "https://api.ruguoapp.com"
UPTOKEN_URL = "https://upload.jike.ruguoapp.com/token"
QINIU_UPLOAD_URL = "https://up.qbox.me/"
REQUEST_TIMEOUT_SEC = 15
HEADERS = {
    "Origin": "https://web.okjike.com",
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 "
        "Mobile/15E148 Safari/604.1"
    ),
    "Accept": "application/json, text/plain, */*",
    "DNT": "1",
}


def _call(method: str, path: str, access_token: str, refresh_token: str, retry: bool = True, **kwargs):
    hdrs = {**HEADERS, "Content-Type": "application/json", "x-jike-access-token": access_token}
    resp = requests.request(
        method,
        f"{API_BASE}{path}",
        headers=hdrs,
        timeout=REQUEST_TIMEOUT_SEC,
        **kwargs,
    )

    if resp.status_code == 401 and retry:
        new_access, new_refresh = _refresh(refresh_token, access_token)
        return _call(method, path, new_access, new_refresh, retry=False, **kwargs)

    resp.raise_for_status()
    return resp.json() if resp.content else {}


def _refresh(refresh_token: str, access_token: str = "") -> tuple:
    resp = requests.post(
        f"{API_BASE}/app_auth_tokens.refresh",
        headers={**HEADERS, "Content-Type": "application/json", "x-jike-refresh-token": refresh_token},
        json={},
        timeout=REQUEST_TIMEOUT_SEC,
    )
    resp.raise_for_status()
    return (
        resp.headers.get("x-jike-access-token", access_token),
        resp.headers.get("x-jike-refresh-token", refresh_token),
    )


# ── API Functions ─────────────────────────────────────────

def get_uptoken() -> str:
    """获取七牛云上传 token"""
    resp = requests.get(UPTOKEN_URL, params={"bucket": "jike"}, timeout=REQUEST_TIMEOUT_SEC)
    resp.raise_for_status()
    return resp.json()["uptoken"]


def upload_picture(file_path: str) -> str:
    """上传单张图片到七牛云，返回 picture key"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type or not mime_type.startswith("image"):
        raise ValueError(f"Not an image file: {file_path}")
    
    uptoken = get_uptoken()
    with open(path, "rb") as f:
        files = {
            "token": (None, uptoken),
            "file": (path.name, f, mime_type),
        }
        resp = requests.post(QINIU_UPLOAD_URL, files=files, timeout=30)
    
    resp.raise_for_status()
    result = resp.json()
    if result.get("success"):
        return result["key"]
    raise RuntimeError(f"Upload failed: {result}")


def upload_pictures(file_paths: List[str]) -> List[str]:
    """上传多张图片，返回 picture keys 列表"""
    return [upload_picture(p) for p in file_paths]


def feed(at: str, rt: str, limit: int = 20, load_more_key: Optional[str] = None) -> dict:
    body: dict = {"limit": limit}
    if load_more_key:
        body["loadMoreKey"] = load_more_key
    return _call("POST", "/1.0/personalUpdate/followingUpdates", at, rt, json=body)


def create_post(at: str, rt: str, content: str, picture_keys: Optional[list] = None, topic_id: Optional[str] = None) -> dict:
    body = {"content": content, "pictureKeys": picture_keys or []}
    if topic_id:
        body["submitToTopic"] = topic_id
    return _call("POST", "/1.0/originalPosts/create", at, rt, json=body)


def delete_post(at: str, rt: str, post_id: str) -> dict:
    return _call("POST", "/1.0/originalPosts/remove", at, rt, json={"id": post_id})


def add_comment(at: str, rt: str, post_id: str, content: str, target_type: str = "ORIGINAL_POST") -> dict:
    return _call("POST", "/1.0/comments/add", at, rt, json={
        "targetType": target_type, "targetId": post_id,
        "content": content, "syncToPersonalUpdates": False, "pictureKeys": [], "force": False,
    })


def delete_comment(at: str, rt: str, comment_id: str, target_type: str = "ORIGINAL_POST") -> dict:
    return _call("POST", "/1.0/comments/remove", at, rt, json={"id": comment_id, "targetType": target_type})


def search(at: str, rt: str, keyword: str, limit: int = 20) -> dict:
    return _call("POST", "/1.0/search/integrate", at, rt, json={"keyword": keyword, "limit": limit})


def profile(at: str, rt: str, username: str) -> dict:
    return _call("GET", f"/1.0/users/profile?username={username}", at, rt)


def user_posts(at: str, rt: str, username: str, load_more_key: Optional[dict] = None) -> dict:
    body: dict = {"username": username}
    if load_more_key:
        body["loadMoreKey"] = load_more_key
    return _call("POST", "/1.0/userPost/listMore", at, rt, json=body)


def notifications(at: str, rt: str) -> dict:
    return {
        "unread": _call("GET", "/1.0/notifications/unread", at, rt),
        "list": _call("POST", "/1.0/notifications/list", at, rt, json={}),
    }


# ── CLI ───────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Jike API client")
    access_env = os.getenv("JIKE_ACCESS_TOKEN") or None  # coerce "" -> None
    refresh_env = os.getenv("JIKE_REFRESH_TOKEN") or None  # coerce "" -> None
    p.add_argument(
        "--access-token",
        default=access_env,
        required=access_env is None,
        help="Access token (or set JIKE_ACCESS_TOKEN)",
    )
    p.add_argument(
        "--refresh-token",
        default=refresh_env,
        required=refresh_env is None,
        help="Refresh token (or set JIKE_REFRESH_TOKEN)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("feed").add_argument("--limit", type=int, default=20)
    sp = sub.add_parser("post"); sp.add_argument("--content", required=True); sp.add_argument("--topic-id", default=None); sp.add_argument("--pictures", nargs="*", default=[], help="Image file paths to upload")
    sp = sub.add_parser("upload"); sp.add_argument("--files", nargs="+", required=True, help="Image file paths to upload")
    sub.add_parser("delete-post").add_argument("--post-id", required=True)
    sp = sub.add_parser("comment"); sp.add_argument("--post-id", required=True); sp.add_argument("--content", required=True); sp.add_argument("--target-type", default="ORIGINAL_POST", choices=["ORIGINAL_POST", "REPOST"])
    sp = sub.add_parser("delete-comment"); sp.add_argument("--comment-id", required=True); sp.add_argument("--target-type", default="ORIGINAL_POST", choices=["ORIGINAL_POST", "REPOST"])
    sp = sub.add_parser("search"); sp.add_argument("--keyword", required=True); sp.add_argument("--limit", type=int, default=20)
    sub.add_parser("profile").add_argument("--username", required=True)
    sub.add_parser("user-posts").add_argument("--username", required=True)
    sub.add_parser("notifications")

    args = p.parse_args()
    at, rt = args.access_token, args.refresh_token

    dispatch = {
        "feed": lambda: feed(at, rt, args.limit),
        "post": lambda: create_post(at, rt, args.content, picture_keys=upload_pictures(args.pictures) if args.pictures else None, topic_id=args.topic_id),
        "upload": lambda: {"keys": upload_pictures(args.files)},
        "delete-post": lambda: delete_post(at, rt, args.post_id),
        "comment": lambda: add_comment(at, rt, args.post_id, args.content, args.target_type),
        "delete-comment": lambda: delete_comment(at, rt, args.comment_id, args.target_type),
        "search": lambda: search(at, rt, args.keyword, args.limit),
        "profile": lambda: profile(at, rt, args.username),
        "user-posts": lambda: user_posts(at, rt, args.username),
        "notifications": lambda: notifications(at, rt),
    }

    try:
        result = dispatch[args.cmd]()
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
    except requests.RequestException as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
