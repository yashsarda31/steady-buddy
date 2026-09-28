"""Verify the actual password-gated Streamlit session, not just a test endpoint."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

OUT = Path(__file__).resolve().parents[1] / "output"


def check(url, password):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)
        expect(page.get_by_role("heading", name="Welcome back.")).to_be_visible()
        page.get_by_label("Your access password").fill(password)
        page.get_by_role("button", name="Unlock my buddy").click()
        frame = page.frame_locator("#buddy-frame")
        expect(frame.get_by_role("heading", name="Steady Buddy", exact=True)).to_be_visible(timeout=30000)
        expect(frame.get_by_role("button", name="Save check-in", exact=True)).to_be_visible()
        page.get_by_role("button", name="Lock", exact=True).click()
        expect(page.get_by_role("heading", name="Welcome back.")).to_be_visible()
        assert context.request.get(url + "/streamlit/", max_redirects=0).status == 303
        context.close()
        browser.close()
    OUT.mkdir(exist_ok=True)
    result = {"passed": True, "checks": ["Real private login", "Native authenticated WebSocket/diary render", "Lock and protected reconnect"]}
    (OUT / "auth-verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8767")
    args = parser.parse_args()
    check(args.url.rstrip("/"), os.environ["BUDDY_TEST_PASSWORD"])
