# Digital Health (Screen Time & Blocking) — Design Spec

Status: Draft, approved in chat 2026-09-16
Depends on: [Platform Architecture](2026-09-16-platform-architecture-design.md)

## Purpose

"Digital health" here means phone/screen-time habits: how much time is spent
on the device and in which apps, plus the ability to actively block apps or
limit their use on a schedule (mornings/evenings) — the same territory as
apps like Refocus, Opal, or One Sec.

## The platform constraint this spec is built around

iOS and Android expose fundamentally different capabilities here, and the
spec is honest about that rather than promising false parity:

- **iOS** (`FamilyControls` + `DeviceActivity` + `ManagedSettings`
  frameworks): requires Apple's Family Controls entitlement. Real per-app
  usage **numbers are never exposed to your app code** — Apple renders them
  inside a sandboxed `DeviceActivityReport` extension that only the user sees
  on-device. What your app *can* get and act on: opaque app/category tokens
  (via `FamilyActivityPicker`, not real app identifiers), scheduled shields
  (`ManagedSettings` "block this app/category during this window"), and
  threshold events from `DeviceActivityMonitor` (e.g. "the user's Social
  category crossed 60 minutes today" as an event, not a number you can query
  freely). So: blocking and time-limit enforcement are fully achievable;
  exportable numeric analytics are not.
- **Android**: no equivalent restriction on reading usage data
  (`UsageStatsManager`, granted via the user enabling "Usage Access" in
  Settings) — real per-app minutes, exportable to the backend. Blocking has no
  first-party API; it's done via a foreground **Accessibility Service** that
  detects the active app and shows a blocking overlay during a scheduled
  window or once a time limit is hit. This is the same technique every
  Android focus app uses; Play Store review scrutinizes
  `BIND_ACCESSIBILITY_SERVICE` usage more closely, so the app's stated
  purpose and permission-rationale screen matter for approval.

## Scope

- **Rule configuration** (synced to backend, same on both platforms): named
  blocking rules — a set of apps/categories, a schedule (e.g. "6-9am,
  8-11pm"), and/or a daily time limit per app/category.
- **Enforcement** (on-device, platform-specific per above):
  - iOS: `ManagedSettings` shields apply the configured rules; `DeviceActivity`
    schedules and thresholds trigger shield changes.
  - Android: Accessibility Service checks the foreground app against active
    rules and shows a full-screen blocking overlay when a rule applies.
- **Usage visibility**:
  - Android: daily/weekly per-app usage synced to the backend, shown as
    charts/breakdowns, same as a typical screen-time dashboard.
  - iOS: real usage shown on-device via a `DeviceActivityReport` extension
    (styled to match the app as much as Apple's API allows); only
    threshold-crossing *events* (not full numbers) sync to the backend, so
    cross-device history on iOS is necessarily thinner than Android.
- Mindful-use nudges: a gentle in-app or notification-based nudge when a
  scheduled block is about to start, or a limit is close to being hit.

## Out of scope (this phase)

- Any attempt to work around iOS's data restriction (e.g. screenshotting the
  report extension) — treat Apple's boundary as a hard constraint, not a
  problem to engineer around.
- Family/parental multi-user management (this is single-user self-management,
  not a parent managing a child's device).
- Cross-app blocking based on content (e.g. blocking specific websites within
  a browser) — app-level granularity only.

## Data model

**`screentime_rules` container** (per-user, partitioned by `/user_id`):
```
{ id, user_id, name, apps_or_categories: string[],
  schedule?: [{ days: string[], start_time, end_time }],
  daily_limit_minutes?, enabled, created_at, updated_at }
```

**`screentime_usage`** (per-user, Android only for full data; iOS writes
threshold events only):
```
{ id, user_id, date, platform: "ios"|"android",
  // android: per-app minutes
  app_usage?: [{ app_id, minutes }],
  // ios: events only
  threshold_events?: [{ category_token, crossed_at, limit_minutes }] }
```

## API (`/screentime` router)

- `GET/POST /screentime/rules`, `PATCH/DELETE /screentime/rules/{id}` —
  rule CRUD, synced across devices.
- `POST /screentime/usage/android` — daily batch upload of per-app minutes.
- `POST /screentime/usage/ios-events` — threshold-event upload.
- `GET /screentime/usage?range=` — dashboard data (richer on Android, event
  timeline on iOS).

## Client structure

- `src/app/digital-health/` — dashboard (home), rule-builder,
  ios-report (hosts the `DeviceActivityReport` extension view),
  android-usage-charts.
- `src/modules/digital_health/` — rule sync logic, native module bridges
  (`ios/` and `android/` config-plugin-backed native code for the respective
  frameworks), local enforcement state.
- Native code here is substantial enough that this module should have its own
  Expo config plugin(s) rather than relying on managed-workflow defaults —
  confirm current patterns against the versioned Expo v57 docs (per
  AGENTS.md) before implementation, since config plugin APIs are an area
  Expo revises across versions.

## Error handling

- iOS entitlement not yet approved / rejected: app should degrade gracefully
  to "rule configuration only, enforcement disabled" rather than crashing, so
  development/testing isn't blocked on Apple's review process.
- Android Accessibility Service disabled by the user (OS may prompt to
  disable unused accessibility services periodically): detect this state and
  re-prompt the user to re-enable, since silent enforcement failure would be
  confusing ("why didn't it block Instagram this morning").

## Testing

- Backend contract tests: rule CRUD, ownership, usage upload validation.
- Manual QA on real devices only (blocking/accessibility behavior cannot be
  meaningfully tested in a simulator): verify a schedule actually shields the
  app on iOS, and the overlay actually appears on Android, for each rule type
  (schedule-based and limit-based).

## Open assumptions to confirm

- This module ships last in the sequence (per the Platform spec) since it's
  the most native-code-heavy and carries App Store review risk on the Family
  Controls entitlement — confirm you're fine with that risk landing at the
  end rather than earlier.
- Given the entitlement/review lead time, you may want to submit the Apple
  Family Controls entitlement request early (in parallel with building
  earlier modules) rather than waiting until this module starts, since
  approval isn't instant.
