"""Visual/motion/accessibility checks. Use only an isolated local test diary.

Run after npm pack axe-core@4.13.0 --pack-destination output --silent.
The existing browser_check.py covers saving records, backups and recovery.
"""
import argparse
import json
from pathlib import Path
import tarfile

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
PAGES = {
    "": "You've got this, Friend.",
    "food": "Food, without the fuss.",
    "move": "Start small. Keep showing up.",
    "buddy": "I'm in your corner.",
    "progress": "Progress has more than one shape.",
    "settings": "Make this feel like yours.",
}


def ready(page, base, route=""):
    page.goto(f"{base}/{route}")
    expect(page.get_by_role("heading", name=PAGES[route], exact=True)).to_be_visible(timeout=30000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
    expect(page.locator(".st-key-navigation a")).to_have_count(6)
    expect(page.locator('.st-key-navigation a[aria-current="page"]')).to_have_count(1)


def check(base):
    assert base.startswith(("http://localhost:", "http://127.0.0.1:")), "Use an isolated local test diary"
    OUT.mkdir(exist_ok=True)
    with tarfile.open(OUT / "axe-core-4.13.0.tgz") as package:
        (OUT / "axe.min.js").write_bytes(package.extractfile("package/axe.min.js").read())
    report = {"checks": [], "layouts": [], "accessibility": [], "errors": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width":1440, "height":1050})
        page = context.new_page()
        page.on("pageerror", lambda error: report["errors"].append(str(error)))
        ready(page, base)
        expect(page.locator('.garden[data-garden="webgl"]')).to_be_visible(timeout=15000)
        expect(page.locator('.garden')).to_have_attribute("data-playing", "true")
        assert page.locator("canvas").count() == 1
        report["checks"].append("Actual Three.js canvas and GSAP motion loaded from local assets")
        page.get_by_role("button", name="Save check-in", exact=True).scroll_into_view_if_needed()
        expect(page.locator(".garden")).to_have_attribute("data-playing", "false")
        page.locator(".garden").scroll_into_view_if_needed()
        expect(page.locator(".garden")).to_have_attribute("data-playing", "true")
        report["checks"].append("Decorative animation pauses outside the viewport and resumes on return")

        food_link = page.locator('.st-key-navigation a[href="food"]')
        food_link.focus()
        assert food_link.evaluate("el => getComputedStyle(el).outlineStyle") != "none"
        page.keyboard.press("Enter")
        expect(page.get_by_role("heading", name=PAGES["food"], exact=True)).to_be_visible()
        report["checks"].append("Visible keyboard focus and Enter navigation")
        page.get_by_role("spinbutton", name="day, Diary date", exact=True).focus()
        page.keyboard.press("Alt+ArrowDown")
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.get_by_role("combobox", name="Diary date", exact=True)).to_have_attribute("aria-expanded", "true")
        page.keyboard.press("Escape")
        expect(page.get_by_role("dialog")).to_have_count(0)
        report["checks"].append("Date editor and calendar remain operable with keyboard shortcuts")
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({"width":width, "height":1050})
            for route in PAGES:
                ready(page, base, route)
                page.wait_for_timeout(700)
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1"), (width,route)
                clipped = page.locator(".st-key-navigation a p, .st-key-next-steps a p").evaluate_all(
                    "els => els.filter(el => el.scrollWidth > el.clientWidth + 1).map(el => el.textContent)")
                assert not clipped, (width,route,clipped)
                report["layouts"].append({"width":width,"route":route or "today","clipped_navigation":False})
                if width in (390,1440):
                    page.add_script_tag(path=str(OUT / "axe.min.js"))
                    violations = page.evaluate("""async () => (await axe.run(document, {
                      runOnly: ['wcag2a','wcag2aa','wcag21a','wcag21aa']
                    })).violations.map(v => ({id:v.id,impact:v.impact,description:v.description,
                      nodes:v.nodes.map(n => ({target:n.target,summary:n.failureSummary}))}))""")
                    report["accessibility"].append({"width":width,"route":route or "today","violations":violations})
                    page.screenshot(path=OUT / f"redesign-{route or 'today'}-{width}.png", full_page=True)
        report["checks"].append("All six routes: layouts at four widths, automated accessibility at two widths")
        for label, options, init_script in [
            ("Reduced motion", {"reduced_motion":"reduce"}, None),
            ("WebGL unavailable", {}, """const original = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type,...args) {
                  return /^webgl/.test(type) ? null : original.call(this,type,...args);
                };"""),
            ("Visual libraries unavailable", {}, None),
        ]:
            alternate = browser.new_context(viewport={"width":390,"height":1000}, **options)
            if init_script:
                alternate.add_init_script(init_script)
            if label == "Visual libraries unavailable":
                alternate.route("**/app/static/vendor/**", lambda route: route.abort())
            fallback = alternate.new_page()
            fallback.on("pageerror", lambda error: report["errors"].append(str(error)))
            ready(fallback, base)
            expect(fallback.locator('.garden')).to_have_attribute('data-ready', 'true', timeout=15000)
            if label == "Reduced motion":
                expect(fallback.locator('.garden[data-garden="webgl"]')).to_be_visible(timeout=15000)
                expect(fallback.locator(".garden")).to_have_attribute("data-playing", "false")
                fallback.emulate_media(reduced_motion="no-preference")
                expect(fallback.locator(".garden")).to_have_attribute("data-playing", "true")
                fallback.emulate_media(reduced_motion="reduce")
                expect(fallback.locator(".garden")).to_have_attribute("data-playing", "false")
            else:
                expect(fallback.locator('.garden[data-garden="fallback"]')).to_be_visible()
                expect(fallback.locator(".garden-fallback")).to_be_visible()
            expect(fallback.get_by_role("button", name="Save check-in", exact=True)).to_be_visible()
            fallback.screenshot(path=OUT / f"redesign-{label.lower().replace(' ','-')}.png", full_page=True)
            report["checks"].append(f"{label}: content and forms remain available")
            alternate.close()

        # Instrument browser resource creation rather than assuming DOM removal frees WebGL.
        cleanup = browser.new_context()
        cleanup.add_init_script("""window.__gardenResources = {created:0,lost:0};
          const seen = new WeakSet(), original = HTMLCanvasElement.prototype.getContext;
          HTMLCanvasElement.prototype.getContext = function(type,...args) {
            const context = original.call(this,type,...args);
            if (context && /^webgl/.test(type) && !seen.has(this)) {
              seen.add(this); window.__gardenResources.created++;
              this.addEventListener('webglcontextlost', () => window.__gardenResources.lost++);
            }
            return context;
          };""")
        clean_page = cleanup.new_page()
        clean_page.on("pageerror", lambda error: report["errors"].append(str(error)))
        ready(clean_page, base)
        for _ in range(4):
            expect(clean_page.locator('.garden[data-garden="webgl"]')).to_be_visible(timeout=15000)
            clean_page.locator('.st-key-navigation a[href="food"]').click()
            expect(clean_page.get_by_role("heading", name=PAGES["food"], exact=True)).to_be_visible()
            expect(clean_page.locator("canvas")).to_have_count(0)
            clean_page.wait_for_function("__gardenResources.created === __gardenResources.lost")
            clean_page.wait_for_function("!gsap.globalTimeline.getChildren().some(tween => tween.repeat() === -1)")
            clean_page.locator('.st-key-navigation a[href=""]').click()
            expect(clean_page.get_by_role("heading", name=PAGES[""], exact=True)).to_be_visible()
        report["resources"] = clean_page.evaluate("__gardenResources")
        report["checks"].append("WebGL contexts released on four consecutive page departures")
        cleanup.close()
        context.close()
        browser.close()
    report["passed"] = not report["errors"] and all(not entry["violations"] for entry in report["accessibility"])
    (OUT / "redesign-verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    violations = [entry for entry in report["accessibility"] if entry["violations"]]
    print(json.dumps({"passed":report["passed"],"checks":len(report["checks"]),"layouts":len(report["layouts"]),
                      "accessibility_scans":len(report["accessibility"]),
                      "violations":[{"route":v['route'],"width":v['width'],"rules":[item['id'] for item in v['violations']]} for v in violations],
                      "errors":report["errors"]},indent=2))
    assert report["passed"], "See output/redesign-verification.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8501")
    check(parser.parse_args().url.rstrip("/"))
