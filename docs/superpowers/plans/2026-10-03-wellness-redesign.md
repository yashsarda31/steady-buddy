# Wellness Redesign Implementation Plan

**Goal:** Redesign all six Steady Buddy screens with a calm wellness aesthetic, Three.js and GSAP, then test and redeploy the existing app.

**Architecture:** Retain Streamlit routing, native accessible widgets, and the existing diary/recovery logic. Share layout helpers and a consistent theme; mount an inline v2 component that imports pinned, locally served Three.js and GSAP assets.

**Tech stack:** Streamlit 1.64, Python, Three.js 0.186.1, GSAP 3.15.0, pytest, Ruff, Playwright.

## Constraints

- User approved `docs/redesign-plan.md` and authorised implementation and deployment without additional approval requests.
- Work inline in the existing checkout on `codex/wellness-redesign`; preserve real diaries.
- Keep all six routes, installation, browser isolation/recovery, backups, and health semantics.
- Essential controls work without WebGL or motion. Respect reduced motion, background visibility and resource cleanup.
- Test before pushing the release to the existing Cloud deployment branch.

## Task 1: Shared shell and visual component

Files: `.streamlit/config.toml`, `app.py`, `buddy/design.py`, `buddy/scene.py`, `web/garden.js`, `web/garden.css`, `web/design.css`, `static/vendor/`.

- [ ] Add pinned local browser distributions of Three.js and GSAP, with licenses.
- [ ] Build the ivory/forest/sage/apricot design system, branded header, and responsive native navigation.
- [ ] Build a Three.js pebble garden with gentle GSAP motion, static fallback, visibility controls, and full cleanup.
- [ ] Render with the real Streamlit server; verify assets load under both direct and Cloud iframe paths.

## Task 2: Six-screen redesign

Files: `app_pages/today.py`, `buddy/food_view.py`, `app_pages/move.py`, `app_pages/buddy.py`, `app_pages/progress.py`, `app_pages/settings.py`, `buddy/ui.py`, `buddy/timer.py`, `buddy/browser.py`, `web/web.css`.

- [ ] Build Today hero, recorded daily stats, quick actions, check-in and habit summary.
- [ ] Group Food logging/diary and Move plan/log into clear responsive cards.
- [ ] Build a quiet Buddy reset space; retain the working timer and alcohol support guidance.
- [ ] Separate Progress habits, optional weight, and recorded food history; group Settings preferences and data tools.
- [ ] Keep all form identifiers and data operations stable; escape user text in decorative markup.
- [ ] Run `rtk proxy .venv/Scripts/python.exe -m pytest -q` and `rtk proxy .venv/Scripts/python.exe -m ruff check .`; repair failures before browser checks.

## Task 3: Functional and visual verification

Files: `scripts/redesign_check.py`, existing `scripts/browser_check.py`, `scripts/cloud_frame_check.py`, `tests/test_app.py`, `output/`.

- [ ] Run existing browser flows against disposable Cloud and gateway diaries.
- [ ] Check all six screens at 320, 390, 768, and 1440 pixels; capture and inspect desktop/mobile screenshots.
- [ ] Exercise reduced motion, disabled WebGL, keyboard focus, library-load fallback and animation cleanup on repeated page changes.
- [ ] Validate installation metadata and browser recovery using the existing Cloud iframe check.

## Task 4: Publish and verify

Files: `README.md`, `docs/screenshots/`, deployment report in `output/`.

- [ ] Record current verification evidence and replace the old screenshot.
- [ ] Review `rtk git diff --check` and `rtk git diff --stat`; ensure no private data or generated diary is included.
- [ ] Commit the tested redesign, integrate it into `main`, and push to the existing public repository.
- [ ] Wait for the Cloud update; verify the actual live iframe, new scene, all routes, install button, static assets, and absence of exceptions without saving health records.
- [ ] Report the live URL and relevant limitations, supported by current checks.
