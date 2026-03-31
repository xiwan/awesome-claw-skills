#!/usr/bin/env python3
"""
Jike QR Authentication (standalone)
Run directly: python3 scripts/auth.py
No pip install required — only needs `requests`.

Outputs JSON with access_token and refresh_token to stdout.
"""

import json
import sys
import time
import uuid

import requests

API_BASE = "https://api.ruguoapp.com"
REQUEST_TIMEOUT = 10
POLL_INTERVAL = 2
POLL_TIMEOUT = 120

HEADERS = {
    "Origin": "https://web.okjike.com",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) "
        "Gecko/20100101 Firefox/148.0"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def create_session() -> str:
    """Create a new login session, return uuid."""
    session_uuid = str(uuid.uuid4())
    resp = requests.post(
        f"{API_BASE}/1.0/readability/createLoginLinkSession",
        headers=HEADERS,
        json={"uuid": session_uuid},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return session_uuid


def poll_session(session_uuid: str) -> dict | None:
    """Poll session status, return tokens if confirmed."""
    resp = requests.post(
        f"{API_BASE}/1.0/readability/loginWithLinkSession",
        headers=HEADERS,
        json={"uuid": session_uuid},
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code == 200:
        data = resp.json()
        if data.get("success"):
            return {
                "access_token": resp.headers.get("x-jike-access-token"),
                "refresh_token": resp.headers.get("x-jike-refresh-token"),
            }
    return None


def main():
    try:
        session_uuid = create_session()
    except requests.RequestException as e:
        print(json.dumps({"error": f"Failed to create session: {e}"}), file=sys.stderr)
        sys.exit(1)

    # Generate QR code URL
    qr_url = f"jike://page.jk/web?url=https%3A%2F%2Fwww.okjike.com%2Faccount%2Fscan%3Fuuid%3D{session_uuid}&displayHeader=false&displayFooter=false"
    
    print(f"[+] Session: {session_uuid}", file=sys.stderr)
    
    # Try to render QR in terminal
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(qr_url)
        qr.print_ascii(out=sys.stderr, invert=True)
    except ImportError:
        print(f"[*] Install 'qrcode' for terminal QR, or scan:", file=sys.stderr)
        print(f"    {qr_url}", file=sys.stderr)
    
    print(f"[*] Waiting for scan...", file=sys.stderr)

    # Poll for confirmation
    start = time.time()
    while time.time() - start < POLL_TIMEOUT:
        tokens = poll_session(session_uuid)
        if tokens and tokens.get("access_token"):
            print(json.dumps(tokens, indent=2))
            print(f"[+] Login successful!", file=sys.stderr)
            return
        time.sleep(POLL_INTERVAL)

    print(json.dumps({"error": "Login timeout"}), file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
