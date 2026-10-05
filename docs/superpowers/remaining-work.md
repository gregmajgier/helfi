# Remaining Work

Last updated: 2026-10-05. Source: `review-01.md`.

## Done (uncommitted, tsc clean, iOS bundle builds)

- Design System v2 spec and implementation: new palette, radius/shadow/motion tokens, Phosphor pillar icons, `AnimatedPressable`, rebuilt `Button`/`Card`/`Chip`/`PillarTile`/`ProgressDots`, `src/lib/motion.ts` (reduced-motion aware).
- Today dashboard spec and implementation: Day/Week toggle, date nav, animated `RingCluster`, `StatTile` row, pillar cards, `src/modules/dashboard/` (types, `summary.ts`, `useDashboardSummary`).
- Specs committed: `specs/2026-10-04-dashboard-layout-design.md`, `specs/2026-10-04-design-system-v2-design.md`.

## 0. Wrap up the finished work

- [ ] Run the app in iOS Simulator and Android, light and dark mode. Check rings, shadows, tinted surfaces, icons, press feedback, entrance stagger, and that Reduce Motion disables springs. Nothing has been checked visually yet.
- [ ] Review and commit the implementation. My edits overlap your earlier uncommitted changes in the screen files (the `colors.danger` replacement), so stage deliberately.
- [x] Add a JS test runner (none exists). Then write the tests the specs call for: `computeSummary`/`rangeFor` (day vs week, capping at 100%, no-goal gives `tracked: false`) and the label-contrast check for pillar colours.
- [x] Fix `expo lint`: it fails because `eslint` is not installed.
- [x] Update the dashboard spec: its "Visual direction" section is superseded by the design-system spec. Its "Date nav" wording also differs slightly from what was built (a `‹ date ›` row with the "Today"/"This week" label inside the ring).
- [x] Sweep remaining screens for raw `Pressable` buttons and leftover hardcoded `#FFFFFF` so they adopt `AnimatedPressable` and tokens (mood-face buttons in `mental-health/index.tsx` first).
- Done 2026-10-05: jest-expo + RTL installed (`npm test`, 16 tests for `summary.ts` and theme contrast); `expo lint` clean (one pre-existing `useMemo` warning in `auth-context.tsx`); mood faces and goal-move steppers use `AnimatedPressable`.
- Still needs a human/simulator: the visual pass (first item) and review of the commit split.
- Known limitation: Android tinted shadows fall back to neutral `elevation`.

## 1. Native screen-time tracking (spec not yet written)

Needed for the Focus ring, the "time on dumb apps" stat and the Focus card, which are placeholders today.

- [ ] Brainstorm and write a spec. It is its own architectural project.
  - iOS: Screen Time API (Family Controls / DeviceActivity), which needs an Apple entitlement request and a custom dev client (does not run in Expo Go).
  - Android: `UsageStatsManager` via a native module or config plugin, plus the Usage Access permission flow.
- [ ] Let the user exclude productive apps from tracking (from `review-01.md`). Define "dumb apps" as everything not excluded.
- [ ] Backend: store or sync usage data. Today the digital-health module only stores limit rules.
- [ ] Wire real data into `computeSummary`: Focus ring percent, screen-time stat tile (currently a hard-coded "-"), and the Focus card text.
- [ ] Check Expo SDK 57 docs for config plugins before writing code, per `AGENTS.md`.

## 2. Onboarding redesign (spec not yet written)

From `review-01.md` section 1.

- [ ] Replace the "ugly" main food goal buttons (`onboarding/goal-fuel.tsx`).
- [ ] Make onboarding longer and more detailed, and a stronger hook, both visual and motivational.
- [ ] Redesign the "You're all set" screen.
- [ ] Build on Design System v2 (Chips, Cards, PillarIcon, motion).

## 3. OAuth (spec not yet written)

- [ ] Decide providers (for example Apple, Google). Apple Sign-In is required on iOS if any other social login is offered.
- [ ] Backend: token verification endpoint and user linking with the existing email/password accounts.
- [ ] Frontend: sign-in buttons on `(auth)/login.tsx` and `register.tsx`, plus the onboarding handoff.
- [ ] Check Expo SDK 57 docs (`expo-auth-session`, `expo-apple-authentication`) first.

## Order

Wrap up (0), then screen-time (1), then onboarding (2) and OAuth (3). Onboarding and OAuth can share one spec or be split.
