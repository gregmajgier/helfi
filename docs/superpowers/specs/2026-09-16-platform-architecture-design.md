# Platform Architecture — Design Spec

Status: Draft, approved in chat 2026-09-16
Owner: gregmajgier@gmail.com

## Purpose

This app combines four tracking domains — meals/nutrition, training, mental
health, and digital wellbeing — into one product, released module by module so
each can be marketed independently on TikTok/Instagram as it ships. This spec
defines the shared platform (auth, data, client shell, API conventions) that
every module builds on. Each module has its own spec:

- [Meal & Calorie Tracker](2026-09-16-meal-tracker-design.md)
- [Training Tracker](2026-09-16-training-tracker-design.md)
- [Mental Health](2026-09-16-mental-health-design.md)
- [Digital Health](2026-09-16-digital-health-design.md)

## Constraints that shaped this design

- **No Expo Go.** Digital Health's native screen-time/blocking APIs
  (iOS `FamilyControls`/`DeviceActivity`/`ManagedSettings`, Android
  Accessibility Service) require custom native modules, which only run in an
  EAS-built dev client / production build, never Expo Go. This applies to the
  whole app, not just that module, so it's a platform-level decision.
- **Cosmos DB is never called directly from the client.** All data access goes
  through the backend API so credentials and cross-user access rules stay
  server-side.
- Per AGENTS.md: Expo has changed significantly. Before writing any client
  code (especially native config plugins), read the versioned docs at
  https://docs.expo.dev/versions/v57.0.0/ rather than relying on older
  training knowledge.

## Architecture

```
┌─────────────────────────────┐
│ Expo app (EAS dev client)   │
│  src/app/<module>/  (routes)│
│  src/modules/<module>/      │
│  src/lib/api-client, auth   │
└──────────────┬──────────────┘
               │ HTTPS, JWT bearer
┌──────────────▼──────────────┐
│ FastAPI app (Azure Container│
│ Apps)                       │
│  /auth  /meals  /workouts   │
│  /mood  /screentime         │
└──────────────┬──────────────┘
               │ Cosmos SDK
┌──────────────▼──────────────┐
│ Azure Cosmos DB              │
│  containers: users, foods,   │
│  meal_entries, workouts,     │
│  mood_entries, screentime_*  │
└───────────────────────────────┘
```

Each module owns its own FastAPI router and Cosmos container(s). Modules do
not call each other's containers directly — if a future module needs another
module's data (e.g. a "daily summary" screen combining meals + mood), it goes
through that module's API, not its container.

## Auth

FastAPI is the single source of truth for identity:

- **Email/password**: FastAPI hashes (bcrypt/argon2) and stores credentials in
  the `users` container, issues access + refresh JWTs.
- **OAuth (Apple, Google)**: client performs the native sign-in, sends the
  provider's ID token to `/auth/oauth/{provider}`, FastAPI verifies it against
  the provider's public keys, upserts a `users` record, and issues its own
  JWTs — same shape as the password flow.
- Client only ever stores and sends **our** JWTs (short-lived access token +
  longer-lived refresh token, refreshed via `/auth/refresh`). This keeps every
  module's auth handling identical regardless of how the user originally
  signed in.

## Data model conventions

- Every per-user container is partitioned on `/user_id`.
- Every document has `id`, `user_id`, `created_at`, `updated_at` (ISO 8601
  UTC).
- Global reference data (e.g. the food product database) lives in its own
  container, partitioned by a natural key (e.g. barcode), not `user_id`.

## Client structure

Extends the pattern already started with `calorie_camera`:

- `src/app/<module>/` — expo-router routes (screens, navigation).
- `src/modules/<module>/` — feature logic, components, hooks local to that
  module.
- `src/lib/` — cross-module shared code: API client (attaches JWT, handles
  401 → refresh → retry), auth state, design system primitives, offline write
  queue.
- Home dashboard (`src/app/index.tsx`) becomes a hub linking to whichever
  modules are enabled/shipped, rather than redirecting straight to one module
  as it does today.

## Error handling & offline writes

- API errors return a consistent shape: `{ "error": { "code", "message" } }`.
  Client maps known codes to user-facing copy; unknown codes fall back to a
  generic retry message.
- Writes that matter to the user in the moment (logging a meal, a workout set,
  a mood check-in) go through a local write queue: optimistic local save,
  background sync, retry with exponential backoff on failure, so a dropped
  connection never loses a log entry.
- Reads are simple request/response with a short in-memory cache per screen;
  no offline read cache in this phase.

## Testing

- Backend: pytest contract tests per route (auth required, validation,
  happy path, ownership checks — user A can never read user B's documents).
- Client: no automated test suite in this phase, given the priority on
  shipping modules quickly for marketing; each module release gets manual QA
  against its spec's acceptance criteria before shipping. Revisit if module
  count/complexity makes manual QA too slow.

## Rollout sequencing

Recommended build order, each independently marketable:

1. Platform shell (auth, navigation, API client) — prerequisite, not marketed
   itself.
2. Meal & Calorie Tracker (extends existing stub).
3. Training Tracker.
4. Mental Health.
5. Digital Health (most native-code-heavy; benefits from the dev client
   infrastructure already being proven out by modules 2-4).

## Open assumptions to confirm

- Backend hosting: assumes a single Container App revision per environment
  (dev/prod), not a per-module deployment, since modules are small FastAPI
  routers, not separate services. Flag if you want per-module deployability.
- No admin/CMS tooling is in scope yet for managing the global food database
  or moderating content — assumed manual/scripted for now.
