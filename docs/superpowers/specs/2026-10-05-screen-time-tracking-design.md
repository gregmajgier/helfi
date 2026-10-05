# Native Screen-Time Tracking - Design Spec

Status: Draft, decisions taken as recommended (autonomous, 2026-10-05)
Owner: gregmajgier@gmail.com
Depends on: [Today dashboard](2026-10-04-dashboard-layout-design.md), [Digital health](2026-09-16-digital-health-design.md)
Source: `review-01.md`, `remaining-work.md` section 1

## Purpose

Replace the three Focus placeholders on the Today dashboard (Focus ring, "time on
dumb apps" stat tile, Focus card) with real data, and let the user exclude
productive apps from tracking. "Dumb apps" = everything not excluded.

## Expo SDK 57 findings (checked against docs.expo.dev/versions/v57.0.0)

- No first-party module exposes Screen Time, DeviceActivity, FamilyControls or
  `UsageStatsManager`. Both platforms need native code via a config plugin, so
  the feature requires a **development build**. It will not run in Expo Go.
- `react-native-device-activity` (MIT, kingstinct) wraps the iOS Screen Time APIs
  and ships an Expo config plugin. It needs an Apple Team ID, an App Group, three
  extension targets, and the Family Controls (Distribution) entitlement approved
  by Apple for the main app and each extension bundle ID.
- iOS never hands usage durations to the app. Apple exposes opaque tokens and
  threshold *events*. Durations can only be inferred from events we schedule.

## Decisions

1. **Android first, iOS second.** Android needs no Apple approval, so it
   delivers real data immediately and proves the data model. iOS starts the
   entitlement request in parallel and ships when approved.
2. **Daily aggregate only.** The app syncs one record per user per local day,
   never per-app usage or app names. This keeps the backend schema
   platform-neutral and the privacy story simple.
3. **Excluded set stays on device.** The user's productive-app list lives in
   device storage (Android package names; iOS `FamilyActivitySelection`
   tokens, which are not portable or readable anyway). Only minute totals are
   uploaded.
4. **Focus ring = daily budget remaining.** The user sets a daily budget for
   dumb-app time (default 120 min). `percent = clamp01(1 - dumbMinutes / budget)`.
   A full ring is a good day. Week mode averages the days' percents.
5. **Local Expo module, not a third-party Android library.** A small module in
   `modules/screen-time` (Expo Modules API, Kotlin) wraps `UsageStatsManager`.
   iOS uses `react-native-device-activity` behind the same TS interface.

## Architecture

```
src/modules/screen_time/
  index.ts          // platform-neutral interface: getPermissionState, requestPermission,
                    //   getDailyUsage(date), listInstalledApps (Android), pickExcludedApps
  usage.android.ts  // calls the local native module
  usage.ios.ts      // calls react-native-device-activity; thresholds every 15 min
  usage.web.ts      // stub: permission "unavailable"
  sync.ts           // computes DailyUsage for a date and PUTs it to the backend
  types.ts
modules/screen-time/   // Expo module (Kotlin): queryUsageStats, openUsageAccessSettings
```

Shared types:

```ts
type DailyUsage = { date: string; total_minutes: number; dumb_minutes: number };
type PermissionState = "granted" | "denied" | "unavailable";
```

### Android

- Permission: `PACKAGE_USAGE_STATS` via the Usage Access settings screen
  (`ACTION_USAGE_ACCESS_SETTINGS`); it cannot be granted by a runtime prompt.
  `getPermissionState` checks `AppOpsManager`.
- `getDailyUsage(date)`: `UsageStatsManager.queryEvents` over the local day,
  summing foreground intervals per package (more accurate than
  `queryUsageStats` buckets). Exclude launcher, system UI and helf itself.
  `dumb_minutes` = total minus excluded packages.
- Excluded picker: installed launchable apps, searchable, multi-select.
  Sensible defaults pre-checked from `PackageManager` categories
  (productivity, education, health & fitness, maps, communication-work is left
  to the user).

### iOS

- Entitlement: request Family Controls (Distribution) for the app and three
  extensions before any iOS build is shippable. Development entitlement works
  on registered devices meanwhile.
- Authorization via `requestAuthorization(individual)`.
- Excluded picker: system `FamilyActivityPicker` (the only way to choose apps).
  The *selected* apps are the **tracked "dumb" set** inverted: iOS cannot
  express "everything except X", so the picker is used to choose the excluded
  productive apps, and the monitor uses an `all apps and categories` selection
  with the excluded tokens removed.
- Duration: schedule a daily `DeviceActivity` monitor with threshold events at
  15-minute steps (up to the budget plus headroom). The extension writes the
  highest threshold reached to the shared App Group; the app reads it. Accuracy
  is therefore 15 minutes, which is acceptable for a daily ring and is
  disclosed in the UI ("approximate on iPhone").

## Backend

Extend `backend/app/screentime` (today it stores rules only):

- Model `ScreenTimeUsageUpsert { total_minutes: int>=0 <=1440, dumb_minutes: int>=0 <=total_minutes }`.
- `PUT /screentime/usage/{date}` (date is `YYYY-MM-DD`, not in the future, at most
  400 days back), idempotent upsert keyed by `(user_id, date)`.
- `GET /screentime/usage?start=&end=` returning the user's records, range
  capped at 366 days.
- New `ScreenTimeUsageRepository` with in-memory and Cosmos implementations,
  partition key `user_id`, document id `usage-{date}`.
- Budget lives on the existing user settings alongside the calorie and move
  goals (`focus_budget_minutes`, default 120, 15 to 720).

## Frontend wiring

- `useDashboardSummary` loads usage for the range (local device value for
  today, backend values for past days) and passes `{ dumbMinutesByDay, budget }`
  to `computeSummary`.
- `computeSummary`: Focus ring percent per decision 4, `tracked` true only when
  permission is granted and a budget exists. Stat tile shows hours of dumb-app
  time (one decimal). Focus card text: `"1h 20m of 2h budget"` /
  `"Set up screen-time tracking"` when untracked.
- Digital health screen gets a "Screen-time tracking" section: permission
  state with a single action button, excluded-apps picker, daily budget
  stepper, platform accuracy note.
- Sync runs on app foreground and after the dashboard loads, at most once per
  15 minutes, and never blocks the UI. Failures are silent and retried later.

## Privacy and security

- No app names or per-app durations leave the device. State this in the
  permission explainer shown before the system prompt.
- Backend validates every field range; the user can only read and write their
  own records (existing `get_current_user_id` pattern).
- Usage endpoints get the same per-user rate limit mechanism as the estimate
  endpoints (60/hour).

## Testing

- Backend: upsert idempotency, range and future-date validation, user isolation,
  `dumb_minutes <= total_minutes`, memory and Cosmos repo parity tests.
- JS (jest-expo): `computeSummary` Focus cases (no data, over budget clamps to 0,
  under budget, week average, untracked); interval-summing and exclusion logic
  kept in a pure function (`sumForegroundIntervals`) with fixtures.
- Native: manual device pass on a physical Android device (Usage Access flow,
  excluded apps change the total) and, once entitled, a physical iPhone. Neither
  platform can be exercised in the simulator or Expo Go.

## Milestones

1. Backend usage endpoints and budget setting (testable now).
2. Dashboard Focus logic with a mocked usage provider (testable now).
3. Android native module, permission flow and picker (needs a dev build).
4. iOS: start the Apple entitlement request, then integrate
   `react-native-device-activity` once approved.

## Open items (not blocking)

- Whether to count helf's own foreground time (default: excluded).
- A tighter iOS accuracy tier (5-minute thresholds) if the extension's event
  limits allow it.
