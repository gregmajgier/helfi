# Today Dashboard Layout — Design Spec

Status: Draft, approved in chat 2026-10-04
Owner: gregmajgier@gmail.com
Depends on: [helf Rebrand, Design System & Onboarding](2026-10-02-helf-brand-onboarding-design.md)
Related (future, not a dependency): Screen-Time Native Tracking spec (not yet
written) — Focus data in this spec ships as a placeholder until that lands.

## Purpose

Replace the current Today screen (`src/app/index.tsx`), which is a static
grid of four status tiles, with an Apple-Health-style dashboard: a day/week
toggle, a date header surrounded by four concentric progress rings (one per
pillar), a row of four at-a-glance stats, and four pillar-colored detail
cards that lead into each module. Source doc: `docs/superpowers/review-01.md`
section 2.

Out of scope: real screen-time usage tracking (separate spec), onboarding
changes (separate spec), any backend schema changes — this is a frontend
aggregation + presentation layer over existing APIs.

## Data layer

New `src/modules/dashboard/`:

- `types.ts` — `ViewMode = "day" | "week"`, `PillarProgress = { pillar: PillarKey; percent: number; tracked: boolean }`, `DashboardSummary = { date: string; viewMode: ViewMode; rings: PillarProgress[]; stats: { caloriePercent: number | null; trainingHours: number; focusMinutes: number | null; rating: number | null }; cards: Record<PillarKey, string> }`.
- `useDashboardSummary(anchorDate: Date, viewMode: ViewMode): { summary: DashboardSummary | null; loading: boolean; reload: () => void }` — a hook that computes the range (single day, or the Mon–Sun week containing `anchorDate`) and fetches/aggregates from the existing module APIs in parallel:
  - **Move**: `listWorkouts()` filtered into range; sum `duration_s`. Day and
    week ring percents use the exact formula in "Move ring formula" below.
    No goal set → `tracked: false` for both rings.
  - **Fuel**: `listEntriesForDay` for each day in range, sum `calories`; `getDailyCalorieGoal()`. Day: `min(1, caloriesToday / goal)`. Week: `min(1, totalCaloriesWeek / (goal * 7))`. `tracked: false` if no goal set.
  - **Mind**: `listMoodEntries(start, end)`; average `mood_score` across entries in range, `percent = avg / 5`. `tracked: false` if zero entries.
  - **Focus**: always `{ percent: 0, tracked: false }` for now; ring renders as a dim empty track, stat tile shows "Not tracked yet", card shows "Screen-time tracking coming soon".
  - Runs all four lookups via `Promise.all`, each independently wrapped in `.catch(() => <empty>)` so one module's failure doesn't blank the whole dashboard (matches existing pattern in `src/app/index.tsx`).

### Move ring formula (resolving the ambiguity above)

Daily share is defined in terms of **minutes**, not workout count, since
duration is what's actually loggable per day:

```
weeklyGoalMinutes = weeklyGoal (workouts/week) * 45  // fixed assumption: 45 min/session
dailyShareMinutes = weeklyGoalMinutes / 7
dayPercent = weeklyGoal ? min(1, minutesTrainedToday / dailyShareMinutes) : 0 (tracked: false)
weekPercent = weeklyGoal ? min(1, workoutsThisWeek / weeklyGoal) : 0 (tracked: false)
```

The 45-min/session assumption is a placeholder constant in
`src/modules/dashboard/summary.ts`; revisit if/when per-workout duration
goals are added. This only affects the *daily* Move ring — the weekly ring
(and the existing move goal everywhere else in the app) is untouched.

## Screen layout

`src/app/index.tsx` body (the authenticated branch) becomes:

1. **Header row** (unchanged): "helf" wordmark + log out, as today.
2. **View toggle**: segmented control, "Day" / "Week", local `viewMode` state.
3. **Date nav**: a `‹ date ›` row stepping by one day or by one week
   depending on `viewMode`. Row label: day → "Today" / "Yesterday" / full
   date; week → "This week" / "Oct 28 – Nov 3". The ring centre shows the
   "Today" / "This week" label. `›` is disabled once the range reaches the
   present, so you cannot navigate into the future.
4. **Ring cluster**: new `RingCluster` component — four concentric
   `react-native-svg` circles (outer→inner: Move, Fuel, Mind, Focus), each
   stroked in its pillar color via `stroke-dasharray`/`stroke-dashoffset` for
   the fill percent, rounded line caps, a dim track color underneath (same
   pillar color at low opacity) so an untracked/0% ring is still visible as
   an outline. Date label renders centered inside via absolute positioning.
5. **Stats row**: four `StatTile` components (new), horizontally laid out,
   each a compact card: value + label. Values: "`{caloriePercent}%` Calorie
   goal", "`{trainingHours}h` Trained", "Not tracked yet" (Focus, always),
   "`{rating}/5` Rating". Any `null` stat (goal not set / no data) renders as
   "—" with the label still shown.
6. **Pillar cards**: evolve existing `PillarTile` usage into four cards (same
   component, extended) — each keeps its current tap-through navigation
   (`/training-tracker`, `/meal-tracker`, `/mental-health`, `/digital-health`)
   and accent-color styling, with one added detail line sourced from
   `summary.cards[pillar]` (e.g. Move: "3/4 workouts this week"; Fuel: "1,840
   / 2,200 kcal today"; Mind: "Checked in today"; Focus: "Screen-time
   tracking coming soon").

State (`viewMode`, `anchorDate`) lives in `src/app/index.tsx`; both feed
`useDashboardSummary`, which reloads via `useFocusEffect` (same pattern as
today) plus whenever `viewMode`/`anchorDate` change.

## New dependency

`react-native-svg` — standard Expo-compatible SVG renderer, works in Expo Go
(no custom dev client needed), used only for `RingCluster`'s arcs. Considered
`@shopify/react-native-skia` (more powerful, but requires a native dev
client and is overkill for four progress arcs) and a pure-`View`
border-rotation trick (imprecise for concentric multi-ring fills) — rejected
both in favor of `react-native-svg`.

Per `AGENTS.md`, confirm `react-native-svg`'s install/usage against
https://docs.expo.dev/versions/v57.0.0/ (Expo SDK version pinning, config
plugin requirements if any) before adding it, since Expo's APIs may differ
from older docs/training data.

## Visual direction

Superseded by `2026-10-04-design-system-v2-design.md` (palette, radius/shadow/
motion tokens, Phosphor pillar icons, `AnimatedPressable`). `RingCluster`,
`StatTile` and the pillar cards are built on those tokens.

## Error handling

- Per-module fetch failures are caught individually (see Data layer) — a
  failing module shows `tracked: false` / "—" for its slice rather than
  blanking the whole screen.
- No calorie/move goal set: relevant ring/stat shows untracked state, not an
  error — this is an expected pre-onboarding-goal-setting state, not a bug.
- Navigating the date nav past "today" is prevented client-side (button
  disabled), not an error state.

## Testing

- Unit tests for `src/modules/dashboard/summary.ts` (pure aggregation
  functions, no network): day vs week ranges, goal-met percent capping at
  100%, zero-data / no-goal → `tracked: false`, Move's minutes-based daily
  formula.
- Existing Jest/RTL smoke coverage for `src/app/index.tsx` extended to cover
  the new toggle (day↔week re-renders) and date nav (prev/next updates the
  label and triggers a reload) using mocked module APIs.
- Manual iOS Simulator pass: verify ring arcs render correctly in both light
  and dark mode, with at least one pillar in each of 0% / partial / 100%
  fill to check stroke rendering and the dim/untracked track.

## Open items carried forward (not blocking this spec)

- Real Focus/screen-time data: separate spec, to be written next per the
  agreed build order (Dashboard → Screen-time → Onboarding+OAuth).
- The 45-min/session assumption in the Move daily formula is a placeholder;
  no action needed now, flagged for whoever revisits per-workout duration
  goals.
