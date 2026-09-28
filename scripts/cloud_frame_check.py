"""Verify installation in a local same-origin iframe matching Community Cloud."""
import json
import os
from pathlib import Path
import threading
import time
from urllib.parse import urljoin

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from playwright.sync_api import expect, sync_playwright
import streamlit as st
import uvicorn

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"


def main():
    OUT.mkdir(exist_ok=True)
    os.environ["BUDDY_HOSTING"] = "cloud"
    os.environ["BUDDY_DB_PATH"] = str(OUT / "cloud-frame-test" / "buddy.db")
    diary = st.App(ROOT / "app.py")
    app = FastAPI(lifespan=diary.lifespan())

    @app.get("/")
    async def index():
        return HTMLResponse('''<!doctype html><html><head><title>Cloud preview</title>
          <link rel="manifest" href="/platform-manifest.json"></head><body>
          <iframe id="cloud" src="/~/+/" title="Steady Buddy"
          sandbox="allow-forms allow-modals allow-popups allow-same-origin allow-scripts allow-downloads"
          style="width:100%;height:95vh;border:0"></iframe></body></html>''')

    app.mount("/~/+", diary)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8773, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 20
    while not server.started:
        if not thread.is_alive() or time.monotonic() > deadline:
            raise RuntimeError("Cloud preview could not start")
        time.sleep(0.05)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto("http://localhost:8773/")
            frame = page.frame_locator("#cloud")
            expect(frame.get_by_role("heading", name="You've got this, Friend.")).to_be_visible(timeout=30000)
            expect(frame.get_by_role("button", name="Install app", exact=True)).to_be_visible()
            page.wait_for_function("document.querySelector('link[rel=manifest]').href.includes('/~/+/app/static/manifest.json')")
            manifest_url = page.locator('link[rel="manifest"]').get_attribute("href")
            response = page.request.get(manifest_url)
            assert response.ok and response.json()["name"] == "Steady Buddy"
            for icon in response.json()["icons"]:
                image = page.request.get(urljoin(manifest_url, icon["src"]))
                assert image.ok and image.headers["content-type"].startswith("image/png")
            cdp = page.context.new_cdp_session(page)
            result = cdp.send("Page.getInstallabilityErrors")
            assert not result["installabilityErrors"], result
            frame.get_by_role("button", name="Install app", exact=True).click()
            # A native prompt may be available; fallback help is covered by browser_check.py.
            page.screenshot(path=OUT / "cloud-frame.png")
            fresh = browser.new_page()
            fresh.goto("http://localhost:8773/~/+/buddy")
            expect(fresh.get_by_role("heading", name="I'm in your corner.")).to_be_visible(timeout=30000)
            (OUT / "cloud-frame-verification.json").write_text(json.dumps({
                "passed": True, "manifest": manifest_url, "installability_errors": [],
                "checks": ["Same-origin Cloud iframe", "Outer page manifest and icons", "Direct page startup"]
            }, indent=2), encoding="utf-8")
            browser.close()
            print("Cloud iframe, installation metadata and fresh direct page startup passed")
    finally:
        server.should_exit = True
        thread.join(timeout=10)


if __name__ == "__main__":
    main()
