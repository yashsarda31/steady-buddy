# Steady Buddy redesign

## Visual direction

A calm, premium wellness journal. Warm ivory surfaces, deep forest-green text and actions, muted sage cards, and apricot highlights. Generous spacing, expressive serif headings, clean sans-serif controls, rounded cards, and subtle borders replace the current default dashboard appearance.

Alternatives considered: a dark cinematic interface would add drama but feel heavier for everyday logging; a colourful game-like interface would add energy but introduce pressure into a deliberately gentle companion. The calm direction fits the app's purpose best.

## Experience

- A compact branded header and six clearly labelled destinations: Today, Food, Move, Buddy, Progress, Settings. Navigation remains usable on narrow phones and inside the installed app.
- Today opens with a personal greeting and a softly lit Three.js pebble garden. Quick actions lead immediately to logging a meal, recording movement, or finding encouragement. Three clear cards show actual recorded intake, movement, and check-in status.
- Food presents the logging form and diary as separate visual groups, with readable entry cards and an explicit complete/partial diary state.
- Move presents a suggested small action, a clear logging form, and a weekly progress card.
- Buddy provides a quiet reset space with focused encouragement, the existing working pause timer, and easy check-ins.
- Progress separates recorded habits, optional weight trends, and food history. Empty states explain how to get started without displaying invented progress.
- Settings groups personal preferences, backups and recovery, installation, and support resources.

## Motion and implementation

Keep the existing Streamlit application and Cloud deployment entry point. Use a custom Streamlit v2 component for a locally bundled Three.js scene and GSAP transitions. Build a consistent shared theme and styling layer around native, accessible forms and navigation. Preserve the diary schema and existing browser identity, isolation, backup, and recovery flows.

GSAP supplies short entrance transitions and a slow, gentle scene animation. Respect reduced-motion preferences, pause rendering when hidden or outside the viewport, cap render resolution, and dispose animation and WebGL resources when unmounted. Display a styled static illustration when WebGL is unavailable. Essential content and forms remain usable if visual enhancement fails.

## Data and health semantics

Use actual diary values only. Never deduct exercise from food intake, interpret partial diaries as deficits, count missing alcohol check-ins as alcohol-free, or fill missing weight measurements. Preserve current health support messages and backup warnings. Escape user-provided text in decorative HTML.

## Verification and deployment

1. Run all existing automated tests and lint checks.
2. Exercise actual food, movement, check-in, timer, weight, preference, backup, restore, and recovery flows in isolated test diaries.
3. Check all six views at 320, 390, 768, and 1440 pixels, keyboard navigation, reduced motion, WebGL fallback, and animation cleanup.
4. Verify Cloud iframe installation metadata, icon loading, and browser diary isolation.
5. Push the tested release to the existing public repository's main branch, which triggers the existing Streamlit Community Cloud redeployment.
6. Verify the redesigned live app at https://steady-buddy.streamlit.app/, including the new visual assets, navigation, install controls, and absence of application errors. Do not write test health records into the live diary.

## Execution order

Approve the visual direction; build the shared shell and locally bundled scene; redesign all six screens; run functional and visual checks; fix findings; publish and verify the live release.
