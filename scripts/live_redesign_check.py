"""Read-only verification of the released Community Cloud UI; saves no health records."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
HEADINGS = {
    "Today": "You've got this, Friend.", "Food": "Food, without the fuss.",
    "Move": "Start small. Keep showing up.", "Buddy": "I'm in your corner.",
    "Progress": "Progress has more than one shape.", "Settings": "Make this feel like yours.",
}


def check(url):
    OUT.mkdir(exist_ok=True)
    report = {"url":url, "screens":[], "assets":[], "page_errors":[]}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width":1440,"height":1050})
        page = context.new_page()
        page.on("pageerror",lambda error: report["page_errors"].append(str(error)))
        page.goto(url,wait_until="domcontentloaded",timeout=60000)
        deadline = time.monotonic() + 180
        frame = None
        while time.monotonic() < deadline:
            wake = page.get_by_role("button",name="Yes, get this app back up!")
            if wake.count() and wake.is_visible():
                wake.click()
                print("Requested Community Cloud wake-up",flush=True)
            frame = next((f for f in page.frames if "/~/+/" in f.url), None)
            if frame:
                break
            page.wait_for_timeout(1000)
        if not frame:
            page.screenshot(path=OUT / "live-startup-failure.png")
            raise AssertionError(f"No app iframe: {page.locator('body').inner_text()[:500]}")
        expect(frame.locator(".buddy-brand")).to_be_visible(timeout=90000)
        expect(frame.get_by_role("heading",name=HEADINGS["Today"],exact=True)).to_be_visible()
        expect(frame.locator('.garden[data-garden="webgl"]')).to_be_visible(timeout=30000)
        expect(frame.locator('.garden')).to_have_attribute('data-ready','true',timeout=15000)
        report["scene"] = {"state":frame.locator('.garden').get_attribute('data-garden'),
                           "canvases":frame.locator('canvas').count(),
                           "gsap_version":frame.evaluate("gsap.version")}
        assert report["scene"] == {"state":"webgl","canvases":1,"gsap_version":"3.15.0"}
        frame.evaluate("document.fonts.ready")
        assert frame.evaluate("document.fonts.check('500 48px Fraunces') && document.fonts.check('400 16px \"DM Sans\"')")
        base = frame.evaluate("new URL('app/static/',location.href).href")
        for asset in ("vendor/three.module.js","vendor/three.core.js","vendor/gsap.min.js",
                      "fonts/dm-sans.woff2","fonts/fraunces.woff2","icons/buddy-mark.svg"):
            response = context.request.get(urljoin(base,asset))
            assert response.ok, (asset,response.status)
            actual, expected = response.body(), (ROOT / "static" / asset).read_bytes()
            # Git normalizes text on checkout; Windows SVG files can use CRLF.
            if asset.endswith((".js", ".svg")):
                actual, expected = actual.replace(b"\r\n",b"\n"), expected.replace(b"\r\n",b"\n")
            assert hashlib.sha256(actual).digest() == hashlib.sha256(expected).digest(), asset
            report["assets"].append({"asset":asset,"status":response.status,"matches_release":True})
        print("Live Three.js, GSAP, fonts and asset fingerprints verified",flush=True)
        for width in (1440,390):
            page.set_viewport_size({"width":width,"height":1050})
            for label,heading in HEADINGS.items():
                frame.get_by_role("link",name=re.compile(rf" {label}$")).click()
                expect(frame.get_by_role("heading",name=heading,exact=True)).to_be_visible()
                expect(frame.locator('[data-testid="stException"]')).to_have_count(0)
                expect(frame.get_by_role("button",name="Install app",exact=True)).to_be_visible()
                assert not frame.evaluate("document.documentElement.scrollWidth > innerWidth + 1"), (width,label)
                report["screens"].append({"width":width,"screen":label,"passed":True})
                if label == "Today":
                    expect(frame.locator('.garden[data-garden="webgl"]')).to_be_visible(timeout=30000)
                    page.screenshot(path=OUT / f"live-redesign-{width}.png",full_page=True)
        page.evaluate("if (window.__steadyInstall) window.__steadyInstall.prompt=null")
        frame.get_by_role('button',name='Install app',exact=True).click()
        expect(frame.get_by_role('region',name='Installation instructions')).to_be_visible()
        frame.get_by_role('button',name='Got it',exact=True).click()
        manifest_url = page.locator('link[rel="manifest"]').get_attribute('href')
        response = context.request.get(manifest_url)
        assert response.ok and response.json()['theme_color'] == '#284C38'
        for icon in response.json()['icons']:
            image = context.request.get(urljoin(manifest_url,icon['src']))
            assert image.ok and image.headers['content-type'].startswith('image/png')
        report['installability_errors'] = context.new_cdp_session(page).send('Page.getInstallabilityErrors')['installabilityErrors']
        assert not report['installability_errors'], report['installability_errors']
        assert not report['page_errors'], report['page_errors']
        report['passed'] = True
        (OUT / 'live-redesign-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        context.close()
        browser.close()
    print(json.dumps({"passed":True,"screens":len(report['screens']),"assets":len(report['assets']),
                      "scene":report['scene'],"installability_errors":[],"page_errors":[]}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url',default='https://steady-buddy.streamlit.app/')
    check(parser.parse_args().url)
