# helf Rebrand, Design System & Onboarding — Design Spec

Status: Draft, approved in chat 2026-10-02
Owner: gregmajgier@gmail.com
Depends on: [Platform Architecture](2026-09-16-platform-architecture-design.md)
Extends/amends (phase-1 scope only, APIs unchanged unless noted):
[Mental Health](2026-09-16-mental-health-design.md),
[Digital Health](2026-09-16-digital-health-design.md)

## Purpose

Rename the app to **helf**, give it an actual design system (today it's raw
`Button`/`Text`), and ship a pre-signup onboarding flow that introduces the
app's four pillars and gets the user invested before asking them to create an
account. The four pillars each get a name and a color that recurs everywhere
(tab bar, module headers, progress UI) instead of being themed once on a
hub screen.

This also carries Mental Health and Digital Health from "approved spec, zero
code" to real modules, since onboarding's goal-setting step needs live
endpoints to write real first-use data into (a real mood entry, a real draft
screen-time rule) rather than throwaway answers.

## The four pillars

| Pillar | Maps to module | Color (light) | Color (dark) |
|--------|-----------------|---------------|---------------|
| **Move** | training-tracker (existing) | `#E8623D` terracotta | `#FF8162` |
| **Fuel** | meal-tracker (existing) | `#7C9A5C` sage | `#9CBB7A` |
| **Mind** | mental-health (new, phase 1) | `#8B7FD1` lavender | `#A79BEB` |
| **Focus** | digital-health (new, phase 1) | `#3E9A96` slate teal | `#5CC2BD` |

These are user-facing display names and accent colors only — existing route
folders (`training-tracker`, `meal-tracker`) and API prefixes (`/mood`,
`/screentime`) keep their current names to avoid churn on already-shipped,
tested code. "Move/Fuel/Mind/Focus" live in UI copy and a
`PILLARS` lookup table in the design system, not in file paths.

## Design system

New `src/lib/theme.ts` exporting:

- **Neutrals** (structure, text, backgrounds — do the heavy lifting; pillar
  colors are accents only, not a wash over every screen):
  - Light: background `#FBF9F6`, surface `#FFFFFF`, text primary `#22262B`,
    text secondary `#6B7177`, border `#E6E2DC`.
  - Dark: background `#16181C`, surface `#1F2227`, text primary `#F4F2EE`,
    text secondary `#9BA1A8`, border `#2B2F35`.
  - Follows `userInterfaceStyle: "automatic"` (already set in `app.json`) via
    `useColorScheme()`.
- **Pillar colors** — the table above, each as `{ light, dark }`.
- **Typography** — Plus Jakarta Sans (via `@expo-google-fonts/plus-jakarta-sans`),
  weights 500/600/700/800. Friendly geometric sans, not a rounded "kids app"
  font, not a default system font either.
- **Spacing scale** — 4/8/12/16/24/32/48.

New `src/components/` primitives built on these tokens: `Button` (primary /
secondary / text variants), `Card`, `PillarTile`, `Chip` (multi/single select,
used in onboarding), `ProgressDots` (carousel indicator), `ScreenContainer`
(safe-area + padding + background).

### Brand assets

- `app.json`: `name` → "helf". Tagline "Small steps. Every part of you." used
  in onboarding copy, not in app.json itself.
- Splash screen background → neutral `#FBF9F6` with a simple "helf" wordmark
  asset replacing the current generic `splash-icon`.
- **Open assumption** (flagging rather than deciding silently): `slug`
  (`health_app`) and `scheme` (`healthapp`) are left unchanged in this pass.
  Renaming them is safe cosmetically but could break an existing EAS
  project link or OAuth redirect URI if either was already configured
  outside this repo — confirm before renaming those two fields specifically.

## Onboarding flow

Runs **before** account creation. Route group `src/app/onboarding/`, a Stack
with no header, in this order:

1. **Welcome** — wordmark, tagline, "Get Started" CTA, small "Already have an
   account? Log in" link → `/login` (skips onboarding entirely for returning
   users on a new device).
2. **Pillar carousel** — 4 swipeable full-bleed slides, one per pillar color,
   icon + one-line value prop each. Dots indicator.
3. **Move goal** — "How many workouts a week are you aiming for?" stepper,
   1–7.
4. **Fuel goal** — "What's your main food goal?" 4 chips: Lose weight /
   Maintain / Build muscle / Eat healthier.
5. **Mind check-in** — "How are you feeling right now?" 5-point mood picker.
   This is the user's **real first mood entry**, not throwaway.
6. **Focus apps** — "Which apps tend to eat your time?" multi-select chips
   (Social, Games, Video/Streaming, News, Shopping, Other). Seeds a **real
   draft screen-time rule** (disabled, no schedule yet — just named +
   categorized, user tunes it later in Focus).
7. **Notification permission** — asked in context, not upfront-and-vague:
   copy specifically says "we'll remind you about your Mind check-in."
   Requests permission via `expo-notifications` and, if granted, schedules
   one local daily reminder (default 8pm, hardcoded this phase — no
   settings UI to change it yet). Declining skips silently, no nagging.
8. **Account creation** — reuses existing `(auth)/register.tsx` with updated
   styling, not a new screen.
9. **Recap** — "You're all set" screen echoing the 4 answers back, then
   lands on the hub.

### Answer persistence

Answers are written incrementally to a pending-answers key via a new
`src/lib/onboarding-store.ts` helper (backed by
`@react-native-async-storage/async-storage`, a new dependency — nothing
sensitive is stored here, so this is the right tool rather than
`expo-secure-store`). Using plain storage writes rather than React Context
means answers survive navigating from the `onboarding` route group into the
`(auth)` group for registration, which are different stacks.

On successful registration:

1. POST the Mind answer to `/mood/entries`.
2. POST the Focus answer as a disabled, unscheduled `/screentime/rules` row.
3. Store Move/Fuel goals under permanent local keys (`move_goal_per_week`,
   `fuel_goal`) — **not synced to the backend this phase**, shown on the hub
   as a personal target only. A real backend-synced goals concept is a
   reasonable fast-follow, not blocking this pass.
4. Clear the pending-answers key, set `onboarding_complete = true`.
5. Navigate to the hub.

If steps 1–2 fail (network blip right after registering), don't block the
user on the hub over it — retry once in the background, then drop silently
with a console warning. A missing seed mood entry or draft rule is a minor
loss, not a reason to strand a newly-registered user on an error screen.

### Routing changes

`src/app/index.tsx`: currently redirects to `/login` whenever `user` is null.
Add an `onboarding_complete` check (read via `onboarding-store.ts`) before
that redirect — while unresolved, render nothing (same pattern as the
existing `isLoading` check); if `false`/unset, redirect to `/onboarding`
instead of `/login`.

## Hub becomes a tile dashboard

`src/app/index.tsx` is rebuilt as a "Today" dashboard: four colored cards,
one per pillar (Move / Fuel / Mind / Focus), each tinted its pillar color
and showing a quick status line — this week's workout count vs. the local
goal, today's meals logged, last Mind check-in, count of active Focus rules.
Tapping a card pushes into that module's existing route
(`/training-tracker`, `/meal-tracker`, `/mental-health`, `/digital-health`);
back returns to Today. No tab bar, no restructuring of the existing
`training-tracker`/`meal-tracker` routes into an expo-router tab group —
they keep their current top-level paths.

Each pillar's own screens (headers, primary buttons, progress indicators)
carry that pillar's accent color so the identity doesn't disappear once the
user taps past Today — persistence of color comes from consistent accenting
within each module, not from a persistent nav bar.

Log out moves into a small account icon in the Today header rather than a
standing visible button — a dedicated settings/profile screen is out of
scope this phase.

## Mental Health (Mind) — building the existing spec, unchanged

Full scope from the existing approved spec: check-in, journal, history,
rotating prompts. No API or data-model changes from that spec — only the
visual skin (Mind color/typography) and the fact that the first check-in
gets seeded by onboarding are new here.

- `backend/app/mood/{models.py,router.py}` mirroring the `workouts` module's
  structure; repo interfaces added to `db/base.py`, implementations in
  `db/memory.py` and `db/cosmos.py`, wired in `deps.py`, router registered in
  `main.py` at `/mood`.
- `src/app/mental-health/{_layout.tsx,index.tsx,journal.tsx,history.tsx}`,
  `src/modules/mental_health/{api.ts,types.ts}` — same shape as
  `training_tracker`.

## Digital Health (Focus) — phase 1: rules only, no enforcement

This is a deliberate scope cut of the existing spec, not a shortcut: that
spec's own error-handling section already defines a "rule configuration
only, enforcement disabled" degraded state for when the iOS entitlement
isn't approved yet. Phase 1 ships permanently in that state; native
enforcement (`FamilyControls`/`DeviceActivity`/`ManagedSettings` on iOS, an
Accessibility Service overlay on Android) is unchanged future scope, and per
the platform spec's rollout sequencing, the most native-code-heavy and
review-risky piece — building it now would mean standing up EAS dev-client
native modules and an Apple entitlement request as a side effect of a
branding task.

Phase 1 scope:

- `backend/app/screentime/{models.py,router.py}`: `GET/POST /screentime/rules`,
  `PATCH/DELETE /screentime/rules/{id}`. **No** usage-upload or usage-dashboard
  endpoints this phase — there's no on-device collection yet to produce that
  data, so shipping those endpoints now would have nothing to call them.
- Rule fields, trimmed from the full spec: `name`, `apps_or_categories`,
  `daily_limit_minutes?`, `enabled`. Scheduled time-windows (`schedule`) are
  deferred alongside enforcement, since a time-window is meaningless without
  something enforcing it.
- `src/app/digital-health/{_layout.tsx,index.tsx,rule-builder.tsx}`: dashboard
  lists rules with an "Enforcement coming soon" banner; rule-builder covers
  name + category chips + optional daily limit + enabled toggle.
- `src/modules/digital_health/{api.ts,types.ts}`.

## Error handling

Follows the platform spec's conventions (`{ error: { code, message } }`,
ownership checks on every row). Additive rule for this phase:

- Onboarding's post-registration data seeding (mood entry, draft rule) is
  best-effort per the Answer Persistence section above — never blocks
  reaching the hub.
- Local notification scheduling failure (permission denied, or the API call
  throwing on an unsupported platform like web) is caught and ignored — it's
  a nice-to-have, not a flow blocker.

## Testing

- Backend: pytest contract tests for `/mood` and `/screentime` routes
  (auth required, validation, ownership), mirroring existing test files —
  new `test_mood_router.py`, `test_screentime_router.py`; extend
  `test_memory_repositories.py` and `test_cosmos_repos.py` for the two new
  repo pairs.
- Client: no automated test suite, consistent with the platform spec's
  existing decision. Manual QA must specifically cover the onboarding → data
  handoff (fresh install → full onboarding → register → confirm the mood
  entry and draft rule actually exist for that user), since that's the
  highest-risk silent-failure point introduced by this spec.

## Rollout sequencing

1. Design system (`theme.ts`, components) — everything else depends on it.
2. Mental Health (Mind) module — backend + screens, standard CRUD pattern
   already proven by meal/training trackers.
3. Digital Health (Focus) module, phase 1 — backend + screens, no native
   code.
4. Onboarding flow + hub tab-bar rework + rebrand — ties the above together
   and is the most visible/riskiest-to-navigation piece, so it goes last
   once the modules it links to actually exist.

## Open assumptions to confirm

- `app.json` `slug`/`scheme` left unchanged this phase (see Brand assets) —
  flag if either was already wired into an external config (EAS project,
  OAuth redirect) that should also be renamed.
- Move/Fuel goals are local-only this phase, not backend-synced — confirm
  that's acceptable short-term (a user reinstalling or switching devices
  loses their goal number, though not their actual logged data).
- Default local reminder time (8pm) is hardcoded with no settings UI to
  change it — acceptable for phase 1, or should a simple time picker be
  in scope now instead of as a fast-follow?
