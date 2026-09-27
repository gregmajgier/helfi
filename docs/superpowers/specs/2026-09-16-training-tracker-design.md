# Training Tracker — Design Spec

Status: Draft, approved in chat 2026-09-16
Depends on: [Platform Architecture](2026-09-16-platform-architecture-design.md)

## Purpose

Log strength training, calisthenics, running, and cycling. Cardio (running/
cycling) is logged manually (distance, duration, pace) — the app does not do
its own GPS recording. Importing activities from Strava/Apple Health/etc. is
deferred to a later version (see Out of scope below); v1 is manual-only for
every activity type.

## Scope

- Manual strength/calisthenics logging: exercises, sets, reps, weight (or
  bodyweight flag), rest, organized into a workout session.
- Exercise library: predefined common exercises + user-added custom ones.
- Manual cardio logging: running/cycling entries with distance, duration,
  pace/speed, elevation gain (optional) — no in-app GPS recording or route
  map.
- Session history with per-activity-type stats over time.

## Out of scope (this phase)

- **Integrations sub-module (Strava, Apple Health, Google Fit/Health
  Connect, Garmin, etc.)** — deferred to a future version. v1 has no OAuth
  connections, background sync worker, or imported-activity dedupe; the
  `source`/`external_id` fields stay in the data model so this can be added
  later without a schema migration, but no integration code ships in v1.
  Users who want GPS-tracked runs/rides record them in Strava or their
  device's native health app for now, with manual re-entry into this app in
  the meantime.
- In-app GPS tracking (start/pause/stop recording, live route map,
  foreground/background location permissions).
- Workout program builder / periodization plans.
- Social features (kudos, following, leaderboards).
- Live coaching cues during a tracked session.

## Architecture notes specific to this module

- No location permissions or maps SDK are needed for this module since GPS
  recording is out of scope — cardio entries are manual only in v1.
- No server-side integration/background-worker infrastructure is needed in
  v1. When the integrations sub-module is built later, tokens would be
  stored server-side per user and a background worker in the Container App
  would poll the provider's API (or handle their webhook) to write
  normalized `workouts` records — noted here so the deferred design isn't
  lost, not as current-phase work.

## Data model

**`workouts` container** (per-user, partitioned by `/user_id`):
```
{ id, user_id, type: "strength"|"calisthenics"|"running"|"cycling",
  source: "manual",       // "strava"|"apple_health"|"google_fit" reserved for a future version
  external_id?,           // reserved: dedupe key for imported activities (unused in v1)
  started_at, duration_s,
  // strength/calisthenics:
  exercises?: [{ exercise_id, sets: [{reps, weight_kg?, bodyweight?}] }],
  // cardio:
  distance_m?, route_polyline?, avg_pace_s_per_km?, elevation_gain_m?,
  created_at, updated_at }
```

**`exercises` container** (global + user-custom, same pattern as `foods` in
the meal tracker): `{ id, name, category, is_bodyweight, created_by_user_id? }`.

Not built in v1: `integration_connections` container — add it when the
integrations sub-module is picked up.

## API (`/workouts` router)

- `GET/POST /workouts` — list/create manual entries.
- `PATCH/DELETE /workouts/{id}`.
- `GET /workouts/exercises` — library search.
- `POST /workouts/exercises` — add a custom exercise.

Not built in v1: `/workouts/integrations/*` (Strava connect/disconnect and
any other provider) — add when the integrations sub-module is picked up.

## Client structure

- `src/app/training-tracker/` — history (home), log-strength, log-cardio
  (manual entry form: distance/duration/pace), exercise-library.
- `src/modules/training_tracker/` — exercise/set form state, cardio entry
  form state.

Not built in v1: an `integrations-settings` screen — add alongside the
integrations sub-module.

## Error handling

- Standard validation errors on manual entry (missing required fields,
  negative distance/duration, etc.) — no integration-sync error handling is
  needed in v1.

## Testing

- Backend contract tests: workout CRUD, ownership.
- Manual QA: manual strength and cardio logging flows end-to-end.

## Open assumptions to confirm

- Distances/weights stored metric (km, kg) with unit conversion at the
  display layer — flag if you want imperial as the stored unit instead.
- When the integrations sub-module is picked up later, confirm Strava
  remains the first/reference provider, with Apple Health & Google Fit as
  follow-ups in the same sub-module.
