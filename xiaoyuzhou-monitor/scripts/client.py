#!/usr/bin/env python3
"""
小宇宙 API 客户端（带自动刷新）
与即刻 skill 保持一致的机制
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

import requests

# API 配置
PODCASTER_API = "https://podcaster-api.xiaoyuzhoufm.com"
PUBLIC_API = "https://api.xiaoyuzhoufm.com"
JIKE_API = "https://api.ruguoapp.com"  # 用于刷新 token

REQUEST_TIMEOUT = 15
HEADERS = {
    "Origin": "https://www.xiaoyuzhoufm.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) Gecko/20100101 Firefox/148.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

SECRETS_FILE = Path(os.getenv("XIAOYUZHOU_SECRETS_FILE", Path.home() / "clawd" / "secrets" / "xiaoyuzhou.json"))


def load_config():
    """加载凭据"""
    if not SECRETS_FILE.exists():
        print(f"❌ 凭据文件不存在: {SECRETS_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(SECRETS_FILE) as f:
        return json.load(f)


def save_config(config):
    """保存凭据（token 刷新后）"""
    SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SECRETS_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print("🔄 Token 已刷新并保存", file=sys.stderr)


def refresh_tokens(refresh_token: str, access_token: str) -> tuple:
    """刷新 token（使用即刻的刷新接口，小宇宙和即刻共用）"""
    resp = requests.post(
        f"{JIKE_API}/app_auth_tokens.refresh",
        headers={
            **HEADERS,
            "x-jike-refresh-token": refresh_token,
        },
        json={},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    new_access = resp.headers.get("x-jike-access-token", access_token)
    new_refresh = resp.headers.get("x-jike-refresh-token", refresh_token)
    return new_access, new_refresh


def call_api(method: str, base_url: str, path: str, config: dict, retry: bool = True, **kwargs):
    """调用 API，自动处理 401 刷新"""
    hdrs = {
        **HEADERS,
        "x-jike-access-token": config["accessToken"],
        "x-jike-refresh-token": config["refreshToken"],
    }
    # 主播 API 需要 x-pid
    if base_url == PODCASTER_API:
        hdrs["x-pid"] = config["podcastId"]
    
    resp = requests.request(
        method,
        f"{base_url}{path}",
        headers=hdrs,
        timeout=REQUEST_TIMEOUT,
        **kwargs,
    )
    
    if resp.status_code == 401 and retry:
        print("⚠️ Token 过期，正在刷新...", file=sys.stderr)
        try:
            new_access, new_refresh = refresh_tokens(config["refreshToken"], config["accessToken"])
            config["accessToken"] = new_access
            config["refreshToken"] = new_refresh
            save_config(config)
            return call_api(method, base_url, path, config, retry=False, **kwargs)
        except Exception as e:
            print(f"❌ 刷新失败: {e}", file=sys.stderr)
            print("请重新登录获取 token", file=sys.stderr)
            sys.exit(1)
    
    resp.raise_for_status()
    return resp.json() if resp.content else {}


# ── API 函数 ─────────────────────────────────────────

def get_episodes(config: dict, limit: int = 20) -> dict:
    """获取单集列表（含播放数据）"""
    return call_api("POST", PODCASTER_API, "/v1/episode/list", config, 
                    json={"pid": config["podcastId"], "limit": limit})


def get_subscribers(config: dict, skip: int = 0, limit: int = 100) -> dict:
    """获取订阅者列表"""
    return call_api("POST", PODCASTER_API, "/v1/subscriber/list", config,
                    json={"pid": config["podcastId"], "skip": skip, "limit": limit})


def get_podcast_info(config: dict) -> dict:
    """获取播客基本信息"""
    return call_api("GET", PUBLIC_API, f"/v1/podcast/{config['podcastId']}", config)


def get_comments(config: dict, episode_id: str, limit: int = 20) -> dict:
    """获取单集评论"""
    return call_api("POST", PUBLIC_API, "/v1/comment/listPrimary", config,
                    json={"eid": episode_id, "order": "HOT", "limit": limit})


# ── CLI ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="小宇宙数据客户端")
    sub = parser.add_subparsers(dest="cmd", required=True)
    
    # episodes
    ep = sub.add_parser("episodes", help="获取单集列表")
    ep.add_argument("--limit", type=int, default=20)
    
    # subscribers
    sb = sub.add_parser("subscribers", help="获取订阅者列表")
    sb.add_argument("--skip", type=int, default=0)
    sb.add_argument("--limit", type=int, default=100)
    
    # info
    sub.add_parser("info", help="获取播客基本信息")
    
    # comments
    cm = sub.add_parser("comments", help="获取单集评论")
    cm.add_argument("--episode-id", required=True)
    cm.add_argument("--limit", type=int, default=20)
    
    # refresh (手动刷新 token)
    sub.add_parser("refresh", help="手动刷新 token")
    
    args = parser.parse_args()
    config = load_config()
    
    try:
        if args.cmd == "episodes":
            result = get_episodes(config, args.limit)
        elif args.cmd == "subscribers":
            result = get_subscribers(config, args.skip, args.limit)
        elif args.cmd == "info":
            result = get_podcast_info(config)
        elif args.cmd == "comments":
            result = get_comments(config, args.episode_id, args.limit)
        elif args.cmd == "refresh":
            new_access, new_refresh = refresh_tokens(config["refreshToken"], config["accessToken"])
            config["accessToken"] = new_access
            config["refreshToken"] = new_refresh
            save_config(config)
            result = {"success": True, "message": "Token 刷新成功"}
        else:
            result = {"error": "Unknown command"}
        
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
    except requests.RequestException as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
