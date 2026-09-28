# Verification · 28 September 2026

## Streamlit Community Cloud update

- **51 automated tests:** the existing diary, coaching, page and access checks, plus separate browser diaries, validated browser keys, automatic recovery, rejection of broken backups, Cloud startup routing and preservation of the legacy diary.
- **Ruff:** no findings.
- **11 direct Streamlit browser checks:** food arithmetic and reload persistence, movement, craving timer and check-in, weigh-in, backup download/restore, native installation help, manifest/icons/Chromium installability, deferred install event, separate browser privacy, recovery after a simulated Cloud disk reset, and hiding installation controls after installation.
- **24 Cloud-mode layout checks:** all six views at 320, 390, 768 and 1440 pixels without horizontal overflow.
- **Community Cloud iframe simulation:** app rendered inside a sandboxed same-origin `/~/+/` frame; the app manifest replaced the outer platform manifest; icons loaded; Chromium reported zero installation errors; a fresh browser opened Buddy directly.
- **Local gateway:** nine browser flows and 24 layout checks passed. Its authenticated gateway remains covered by the automated tests below.

The automatic recovery copy is browser-specific. It cannot survive clearing browser site data, and it does not sync devices. JSON backup/restore transfers a diary to another device or browser. Cloud installation requires an active connection and does not provide offline logging. Physical Android/iPhone installation still requires device verification.

Detailed reports, screenshots and disposable test diaries are under ignored `output/`. Browser checks never write to the live diary. GitHub Actions now runs the automated tests and lint on pushes and pull requests.

## Original local gateway verification

- **41 pytest tests passed:** durable diary records, portion arithmetic, validation, dates, atomic backup restore, completeness semantics, coaching, all six Streamlit views, cookie expiry, CSRF, origin checks, protected WebSockets, password rotation, secure HTTPS cookies and local host restrictions.
- **Ruff passed** with no findings.
- **9 real browser flows passed:** native Streamlit session; meal logging and refresh persistence; movement; craving support and a running/resettable timer; alcohol-free check-in; weigh-in chart; JSON download and restore through the actual file uploader; PWA manifest/service worker; offline recovery. Some checks group related steps.
- **3 private-access browser checks passed:** password login, authenticated native diary/WebSocket render, and Lock with protected reconnect.
- **24 layout checks passed:** Today, Food, Move, Buddy, Progress and Settings at 320, 390, 768 and 1440 pixels, with no horizontal document overflow.
- Chrome's installability check returned **zero errors**. The root-scope service worker activated, cached only public resources and served the honest offline screen.
- Browser page errors: **zero**.

All test data was stored in an isolated local test database. Test databases, downloads, screenshots, logs, backups, secrets and the local environment are excluded from the repository.

The supplied Docker/HTTPS hosting package has not been deployed. Physical Android/iPhone home-screen installation has not been verified; that requires the app at an HTTPS address on the device. Localhost installation works only on the computer running it. There are no background push notifications or offline diary writes.
