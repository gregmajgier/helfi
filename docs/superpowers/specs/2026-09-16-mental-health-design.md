# Mental Health — Design Spec

Status: Draft, approved in chat 2026-09-16
Depends on: [Platform Architecture](2026-09-16-platform-architecture-design.md)

## Purpose

Lightweight daily mood check-ins and journaling, giving users a simple habit
loop (similar to apps like Daylio) rather than a clinical tool.

## Scope

- Daily mood check-in: quick mood rating (e.g. 1-5 scale or emoji set) plus
  optional tags (e.g. "stressed", "tired", "social") and a free-text note.
- Journaling: longer free-text entries, independent of the quick check-in.
- History view: mood trend over time (simple line/calendar heatmap), list of
  journal entries.
- Guided prompts: a small rotating set of reflective prompts to reduce
  blank-page friction when journaling (static content shipped with the app,
  not AI-generated in this phase).

## Out of scope (this phase)

- AI-generated journal prompts or sentiment analysis on entries.
- Guided breathing/meditation audio/video content.
- Any crisis-detection or clinical escalation logic — this is a self-tracking
  tool, not a mental health service; avoid implying otherwise in copy.

## Data model

**`mood_entries` container** (per-user, partitioned by `/user_id`):
```
{ id, user_id, logged_at, mood_score: 1-5, tags: string[],
  note?, created_at, updated_at }
```

**`journal_entries` container** (per-user, partitioned by `/user_id`):
```
{ id, user_id, written_at, prompt?, body, created_at, updated_at }
```

## API (`/mood` router)

- `GET/POST /mood/entries` — quick check-ins, filterable by date range.
- `PATCH/DELETE /mood/entries/{id}`.
- `GET/POST /mood/journal` — journal entries.
- `PATCH/DELETE /mood/journal/{id}`.
- `GET /mood/prompts` — returns a prompt for today (rotates through a static
  list server-side so it's consistent across the user's devices).

## Client structure

- `src/app/mental-health/` — check-in (home), journal-entry, history
  (trend + calendar view).
- `src/modules/mental_health/` — mood selector component, trend chart, static
  prompts list (or fetched from `/mood/prompts` if you'd rather manage them
  server-side without an app update).

## Error handling

- All writes are simple, low-stakes text/number entries — standard optimistic
  local save + background sync via the platform's write queue is sufficient;
  no special handling beyond that needed.

## Testing

- Backend contract tests: entry CRUD, ownership checks, date-range filtering.
- Manual QA: check-in flow, journal flow, trend view rendering with sparse
  and dense data (e.g. one entry vs. 90 days of entries).

## Open assumptions to confirm

- Mood scale is 1-5 with tags, matching common mood-tracker conventions —
  flag if you want a different scale or a mood-wheel style picker instead.
- Prompts are static content shipped/managed by us, not AI-generated — keeps
  this module free of any AI API dependency, unlike the meal tracker.
