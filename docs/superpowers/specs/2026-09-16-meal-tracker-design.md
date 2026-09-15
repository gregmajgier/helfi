# Meal & Calorie Tracker — Design Spec

Status: Draft, approved in chat 2026-09-16
Depends on: [Platform Architecture](2026-09-16-platform-architecture-design.md)

## Purpose

A Yazio-style meal and calorie tracker: a searchable food/product database,
custom foods and recipes, and a daily diary — with photo-AI estimation as one
of several ways to log a meal, not the only one. Extends the existing
`calorie_camera` stub rather than replacing it.

## Scope

- Global food/product database, searchable by name, with barcode lookup.
- Custom foods and recipes (combinations of foods) created by the user.
- Daily diary: entries grouped into breakfast/lunch/dinner/snack, with running
  totals against daily calorie/macro goals.
- Logging paths, all producing the same `meal_entry` record: database search,
  barcode scan, custom food/recipe, quick-add (raw calories/macros, no food
  link), and the existing photo-AI estimate flow.
- Editable AI estimates: photo → AI returns a candidate estimate → user
  confirms or edits before it's saved, never saved silently.

## Out of scope (this phase)

- Social features (sharing meals, following other users).
- Meal planning / grocery lists.
- Restaurant menu database (rely on generic product database + custom foods
  for now).

## Data model

**`foods` container** (global, partitioned by `barcode` or a generated key for
non-barcode items):
```
{ id, barcode?, name, brand?, serving_size, serving_unit,
  calories_per_serving, protein_g, carbs_g, fat_g, source: "off"|"user",
  created_by_user_id? }
```
Seeded from Open Food Facts (assumption — see Platform spec's open questions;
swap provider here if you'd rather use Edamam/USDA FDC/Nutritionix). Sync
strategy: on first search miss, query the provider's API live, cache the
result into `foods` so subsequent lookups are local; no full bulk import
upfront.

**`meal_entries` container** (per-user, partitioned by `/user_id`):
```
{ id, user_id, logged_at, meal_slot: "breakfast"|"lunch"|"dinner"|"snack",
  source: "search"|"barcode"|"custom"|"quick_add"|"photo_ai",
  food_id?, custom_food?, photo_url?, ai_estimate?,
  calories, protein_g, carbs_g, fat_g, created_at, updated_at }
```

**`recipes` container** (per-user): a named list of `{food_id, quantity}`
plus computed totals, logged as a single `meal_entry` when added to the diary.

## API (`/meals` router)

- `GET /meals/foods/search?q=` — search global + user's custom foods.
- `GET /meals/foods/barcode/{code}` — barcode lookup, live-fetches and caches
  from the provider on miss.
- `POST /meals/foods/custom` — create a custom food.
- `POST /meals/recipes` / `GET /meals/recipes` — manage recipes.
- `POST /meals/entries` — log a diary entry (any source).
- `GET /meals/entries?date=` — diary for a given day.
- `PATCH /meals/entries/{id}` / `DELETE /meals/entries/{id}` — edit/remove.
- `POST /meals/photo-estimate` — upload a photo, returns an AI estimate
  (calories/macros + confidence) that the client shows on a confirm screen
  before it becomes a `meal_entries` write; this endpoint does not write to
  the diary itself.

## Client structure

- `src/app/meal-tracker/` — replaces/extends `calorie-ai-tools` routes:
  diary (home), add-entry (search/barcode/quick-add tabs), camera (existing),
  confirm-estimate, food-detail, recipe-builder.
- `src/modules/meal_tracker/` — diary state, food search, entry form, and the
  existing `CalorieCamera` component moved in as one entry path among several.

## Error handling

- Barcode/search miss on the external provider: surfaces "not found, add it
  manually" rather than a hard error, funneling into the custom-food flow.
- Photo AI estimate failures (bad photo, low confidence): still let the user
  proceed to a manual entry pre-filled with whatever partial guess exists,
  never a dead end.

## Testing

- Backend contract tests: search/barcode caching behavior, entry CRUD,
  ownership checks, custom food creation.
- Manual QA: log via each of the five paths end-to-end before release.

## Open assumptions to confirm

- Open Food Facts as the seed/live-lookup provider (free, no API key, but
  data quality varies by region/product).
- Daily goals (calorie/macro targets) are assumed user-set manually in this
  phase — no calculated goal (e.g. from weight/activity/TDEE) yet; flag if
  that should be in scope now vs. a later module.
