"""Real rendering/PWA verification. Run only against an isolated test diary."""
import argparse
import json
from pathlib import Path
import re
import time

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"


def check(base, direct=False):
    OUT.mkdir(exist_ok=True)
    report = {"url": base, "checks": [], "layout": []}
    meal_name = f"Browser test dal {time.time_ns()}"
    walk_name = f"Browser test walk {time.time_ns()}"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base)
        frame = page if direct else page.frame_locator("#buddy-frame")
        expect(frame.get_by_role("heading", name="Steady Buddy", exact=True)).to_be_visible(timeout=30000)
        expect(frame.get_by_role("heading", name="You've got this, Friend.")).to_be_visible()
        report["checks"].append("Native Streamlit session rendered")

        frame.get_by_role("link", name=re.compile(r" Food$")).click()
        expect(frame.get_by_role("heading", name="Food, without the fuss.")).to_be_visible()
        intake = frame.get_by_test_id("stMetricValue").first
        expect(intake).to_be_visible()
        before = float(intake.inner_text().replace("kcal", "").replace(",", "").strip())
        frame.get_by_role("textbox", name="Food or drink", exact=True).first.fill(meal_name)
        frame.get_by_role("spinbutton", name="Calories per serving (kcal)", exact=True).first.fill("180")
        frame.get_by_role("spinbutton", name="Servings", exact=True).first.fill("1.5")
        frame.get_by_role("button", name="Add to diary", exact=True).click()
        expect(frame.get_by_text(meal_name, exact=True)).to_be_visible()
        expect(intake).to_have_text(f"{before + 270:,.0f} kcal")
        page.reload()
        expect(frame.get_by_role("heading", name="Steady Buddy", exact=True)).to_be_visible(timeout=30000)
        frame.get_by_role("link", name=re.compile(r" Food$")).click()
        expect(frame.get_by_text(meal_name, exact=True)).to_be_visible()
        report["checks"].append("Meal, serving multiplier and refresh persistence")

        frame.get_by_role("link", name=re.compile(r" Move$")).click()
        frame.get_by_role("textbox", name="Movement", exact=True).fill(walk_name)
        frame.get_by_role("button", name="Save movement", exact=True).click()
        expect(frame.get_by_text(walk_name, exact=False)).to_be_visible()
        report["checks"].append("Movement log")

        frame.get_by_role("link", name=re.compile(r" Buddy$")).click()
        frame.get_by_role("combobox", name="What would help right now?").click()
        frame.get_by_role("option", name="Want a drink", exact=True).click()
        expect(frame.get_by_role("button", name="Start a two-minute pause")).to_be_visible()
        frame.get_by_role("button", name="Start a two-minute pause").click()
        expect(frame.get_by_role("timer")).not_to_have_text("2:00", timeout=5000)
        frame.get_by_role("button", name="Reset", exact=True).click()
        expect(frame.get_by_role("timer")).to_have_text("2:00")
        alcohol_select = frame.get_by_role("combobox", name="Alcohol check-in", exact=True)
        alcohol_select.scroll_into_view_if_needed()
        # React Aria dismisses popovers on scroll; settle the automatic scroll before opening it.
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        alcohol_select.click()
        try:
            frame.get_by_role("option", name="Alcohol-free", exact=True).click(timeout=5000)
        except Exception:
            page.screenshot(path=OUT / "checkin-failure.png", full_page=True)
            print({"expanded": frame.get_by_role("combobox", name="Alcohol check-in", exact=True).get_attribute("aria-expanded"),
                   "options": frame.get_by_role("option").all_text_contents(), "page_errors": errors})
            raise
        frame.get_by_role("textbox", name="One small win", exact=True).fill("I chose a short walk")
        frame.get_by_role("button", name="Save check-in", exact=True).click()
        report["checks"].append("Craving support, live timer and alcohol-free check-in")

        frame.get_by_role("link", name=re.compile(r" Progress$")).click()
        frame.get_by_role("spinbutton", name="Weight (kg)", exact=True).fill("78.2")
        frame.get_by_role("button", name="Save weigh-in", exact=True).click()
        expect(frame.get_by_text("Weigh-in saved. One number is only one moment.", exact=True)).to_be_visible()
        report["checks"].append("Weigh-in and weight trend")

        frame.get_by_role("link", name=re.compile(r" Settings$")).click()
        with page.expect_download() as download_event:
            frame.get_by_role("button", name=re.compile(r"Download full backup$")).click()
        download = download_event.value
        download.save_as(OUT / "browser-backup.json")
        payload = json.loads((OUT / "browser-backup.json").read_text(encoding="utf-8"))
        assert payload["version"] == 1 and payload["tables"]["foods"]
        frame.get_by_text("Restore a backup", exact=True).click()
        frame.locator('input[type="file"]').set_input_files(OUT / "browser-backup.json")
        frame.get_by_text("Replace my current diary with this backup", exact=True).click()
        expect(frame.get_by_role("checkbox", name="Replace my current diary with this backup", exact=True)).to_be_checked()
        frame.get_by_role("button", name="Restore backup", exact=True).click()
        expect(frame.get_by_text("Backup restored. Your previous diary has a safety copy on this server.", exact=True)).to_be_visible()
        report["checks"].append("Private backup download and atomic restore through actual file upload")

        # Check rendering at each narrow width, including every screen. Real navigation
        # is tested above; fresh iframe loads below also verify durable multi-session data.
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({"width": width, "height": 1000})
            for route, heading in [("", "You've got this, Friend."), ("food", "Food, without the fuss."),
                                   ("move", "Start small. Keep showing up."), ("buddy", "I'm in your corner."),
                                   ("progress", "Progress has more than one shape."), ("settings", "Make this feel like yours.")]:
                if direct:
                    page.goto(f"{base}/{route}")
                else:
                    page.locator("#buddy-frame").evaluate("(el, url) => el.src = url", f"/streamlit/{route}?embed=true")
                expect(frame.get_by_role("heading", name=heading, exact=True)).to_be_visible(timeout=30000)
                ready_button = {"": "Save check-in", "food": "Add to diary", "move": "Save movement",
                                "buddy": "Save check-in", "progress": "Save weigh-in", "settings": "Save my preferences"}[route]
                expect(frame.get_by_role("button", name=ready_button, exact=True)).to_be_visible()
                if route == "":
                    expect(frame.get_by_test_id("stMetricValue")).to_have_count(3)
                expect(frame.locator('[data-testid="stException"]')).to_have_count(0)
                shell_overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
                app_frame = page if direct else next(item for item in page.frames if "/streamlit/" in item.url)
                content_overflow = app_frame.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
                assert not shell_overflow and not content_overflow, f"Overflow: {width}px {route}"
                report["layout"].append({"width": width, "screen": route or "today", "overflow": False})
                if (width, route) in [(390, ""), (1440, ""), (390, "food"), (390, "buddy")]:
                    page.screenshot(path=OUT / f"{route or 'today'}-{width}.png", full_page=True)

        if direct:
            # Exercise the fallback help even if Chromium already offered a prompt.
            page.evaluate("window.__steadyInstall.prompt = null")
            page.get_by_role("button", name="Install app", exact=True).click()
            expect(page.get_by_text("Keep your buddy close.", exact=True)).to_be_visible()
            page.get_by_role("button", name="Got it", exact=True).click()
            manifest_url = page.locator('link[rel="manifest"]').get_attribute("href")
            manifest_response = context.request.get(manifest_url)
            assert manifest_response.ok
            manifest = manifest_response.json()
            assert manifest["name"] == "Steady Buddy" and manifest["display"] == "standalone"
            from urllib.parse import urljoin
            for icon in manifest["icons"]:
                response = context.request.get(urljoin(manifest_url, icon["src"]))
                assert response.ok and response.headers["content-type"].startswith("image/png")
            cdp = context.new_cdp_session(page)
            report["installability_errors"] = cdp.send("Page.getInstallabilityErrors")["installabilityErrors"]
            assert not report["installability_errors"], report["installability_errors"]
            report["checks"].append("Native installation button, help, manifest, icons and Chromium installability")
            page.evaluate("""() => {
              window.testPrompted = false;
              const event = new Event('beforeinstallprompt', {cancelable: true});
              event.prompt = async () => { window.testPrompted = true; };
              event.userChoice = Promise.resolve({outcome: 'dismissed'});
              window.dispatchEvent(event);
            }""")
            page.get_by_role("button", name="Install app", exact=True).click()
            assert page.evaluate("window.testPrompted")
            report["checks"].append("Deferred install prompt triggered by actual button click")
            record = page.evaluate("JSON.parse(localStorage.getItem('steady-buddy-diary-v1'))")
            assert json.loads(record["backup"])["tables"]["foods"]
            other = browser.new_context()
            other_page = other.new_page()
            other_page.goto(base)
            expect(other_page.get_by_role("heading", name="You've got this, Friend.")).to_be_visible(timeout=30000)
            expect(other_page.get_by_test_id("stMetricValue").first).to_have_text("0 kcal")
            assert other_page.evaluate("JSON.parse(localStorage.getItem('steady-buddy-diary-v1')).token") != record["token"]
            other.close()
            report["checks"].append("Separate browser cannot see the first browser's diary")
            # Preserve the disposable test files while simulating Cloud losing its disk.
            devices = (OUT / "cloud-test" / "devices").resolve()
            assert devices.is_relative_to(OUT.resolve()) and devices.is_dir()
            devices.rename(devices.with_name(f"devices-before-reset-{time.time_ns()}"))
            page.reload()
            expect(frame.get_by_role("heading", name="Steady Buddy", exact=True)).to_be_visible(timeout=30000)
            frame.get_by_role("link", name=re.compile(r" Food$")).click()
            expect(frame.get_by_text(meal_name, exact=True)).to_be_visible()
            report["checks"].append("Diary recovered from browser copy after simulated server file reset")
            page.evaluate("window.dispatchEvent(new Event('appinstalled'))")
            expect(page.get_by_role("button", name="Install app", exact=True)).to_be_hidden()
            report["checks"].append("Install control hides after installation")
            report["page_errors"] = errors
            assert not errors, errors
            report["passed"] = True
            (OUT / "cloud-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            browser.close()
            print(json.dumps({"passed": True, "checks": len(report["checks"]), "screen_sizes": len(report["layout"])}))
            return
        page.get_by_role("button", name="Install", exact=True).click()
        if page.get_by_role("dialog").is_visible():
            page.get_by_role("button", name="Got it", exact=True).click()
        page.evaluate("navigator.serviceWorker.ready")
        page.wait_for_function("navigator.serviceWorker.controller !== null", timeout=15000)
        manifest_response = context.request.get(f"{base}/manifest.webmanifest")
        assert manifest_response.ok
        manifest = manifest_response.json()
        assert manifest["display"] == "standalone"
        cdp = context.new_cdp_session(page)
        report["installability_errors"] = cdp.send("Page.getInstallabilityErrors")["installabilityErrors"]
        assert not report["installability_errors"], report["installability_errors"]
        report["checks"].append("Installation help, manifest and active root-scope service worker")
        cached = page.evaluate("async () => { const c = await caches.open('steady-public-v1'); return (await c.keys()).map(r => new URL(r.url).pathname); }")
        assert all(not path.startswith('/streamlit') for path in cached)
        context.set_offline(True)
        page.goto(base, wait_until="domcontentloaded")
        expect(page.get_by_role("heading", name="Take a little pause.")).to_be_visible()
        report["checks"].append("Offline fallback without private diary caching")
        context.set_offline(False)
        page.goto(base)
        expect(frame.get_by_role("heading", name="Steady Buddy", exact=True)).to_be_visible(timeout=30000)
        report["checks"].append("Reconnect after offline")
        report["page_errors"] = errors
        assert not errors, errors
        report["passed"] = True
        (OUT / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        browser.close()
    print(json.dumps({"passed": True, "checks": len(report["checks"]), "screen_sizes": len(report["layout"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8766")
    parser.add_argument("--direct", action="store_true", help="Test streamlit run with BUDDY_HOSTING=cloud and output/cloud-test/buddy.db")
    args = parser.parse_args()
    check(args.url.rstrip("/"), direct=args.direct)
