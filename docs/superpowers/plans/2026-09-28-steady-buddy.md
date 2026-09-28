# Steady Buddy Implementation Plan

> **For agentic workers:** Execute this plan inline using executing-plans. The user has authorized completion without further questions.

**Goal:** Deliver a tested personal Streamlit habit companion and installable PWA package in Downloads.

**Architecture:** Streamlit renders the diary and coaching. SQLite owns durable data. A same-origin FastAPI host supplies the PWA shell, authenticates remote access, and mounts Streamlit's official ASGI application in one server process.

**Tech Stack:** Python 3.12, Streamlit 1.64, SQLite, FastAPI, httpx, websockets, pytest, Playwright.

## Global Constraints

- Isolated folder: C:/Users/yashs/Downloads/steady-buddy.
- Local-only binding is the default; never modify Bharatiq. The user later requested source publication to a public GitHub repository; live app hosting remains outside this request.
- No external AI or nutrition service is required.
- Tracking needs a running server; cache only public assets.
- No exercise-to-food compensation; daily calorie reference is optional and user supplied.
- Missing check-ins are never counted as alcohol-free days.
- Dates use the user's timezone, default Asia/Kolkata.

### Task 1: Durable diary and coaching

Files: buddy/store.py, buddy/coach.py, buddy/foods.py, tests/test_store.py, tests/test_coach.py.
Interfaces: Store(path).add_food(day, name, calories, portions, meal, save_favourite); Store.add_workout(day, name, minutes); Store.check_in(day, alcohol, mood, win); Store.weigh(day, kg); Store.export(); Store.restore(payload). coach.message(situation, reason) returns supportive text.

- [x] Write regression tests for portions, date validation, independent stores, edits, missing alcohol status, daily weigh-in upsert and atomic restore.
- [x] Run `python -m pytest tests/test_store.py tests/test_coach.py -q` and observe missing-module failure.
- [x] Implement parameterised SQLite writes and strict finite-number/date checks. Reject unknown backup versions and invalid records before replacing any data.
- [x] Rerun those tests until all pass.

### Task 2: Mobile Streamlit experience

Files: app.py, buddy/ui.py, .streamlit/config.toml, tests/test_app.py.
Interfaces: Store tables are queried as lists of dictionaries; settings are JSON values. View renderers accept Store and local date. app.py handles navigation and database errors.

- [x] Build Today, Food, Move, Buddy, Progress and Settings, with accessible labelled inputs and empty states.
- [x] Add AppTest coverage of all pages, meal persistence, workout logging, check-in persistence and optional calorie reference.
- [x] Run `python -m pytest tests/test_app.py -q`; require no Streamlit exceptions.

### Task 3: PWA and private gateway

Files: gateway.py, run.py, web/index.html, web/sw.js, web/offline.html, web/manifest.webmanifest, web/icons/, tests/test_gateway.py.
Interfaces: Gateway mounts the native st.App under /streamlit/ and owns its lifespan; /health is served after startup. run.py owns one server process and defaults to loopback.

- [x] Add manifest, 192/512px/maskable icons, installation guidance and offline fallback.
- [x] Mount native Streamlit HTTP/WebSocket handlers, preserve XSRF protection, enforce same-origin WebSockets and private access.
- [x] Test login, protected routes, safe caching, invalid origin, expiry and remote password requirements.
- [x] Run `python -m pytest tests/test_gateway.py -q`.

### Task 4: Delivery and user-flow verification

Files: Start Steady Buddy.cmd, README.md, requirements.txt, requirements-dev.txt, Dockerfile, compose.yaml, scripts/browser_check.py, output/verification.json.

- [x] Pin dependencies from the tested environment and supply one-click local launch.
- [x] Run Ruff and the full pytest suite.
- [x] Start the gateway with a temporary test database; verify real food/workout/check-in/weight flows, refresh persistence, offline fallback, service worker, manifest and 320/390/768/1440px layout in Playwright.
- [x] Keep the user's clean local app running, open it, and report tested features with clear phone HTTPS hosting requirements.
