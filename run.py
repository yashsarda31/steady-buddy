"""Local-first launcher. A single process owns the PWA and Streamlit runtime."""
import argparse
import os
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parent


def check_binding(host, password):
    if host not in ("127.0.0.1", "localhost", "::1") and len(password) < 12:
        raise ValueError("Remote access needs BUDDY_ACCESS_PASSWORD (at least 12 characters). Use HTTPS on your hosting proxy.")


def main():
    parser = argparse.ArgumentParser(description="Start your private Steady Buddy app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    args = parser.parse_args()
    try:
        check_binding(args.host, os.environ.get("BUDDY_ACCESS_PASSWORD", ""))
    except ValueError as exc:
        parser.error(str(exc))
    os.chdir(ROOT)
    print(f"Steady Buddy: http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}")
    print("Keep this app running while you use it. Press Ctrl+C to stop.")
    uvicorn.run("gateway:create_app", factory=True, host=args.host, port=args.port, workers=1,
                access_log=False, proxy_headers=True,
                forwarded_allow_ips=os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1"))


if __name__ == "__main__":
    main()
