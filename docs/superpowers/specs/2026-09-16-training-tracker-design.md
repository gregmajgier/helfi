# Training Tracker — Design Spec

Status: Draft, approved in chat 2026-09-16
Depends on: [Platform Architecture](2026-09-16-platform-architecture-design.md)

## Purpose

Log strength training, calisthenics, running, and cycling, with GPS routes for
cardio, plus import activities from Strava and other wearables/health apps so
users aren't forced to double-log.

## Scope

- Manual strength/calisthenics logging: exercises, sets, reps, weight (or
  bodyweight flag), rest, organized into a workout session.
- Exercise library: predefined common exercises + user-added custom ones.
- GPS-tracked cardio: start/pause/stop recording for running and cycling,
  route map, distance, pace/speed, elevation, duration.
- Session history with per-activity-type stats over time.
- **Integrations sub-module**: Strava OAuth2 connection to import (and
  optionally export) activities; architecture supports adding more providers
  (Apple Health, Google Fit/Health Connect, Garmin) as additional connectors
  without changing core logging.

## Out of scope (this phase)

- Workout program builder / periodization plans.
- Social features (kudos, following, leaderboards) — Strava already does this
  well; we just import the activity data.
- Live coaching cues during a GPS-tracked session.

## Architecture notes specific to this module

- GPS tracking needs foreground location during an active session and,
  ideally, background location so a run/ride keeps recording if the phone
  locks — this requires the `expo-location` background permission flow and
  platform-specific background modes; confirm at implementation time against
  the current Expo v57 docs (per AGENTS.md) since background location
  handling is an area Expo revises often.
- Route rendering needs a maps SDK (`react-native-maps` or Expo's maps
  module) — not yet in `package.json`, to be added when this module starts.
- **Integrations run server-side.** Strava tokens (OAuth access/refresh) are
  stored server-side per user; a background worker in the Container App polls
  Strava's API (or handles their webhook) and writes normalized `workouts`
  records, so the phone doesn't need to be open for an import to happen, and
  the diary/history UI reads one unified format regardless of source.

## Data model

**`workouts` container** (per-user, partitioned by `/user_id`):
```
{ id, user_id, type: "strength"|"calisthenics"|"running"|"cycling",
  source: "manual"|"strava"|"apple_health"|"google_fit",
  external_id?,           // dedupe key for imported activities
  started_at, duration_s,
  // strength/calisthenics:
  exercises?: [{ exercise_id, sets: [{reps, weight_kg?, bodyweight?}] }],
  // cardio:
  distance_m?, route_polyline?, avg_pace_s_per_km?, elevation_gain_m?,
  created_at, updated_at }
```

**`exercises` container** (global + user-custom, same pattern as `foods` in
the meal tracker): `{ id, name, category, is_bodyweight, created_by_user_id? }`.

**`integration_connections` container** (per-user): `{ id, user_id, provider,
access_token, refresh_token, expires_at, last_synced_at }` — tokens encrypted
at rest.

## API (`/workouts` router)

- `GET/POST /workouts` — list/create manual entries.
- `PATCH/DELETE /workouts/{id}`.
- `GET /workouts/exercises` — library search.
- `POST /workouts/exercises` — add a custom exercise.
- `POST /workouts/integrations/strava/connect` — OAuth callback handler.
- `DELETE /workouts/integrations/strava` — disconnect.
- `GET /workouts/live/start` / `POST /workouts/live/{id}/finish` — server
  records for an in-progress GPS session, so an interrupted app doesn't lose
  an in-progress activity (client also buffers points locally and reconciles
  on finish).

## Client structure

- `src/app/training-tracker/` — history (home), log-strength, log-cardio
  (live map + start/pause/stop), exercise-library, integrations-settings.
- `src/modules/training_tracker/` — session state machine (idle/recording/
  paused/finished), GPS point buffering, exercise/set form state.

## Error handling

- GPS signal loss mid-session: keep recording elapsed time/duration, mark the
  route as having a gap rather than failing the whole session.
- Strava sync failures (expired token, rate limit): surface a "reconnect
  Strava" prompt rather than silently dropping imports; retry transient
  failures with backoff in the background worker.

## Testing

- Backend contract tests: workout CRUD, ownership, Strava token
  refresh/expiry handling, dedupe on re-import (`external_id` uniqueness).
- Manual QA: full GPS session on-device (simulators don't exercise real GPS
  behavior), plus a real Strava account for the import flow.

## Open assumptions to confirm

- Strava is the first/reference integration; Apple Health & Google Fit are
  named as follow-ups in the same sub-module, not built in the first pass —
  confirm that sequencing is fine.
- Distances/weights stored metric (km, kg) with unit conversion at the
  display layer — flag if you want imperial as the stored unit instead.
