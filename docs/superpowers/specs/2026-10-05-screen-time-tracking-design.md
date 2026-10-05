# Native Screen-Time Tracking - Design Spec

Status: Milestones 1-3 implemented on `feat/screen-time`; milestone 4 is documented in
[ios-screen-time-setup.md](../ios-screen-time-setup.md) and waits for Apple. See "Implementation decisions" at the end.
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

## Implementation decisions (2026-10-05, autonomous; they override the text above where they differ)

1. **Budget is stored on the device, not the backend.** The spec said "existing user settings", but the calorie and
   move goals live in AsyncStorage (`src/lib/onboarding-store.ts`) and the backend has no settings store. The budget
   follows that pattern: `src/modules/screen_time/settings.ts`, key `helf.focus.daily_budget_minutes`, default 120,
   clamped to 15-720 in 15-minute steps. No `focus_budget_minutes` field exists in the API. Why: adding a user-settings
   endpoint is a separate cross-cutting change, and the ring is computed on the device anyway. Revisit when goals sync.
2. **Date validation allows tomorrow.** `PUT /screentime/usage/{date}` rejects dates more than one day ahead of the
   server's UTC date, not any future date, because a user's local day can be ahead of UTC by up to 14 hours.
3. **The usage limiter lives in `screentime/router.py`.** It reuses `SlidingWindowLimiter` (60/hour per user) but is a
   separate instance, so `app/ratelimit.py` stays untouched. `tests/conftest.py` resets it per test. Limits are
   per replica, same as the estimate limiter.
4. **Interval summing is TypeScript, not Kotlin.** The native module only returns raw `UsageEvents` (foreground,
   background, stopped, screen off, shutdown). `sumForegroundIntervals` in `foreground.ts` does the summing, and
   jest covers it with 16 fixtures. Why: this machine has no JDK or Android SDK, so Kotlin unit tests could not be
   run, and one tested implementation beats a Kotlin copy kept in sync by hand. Event volume per day is small
   (hundreds to a few thousand, capped at 50,000).
5. **Midnight and open intervals.** An app already open at the start of the window is credited from the window start
   only when the first event is its background event. An interval still open at the end is closed at
   `min(window end, now)`.
6. **Always ignored on Android:** helf itself, `com.android.systemui` and every HOME (launcher) package. They count in
   neither the total nor the dumb minutes. Excluded (productive) apps count in the total only.
7. **No `usage.web.ts`.** `usage.ts` is the default provider (unavailable), used by web, jest and tsc. Metro picks
   `usage.android.ts` or `usage.ios.ts` on device.
8. **Permission manifest.** `PACKAGE_USAGE_STATS` and the package-visibility `<queries>` live in the module's own
   `AndroidManifest.xml`, so the Gradle manifest merger adds them and `app.json` needs no change. `QUERY_ALL_PACKAGES`
   is deliberately not used (Play restricts it). The JS side uses `requireOptionalNativeModule`, so Expo Go shows
   "unavailable" instead of crashing.
9. **Focus numbers.**
   - Week mode averages the per-day percents over days that have data; days without data are ignored, not counted as
     perfect or empty.
   - The stat tile is the sum of dumb hours in the range, one decimal.
   - The card reads `1h 20m of 2h budget` (day) or `1h 20m avg of 2h budget` (week).
   - With permission granted but no data: ring untracked, card `No screen-time data yet`.
   - Without permission: `Set up screen-time tracking`.
10. **Default excluded apps** are only those whose `ApplicationInfo.category` is productivity or maps. Education and
    health and fitness have no such category on Android, so the user picks them. The default set is offered the first
    time the picker opens; nothing is saved until the user presses Save.
11. **Today comes from the device, past days from the backend.** The dashboard reads today's value live from the
    provider so it is never 15 minutes stale. Past days use synced records. Sync runs when the dashboard mounts and on
    every foreground, throttled to 15 minutes, and also uploads yesterday once per day so it ends final. Failures are
    silent and do not record a sync time, so they retry on the next trigger. Sync only runs while the home screen is
    mounted; a background task is future work.
12. **iOS bundle ID** `com.gregmajgier.helf` is a proposal in the iOS doc, not applied to `app.json`.

## Not verified here

- Kotlin was written but not compiled or run: no JDK or Android SDK on this machine. `expo prebuild --platform
  android` succeeds in a scratch copy and autolinking resolves `expo.modules.screentime.ScreenTimeModule`, but the
  Gradle build, manifest merge and runtime behaviour need a dev build on a physical Android device.
- Usage Access flow, the excluded-apps picker and real totals need that device pass.
- iOS is entirely unbuilt.
