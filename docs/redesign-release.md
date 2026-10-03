# Steady Buddy wellness redesign — 3 October 2026

All six screens now share an ivory, sage, forest-green and apricot design system, local DM Sans/Fraunces fonts, responsive navigation, clearer task groups, and readable empty states. Today and Buddy include a Three.js pebble garden; GSAP supplies gentle scene and page motion.

The existing diary schema, browser identity, recovery format, health semantics, six routes, and Cloud entry point are retained. Visual libraries and fonts are served by the app. No external visual CDN, analytics, or new provider is required.

## Pre-release evidence

- 51 pytest checks passed; Ruff and diff whitespace checks passed.
- Direct Cloud-mode browser check: 11 functional groups and 24 screen-size checks passed, including diary isolation, recovery after a simulated server reset, backup/restore, installation, and the pause timer.
- Local gateway browser check: 9 functional groups and 24 screen-size checks passed, including reconnect and the offline fallback without private diary caching.
- Cloud iframe check: outer-page installation metadata, icons, Chromium installability, and fresh direct-route startup passed.
- Redesign browser check: 10 groups and 24 screen-size checks passed, with zero violations in 12 automated accessibility scans and zero page errors. Includes keyboard navigation/calendar, mobile installation without a hosting-toolbar overlap, changing reduced-motion preferences, missing WebGL and visual assets, offscreen animation suspension, and WebGL/GSAP cleanup on four consecutive page departures.
- Actual phone and desktop screenshots were inspected for Today, Food, Move, Buddy, Progress and Settings. These are browser viewport checks, not physical-device installation or screen-reader certification.

Detailed local reports remain in the ignored `output/` folder. Test diary records and browser identities are not included in the repository.

## Release procedure

Push the tested redesign branch and verify its GitHub Actions check, then fast-forward the existing `main` deployment branch. Streamlit Community Cloud reads `app.py` from that branch. Confirm the actual live iframe renders the redesign, local fonts and WebGL scene, all six routes, and installation controls.

## Rollback

If the released app cannot open a diary or an essential form stops working, revert the redesign commit on `main` and push the revert to trigger Cloud recovery. The preceding release is `1db170d`. This redesign introduces no database migration, so rollback does not require transforming diary data. A static garden fallback is an expected supported state when WebGL is unavailable.
