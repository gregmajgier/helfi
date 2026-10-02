# helf Rebrand, Onboarding & New Pillars Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand the app to "helf", build out the Mind (mental health) and Focus (digital health, rules-only) modules, ship a design system with a four-pillar color identity, and add a pre-signup onboarding flow that seeds real first-use data.

**Architecture:** Two new FastAPI routers (`/mood`, `/screentime`) follow the exact repository/router pattern already used by `workouts`/`meals` (Protocol interfaces in `db/base.py`, in-memory + Cosmos implementations, DI via `deps.py`). A new `src/lib/theme.ts` + `src/components/` primitives give every screen a shared four-color design language. A new pre-signup `src/app/onboarding/` stack collects goals and writes real data (a mood entry, a draft screen-time rule) once registration succeeds, via a small AsyncStorage-backed answer store that survives navigating between route groups.

**Tech Stack:** Expo ~57.0.21, expo-router, React Native 0.86.3, React 19.2.3, FastAPI + Cosmos DB (Azure) with an in-memory fallback, pytest (`asyncio_mode = auto`).

**Spec:** `docs/superpowers/specs/2026-10-02-helf-brand-onboarding-design.md`

## Global Constraints

- Match the exact SDK 57 APIs verified for this plan (Plus Jakarta Sans via `@expo-google-fonts/plus-jakarta-sans` + `useFonts`; `expo-notifications` daily trigger via `SchedulableTriggerInputTypes.DAILY`; `@react-native-async-storage/async-storage`) — install every new package with `npx expo install <pkg>`, never plain `npm install`, so Expo pins SDK-compatible versions.
- Cosmos DB is never called directly from the client — all data access goes through the FastAPI backend.
- Every per-user container is partitioned on `/user_id`; every document has `id`, `user_id`, `created_at`, `updated_at` (ISO 8601 UTC) — follow the existing `workouts`/`meal_entries` containers exactly for the new `mood_entries`, `journal_entries`, `screentime_rules` containers.
- API errors use the existing `{ "error": { "code", "message" } }` shape, already handled centrally by `apiFetch` — no new error-shape code needed.
- Client has no automated test suite, per the platform spec's existing decision — every client task ends with `npx tsc --noEmit` plus a manual verification script, not Jest/RNTL tests.
- Existing route folder names (`training-tracker`, `meal-tracker`) and API prefixes (`/mood`, `/screentime`) do not change. "Move/Fuel/Mind/Focus" are display names only, defined once in `src/lib/theme.ts`, never baked into file paths.
- Digital Health phase 1 ships ONLY rule CRUD — no usage endpoints, no native enforcement code, no scheduled time-windows. The dashboard screen must say "Enforcement coming soon" explicitly.
- `db_backend` defaults to `"memory"` in `backend/app/config.py` (unchanged) — the full pytest suite must keep running with zero Azure connectivity after every task.

## Review Focus

- A user force-quits mid-onboarding after the Mind check-in but before finishing registration — pending answers live in AsyncStorage (not React state), so they survive the restart and are never POSTed twice once registration completes.
- A returning user reinstalls the app — `onboarding_complete` lives in AsyncStorage and is wiped on uninstall, so they'd see onboarding again despite having a real account; the welcome screen's "Already have an account? Log in" link must stay reachable as the very first screen so this is never a dead end.
- `mood_score` or `daily_limit_minutes` submitted out of range (e.g. `mood_score` 0 or 6, `daily_limit_minutes` 0 or negative) must 422, not silently clamp or 500 — mirrors the existing `reps`/`duration_s` validators in `workouts/models.py`.
- Two users must never see each other's mood entries, journal entries, or screen-time rules — every new repo method takes `user_id`, and every new router test asserts 404 (not 403/500) when user B targets user A's record, exactly like `test_user_cannot_read_or_modify_another_users_workout`.
- The onboarding-to-data handoff (Mind check-in → real `POST /mood/entries`, Focus apps → real `POST /screentime/rules`) failing on a flaky network must not strand the user on an error screen post-registration — this is explicitly best-effort per the spec, and the register screen's manual verification step must prove the hub is still reached even if those two calls are mocked to fail.

---

## Task 1: Design tokens and font loading

**Files:**
- Create: `src/lib/theme.ts`
- Modify: `src/app/_layout.tsx`
- Package: `@expo-google-fonts/plus-jakarta-sans`, `expo-font`

**Interfaces:**
- Consumes: nothing new.
- Produces: `PillarKey`, `Pillar`, `PILLARS`, `PILLAR_ORDER`, `NEUTRALS`, `SPACING`, `FONT_FAMILY`, `pillarColor(pillar, mode)`, `useTheme()` from `src/lib/theme.ts` — consumed by every component and screen task from here on.

- [ ] **Step 1: Install the font packages**

```bash
npx expo install @expo-google-fonts/plus-jakarta-sans expo-font
```

- [ ] **Step 2: Write the design tokens**

`src/lib/theme.ts`:
```typescript
import { useColorScheme } from "react-native";

export type PillarKey = "move" | "fuel" | "mind" | "focus";

export type Pillar = {
  key: PillarKey;
  label: string;
  icon: string;
  light: string;
  dark: string;
};

export const PILLARS: Record<PillarKey, Pillar> = {
  move: { key: "move", label: "Move", icon: "🏃", light: "#E8623D", dark: "#FF8162" },
  fuel: { key: "fuel", label: "Fuel", icon: "🍎", light: "#7C9A5C", dark: "#9CBB7A" },
  mind: { key: "mind", label: "Mind", icon: "🧘", light: "#8B7FD1", dark: "#A79BEB" },
  focus: { key: "focus", label: "Focus", icon: "⏳", light: "#3E9A96", dark: "#5CC2BD" },
};

export const PILLAR_ORDER: PillarKey[] = ["move", "fuel", "mind", "focus"];

type NeutralPalette = {
  background: string;
  surface: string;
  textPrimary: string;
  textSecondary: string;
  border: string;
};

export type ThemeMode = "light" | "dark";

export const NEUTRALS: Record<ThemeMode, NeutralPalette> = {
  light: {
    background: "#FBF9F6",
    surface: "#FFFFFF",
    textPrimary: "#22262B",
    textSecondary: "#6B7177",
    border: "#E6E2DC",
  },
  dark: {
    background: "#16181C",
    surface: "#1F2227",
    textPrimary: "#F4F2EE",
    textSecondary: "#9BA1A8",
    border: "#2B2F35",
  },
};

export const SPACING = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 } as const;

export const FONT_FAMILY = {
  regular: "PlusJakartaSans_400Regular",
  medium: "PlusJakartaSans_500Medium",
  semibold: "PlusJakartaSans_600SemiBold",
  bold: "PlusJakartaSans_700Bold",
  extrabold: "PlusJakartaSans_800ExtraBold",
} as const;

export function pillarColor(pillar: PillarKey, mode: ThemeMode): string {
  return PILLARS[pillar][mode];
}

export function useTheme() {
  const scheme = useColorScheme();
  const mode: ThemeMode = scheme === "dark" ? "dark" : "light";
  return {
    mode,
    colors: NEUTRALS[mode],
    pillars: PILLARS,
    pillarOrder: PILLAR_ORDER,
    spacing: SPACING,
    font: FONT_FAMILY,
  };
}
```

- [ ] **Step 3: Load the font in the root layout**

Replace `src/app/_layout.tsx`:
```tsx
import {
  PlusJakartaSans_400Regular,
  PlusJakartaSans_500Medium,
  PlusJakartaSans_600SemiBold,
  PlusJakartaSans_700Bold,
  PlusJakartaSans_800ExtraBold,
  useFonts,
} from "@expo-google-fonts/plus-jakarta-sans";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { useEffect } from "react";
import { View } from "react-native";

import { AuthProvider } from "@/lib/auth-context";

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    PlusJakartaSans_400Regular,
    PlusJakartaSans_500Medium,
    PlusJakartaSans_600SemiBold,
    PlusJakartaSans_700Bold,
    PlusJakartaSans_800ExtraBold,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError]);

  if (!fontsLoaded && !fontError) {
    return null;
  }

  return (
    <AuthProvider>
      <View style={{ flex: 1 }}>
        <Stack screenOptions={{ headerShown: false }} />
      </View>
    </AuthProvider>
  );
}
```

- [ ] **Step 4: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 5: Manual verification**

```bash
npx expo start
```
Confirm the app still boots to the login screen with no stuck splash screen and no console error about a missing font family (nothing visually uses the font yet — this just proves font loading doesn't break boot).

- [ ] **Step 6: Commit**

```bash
git add src/lib/theme.ts src/app/_layout.tsx package.json package-lock.json
git commit -m "$(cat <<'EOF'
Add design tokens and load Plus Jakarta Sans font

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Shared UI primitives

**Files:**
- Create: `src/components/ScreenContainer.tsx`, `src/components/Button.tsx`, `src/components/Card.tsx`, `src/components/PillarTile.tsx`, `src/components/Chip.tsx`, `src/components/ProgressDots.tsx`, `src/components/index.ts`

**Interfaces:**
- Consumes: `useTheme`, `PillarKey` (`src/lib/theme.ts`, Task 1).
- Produces: `ScreenContainer`, `Button`, `Card`, `PillarTile`, `Chip`, `ProgressDots` from `@/components` — consumed by every screen task from Task 7 onward.

- [ ] **Step 1: `ScreenContainer`**

`src/components/ScreenContainer.tsx`:
```tsx
import type { ReactNode } from "react";
import { SafeAreaView, View, type ViewStyle } from "react-native";

import { useTheme } from "@/lib/theme";

export function ScreenContainer({
  children,
  style,
}: {
  children: ReactNode;
  style?: ViewStyle;
}) {
  const { colors, spacing } = useTheme();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
      <View style={[{ flex: 1, padding: spacing.lg, gap: spacing.md }, style]}>{children}</View>
    </SafeAreaView>
  );
}
```

- [ ] **Step 2: `Button`**

`src/components/Button.tsx`:
```tsx
import { Pressable, StyleSheet, Text } from "react-native";

import { useTheme } from "@/lib/theme";

type ButtonVariant = "primary" | "secondary" | "text";

export function Button({
  title,
  onPress,
  variant = "primary",
  color,
  disabled = false,
}: {
  title: string;
  onPress: () => void;
  variant?: ButtonVariant;
  color?: string;
  disabled?: boolean;
}) {
  const { colors, font, spacing } = useTheme();
  const accent = color ?? colors.textPrimary;

  const backgroundColor =
    variant === "primary" ? accent : variant === "secondary" ? colors.surface : "transparent";
  const textColor = variant === "primary" ? "#FFFFFF" : accent;

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.base,
        {
          backgroundColor,
          borderColor: accent,
          borderWidth: variant === "secondary" ? 1.5 : 0,
          paddingVertical: spacing.md,
          paddingHorizontal: spacing.lg,
          opacity: disabled ? 0.5 : pressed ? 0.8 : 1,
        },
      ]}
    >
      <Text style={{ color: textColor, fontFamily: font.semibold, fontSize: 16, textAlign: "center" }}>
        {title}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: { borderRadius: 14, alignItems: "center", justifyContent: "center" },
});
```

- [ ] **Step 3: `Card`**

`src/components/Card.tsx`:
```tsx
import type { ReactNode } from "react";
import { StyleSheet, View, type ViewStyle } from "react-native";

import { useTheme } from "@/lib/theme";

export function Card({ children, style }: { children: ReactNode; style?: ViewStyle }) {
  const { colors, spacing } = useTheme();
  return (
    <View
      style={[
        styles.base,
        { backgroundColor: colors.surface, borderColor: colors.border, padding: spacing.lg },
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  base: { borderRadius: 18, borderWidth: 1, gap: 8 },
});
```

- [ ] **Step 4: `PillarTile`**

`src/components/PillarTile.tsx`:
```tsx
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useTheme, type PillarKey } from "@/lib/theme";

export function PillarTile({
  pillar,
  status,
  onPress,
}: {
  pillar: PillarKey;
  status: string;
  onPress: () => void;
}) {
  const { colors, mode, pillars, font, spacing } = useTheme();
  const info = pillars[pillar];
  const accent = info[mode];

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        {
          backgroundColor: colors.surface,
          borderColor: accent,
          padding: spacing.lg,
          opacity: pressed ? 0.85 : 1,
        },
      ]}
    >
      <View style={[styles.iconBadge, { backgroundColor: accent }]}>
        <Text style={styles.icon}>{info.icon}</Text>
      </View>
      <Text style={{ fontFamily: font.bold, fontSize: 18, color: colors.textPrimary }}>{info.label}</Text>
      <Text style={{ fontFamily: font.regular, fontSize: 13, color: colors.textSecondary }}>{status}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: { borderRadius: 20, borderWidth: 2, gap: 6, flexBasis: "47%", flexGrow: 1 },
  iconBadge: { width: 40, height: 40, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  icon: { fontSize: 20 },
});
```

- [ ] **Step 5: `Chip`**

`src/components/Chip.tsx`:
```tsx
import { Pressable, StyleSheet, Text } from "react-native";

import { useTheme } from "@/lib/theme";

export function Chip({
  label,
  selected,
  onPress,
  color,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
  color?: string;
}) {
  const { colors, font, spacing } = useTheme();
  const accent = color ?? colors.textPrimary;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        {
          backgroundColor: selected ? accent : colors.surface,
          borderColor: accent,
          paddingVertical: spacing.sm,
          paddingHorizontal: spacing.lg,
          opacity: pressed ? 0.85 : 1,
        },
      ]}
    >
      <Text style={{ color: selected ? "#FFFFFF" : accent, fontFamily: font.medium, fontSize: 14 }}>
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: { borderRadius: 999, borderWidth: 1.5 },
});
```

- [ ] **Step 6: `ProgressDots`**

`src/components/ProgressDots.tsx`:
```tsx
import { StyleSheet, View } from "react-native";

import { useTheme } from "@/lib/theme";

export function ProgressDots({
  count,
  activeIndex,
  color,
}: {
  count: number;
  activeIndex: number;
  color?: string;
}) {
  const { colors } = useTheme();
  const accent = color ?? colors.textPrimary;

  return (
    <View style={styles.row}>
      {Array.from({ length: count }, (_, i) => (
        <View
          key={i}
          style={[
            styles.dot,
            { backgroundColor: i === activeIndex ? accent : colors.border, width: i === activeIndex ? 20 : 8 },
          ]}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: 6, justifyContent: "center" },
  dot: { height: 8, borderRadius: 4 },
});
```

- [ ] **Step 7: Barrel export**

`src/components/index.ts`:
```typescript
export { Button } from "./Button";
export { Card } from "./Card";
export { Chip } from "./Chip";
export { PillarTile } from "./PillarTile";
export { ProgressDots } from "./ProgressDots";
export { ScreenContainer } from "./ScreenContainer";
```

- [ ] **Step 8: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors. (Visual verification of these primitives happens naturally once a screen consumes them, starting Task 7.)

- [ ] **Step 9: Commit**

```bash
git add src/components
git commit -m "$(cat <<'EOF'
Add shared UI primitives for the four-pillar design system

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Mood & journal repository interfaces, in-memory implementations, and dependency wiring

**Files:**
- Modify: `backend/app/db/base.py`, `backend/app/db/memory.py`, `backend/app/deps.py`, `backend/tests/conftest.py`, `backend/tests/test_memory_repositories.py`

**Interfaces:**
- Consumes: nothing new (mirrors the existing `InMemoryWorkoutRepository` pattern).
- Produces: `MoodEntryRepository`, `JournalEntryRepository` Protocols from `app.db.base`; `InMemoryMoodEntryRepository`, `InMemoryJournalEntryRepository` from `app.db.memory`; `get_mood_entry_repo()`, `get_journal_entry_repo()` from `app.deps` — used by Task 4 onward.

- [ ] **Step 1: Write the failing tests**

Replace the `from app.db.memory import (...)` line at the top of `backend/tests/test_memory_repositories.py` with:
```python
from app.db.memory import (
    SEED_EXERCISES,
    SEED_FOODS,
    InMemoryExerciseRepository,
    InMemoryFoodRepository,
    InMemoryJournalEntryRepository,
    InMemoryMealEntryRepository,
    InMemoryMoodEntryRepository,
    InMemoryUserRepository,
    InMemoryWorkoutRepository,
)
```

Append to `backend/tests/test_memory_repositories.py`:
```python
async def test_mood_entry_repository_crud_scoped_by_user():
    repo = InMemoryMoodEntryRepository()

    entry = await repo.create(
        {"user_id": "user-1", "logged_at": "2026-10-01T08:00:00+00:00", "mood_score": 4, "tags": ["calm"]}
    )

    assert entry["id"]
    mine = await repo.list_for_user("user-1")
    assert [e["id"] for e in mine] == [entry["id"]]
    assert await repo.list_for_user("user-2") == []

    updated = await repo.update("user-1", entry["id"], {"mood_score": 5})
    assert updated["mood_score"] == 5
    assert await repo.update("user-2", entry["id"], {"mood_score": 1}) is None

    assert await repo.delete("user-2", entry["id"]) is False
    assert await repo.delete("user-1", entry["id"]) is True
    assert await repo.get("user-1", entry["id"]) is None


async def test_mood_entry_repository_list_for_user_filters_by_date_range():
    repo = InMemoryMoodEntryRepository()
    await repo.create({"user_id": "user-1", "logged_at": "2026-10-01T08:00:00+00:00", "mood_score": 3, "tags": []})
    await repo.create({"user_id": "user-1", "logged_at": "2026-10-05T08:00:00+00:00", "mood_score": 5, "tags": []})

    from datetime import date as date_cls

    in_range = await repo.list_for_user("user-1", start=date_cls(2026, 10, 2), end=date_cls(2026, 10, 10))

    assert [e["mood_score"] for e in in_range] == [5]


async def test_journal_entry_repository_crud_scoped_by_user():
    repo = InMemoryJournalEntryRepository()

    entry = await repo.create(
        {"user_id": "user-1", "written_at": "2026-10-01T08:00:00+00:00", "body": "Today was fine."}
    )

    assert entry["id"]
    mine = await repo.list_for_user("user-1")
    assert [e["id"] for e in mine] == [entry["id"]]
    assert await repo.list_for_user("user-2") == []

    updated = await repo.update("user-1", entry["id"], {"body": "Updated."})
    assert updated["body"] == "Updated."
    assert await repo.update("user-2", entry["id"], {"body": "nope"}) is None

    assert await repo.delete("user-2", entry["id"]) is False
    assert await repo.delete("user-1", entry["id"]) is True
    assert await repo.get("user-1", entry["id"]) is None
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_memory_repositories.py -v
```
Expected: FAIL with `ImportError: cannot import name 'InMemoryMoodEntryRepository'`.

- [ ] **Step 3: Implement**

Append to `backend/app/db/base.py`:
```python
class MoodEntryRepository(Protocol):
    async def create(self, entry: dict) -> dict: ...
    async def list_for_user(
        self, user_id: str, start: Optional[date] = None, end: Optional[date] = None
    ) -> list[dict]: ...
    async def get(self, user_id: str, entry_id: str) -> Optional[dict]: ...
    async def update(self, user_id: str, entry_id: str, updates: dict) -> Optional[dict]: ...
    async def delete(self, user_id: str, entry_id: str) -> bool: ...


class JournalEntryRepository(Protocol):
    async def create(self, entry: dict) -> dict: ...
    async def list_for_user(self, user_id: str) -> list[dict]: ...
    async def get(self, user_id: str, entry_id: str) -> Optional[dict]: ...
    async def update(self, user_id: str, entry_id: str, updates: dict) -> Optional[dict]: ...
    async def delete(self, user_id: str, entry_id: str) -> bool: ...
```

Append to `backend/app/db/memory.py`:
```python
class InMemoryMoodEntryRepository:
    def __init__(self):
        self._entries: dict[str, dict] = {}

    async def create(self, entry: dict) -> dict:
        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {**entry, "id": entry_id, "created_at": now, "updated_at": now}
        self._entries[entry_id] = record
        return record

    async def list_for_user(
        self, user_id: str, start: Optional[date] = None, end: Optional[date] = None
    ) -> list[dict]:
        results = [e for e in self._entries.values() if e["user_id"] == user_id]
        if start is not None:
            results = [e for e in results if e["logged_at"] >= start.isoformat()]
        if end is not None:
            results = [e for e in results if e["logged_at"] <= f"{end.isoformat()}T23:59:59"]
        return sorted(results, key=lambda e: e["logged_at"], reverse=True)

    async def get(self, user_id: str, entry_id: str) -> Optional[dict]:
        entry = self._entries.get(entry_id)
        return entry if entry and entry["user_id"] == user_id else None

    async def update(self, user_id: str, entry_id: str, updates: dict) -> Optional[dict]:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return None
        entry.update(updates)
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        return entry

    async def delete(self, user_id: str, entry_id: str) -> bool:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return False
        del self._entries[entry["id"]]
        return True


class InMemoryJournalEntryRepository:
    def __init__(self):
        self._entries: dict[str, dict] = {}

    async def create(self, entry: dict) -> dict:
        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {**entry, "id": entry_id, "created_at": now, "updated_at": now}
        self._entries[entry_id] = record
        return record

    async def list_for_user(self, user_id: str) -> list[dict]:
        results = [e for e in self._entries.values() if e["user_id"] == user_id]
        return sorted(results, key=lambda e: e["written_at"], reverse=True)

    async def get(self, user_id: str, entry_id: str) -> Optional[dict]:
        entry = self._entries.get(entry_id)
        return entry if entry and entry["user_id"] == user_id else None

    async def update(self, user_id: str, entry_id: str, updates: dict) -> Optional[dict]:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return None
        entry.update(updates)
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        return entry

    async def delete(self, user_id: str, entry_id: str) -> bool:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return False
        del self._entries[entry["id"]]
        return True
```

In `backend/app/deps.py`, add `InMemoryJournalEntryRepository, InMemoryMoodEntryRepository` to the existing `from .db.memory import (...)` line, add below the existing `_exercise_repo = ...` line:
```python
_memory_mood_entry_repo = InMemoryMoodEntryRepository()
_memory_journal_entry_repo = InMemoryJournalEntryRepository()
```
and add below the existing `get_exercise_repo` function:
```python
def get_mood_entry_repo():
    return _memory_mood_entry_repo


def get_journal_entry_repo():
    return _memory_journal_entry_repo
```

In `backend/tests/conftest.py`, add `InMemoryJournalEntryRepository, InMemoryMoodEntryRepository` to the `from app.db.memory import (...)` line, add inside the `client` fixture below `exercise_repo = InMemoryExerciseRepository(SEED_EXERCISES)`:
```python
    mood_entry_repo = InMemoryMoodEntryRepository()
    journal_entry_repo = InMemoryJournalEntryRepository()
```
and add below the existing `app.dependency_overrides[deps.get_exercise_repo] = ...` line:
```python
    app.dependency_overrides[deps.get_mood_entry_repo] = lambda: mood_entry_repo
    app.dependency_overrides[deps.get_journal_entry_repo] = lambda: journal_entry_repo
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/base.py backend/app/db/memory.py backend/app/deps.py backend/tests/conftest.py backend/tests/test_memory_repositories.py
git commit -m "$(cat <<'EOF'
Add mood and journal repository interfaces with in-memory implementations

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Mood & journal endpoints (CRUD, validation, ownership, daily prompt)

**Files:**
- Create: `backend/app/mood/__init__.py`, `backend/app/mood/models.py`, `backend/app/mood/prompts.py`, `backend/app/mood/router.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_mood_router.py` (new)

**Interfaces:**
- Consumes: `get_current_user_id`, `get_mood_entry_repo`, `get_journal_entry_repo` (Task 3).
- Produces: `GET/POST /mood/entries`, `PATCH/DELETE /mood/entries/{id}`, `GET/POST /mood/journal`, `PATCH/DELETE /mood/journal/{id}`, `GET /mood/prompts`; `MoodEntryCreate`, `MoodEntryUpdate`, `MoodEntryOut`, `JournalEntryCreate`, `JournalEntryUpdate`, `JournalEntryOut` — consumed by the client tasks (Task 6).

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_mood_router.py`:
```python
MOOD_PAYLOAD = {"logged_at": "2026-10-01T08:00:00Z", "mood_score": 4, "tags": ["calm"], "note": "good day"}


def test_create_and_list_mood_entry(client, auth_headers):
    headers = auth_headers()

    create = client.post("/mood/entries", json=MOOD_PAYLOAD, headers=headers)
    assert create.status_code == 201
    assert create.json()["mood_score"] == 4

    listing = client.get("/mood/entries", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_mood_entry_score_out_of_range_is_rejected(client, auth_headers):
    headers = auth_headers()

    too_low = client.post("/mood/entries", json={**MOOD_PAYLOAD, "mood_score": 0}, headers=headers)
    too_high = client.post("/mood/entries", json={**MOOD_PAYLOAD, "mood_score": 6}, headers=headers)

    assert too_low.status_code == 422
    assert too_high.status_code == 422


def test_update_and_delete_own_mood_entry(client, auth_headers):
    headers = auth_headers()
    entry_id = client.post("/mood/entries", json=MOOD_PAYLOAD, headers=headers).json()["id"]

    update = client.patch(f"/mood/entries/{entry_id}", json={"mood_score": 2}, headers=headers)
    assert update.status_code == 200
    assert update.json()["mood_score"] == 2

    delete = client.delete(f"/mood/entries/{entry_id}", headers=headers)
    assert delete.status_code == 204

    listing = client.get("/mood/entries", headers=headers)
    assert listing.json() == []


def test_user_cannot_read_or_modify_another_users_mood_entry(client, auth_headers):
    headers_a = auth_headers(email="mood-owner@example.com")
    headers_b = auth_headers(email="mood-intruder@example.com")
    entry_id = client.post("/mood/entries", json=MOOD_PAYLOAD, headers=headers_a).json()["id"]

    update = client.patch(f"/mood/entries/{entry_id}", json={"mood_score": 1}, headers=headers_b)
    assert update.status_code == 404

    delete = client.delete(f"/mood/entries/{entry_id}", headers=headers_b)
    assert delete.status_code == 404


def test_mood_entries_require_auth(client):
    response = client.get("/mood/entries")

    assert response.status_code == 403


JOURNAL_PAYLOAD = {"written_at": "2026-10-01T08:00:00Z", "prompt": "How was today?", "body": "It was fine."}


def test_create_and_list_journal_entry(client, auth_headers):
    headers = auth_headers()

    create = client.post("/mood/journal", json=JOURNAL_PAYLOAD, headers=headers)
    assert create.status_code == 201

    listing = client.get("/mood/journal", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_journal_entry_with_empty_body_is_rejected(client, auth_headers):
    headers = auth_headers()
    payload = {**JOURNAL_PAYLOAD, "body": "   "}

    response = client.post("/mood/journal", json=payload, headers=headers)

    assert response.status_code == 422


def test_update_and_delete_own_journal_entry(client, auth_headers):
    headers = auth_headers()
    entry_id = client.post("/mood/journal", json=JOURNAL_PAYLOAD, headers=headers).json()["id"]

    update = client.patch(f"/mood/journal/{entry_id}", json={"body": "Changed my mind."}, headers=headers)
    assert update.status_code == 200
    assert update.json()["body"] == "Changed my mind."

    delete = client.delete(f"/mood/journal/{entry_id}", headers=headers)
    assert delete.status_code == 204


def test_user_cannot_read_or_modify_another_users_journal_entry(client, auth_headers):
    headers_a = auth_headers(email="journal-owner@example.com")
    headers_b = auth_headers(email="journal-intruder@example.com")
    entry_id = client.post("/mood/journal", json=JOURNAL_PAYLOAD, headers=headers_a).json()["id"]

    update = client.patch(f"/mood/journal/{entry_id}", json={"body": "nope"}, headers=headers_b)
    assert update.status_code == 404


def test_get_todays_prompt_returns_consistent_result(client, auth_headers):
    headers = auth_headers()

    first = client.get("/mood/prompts", headers=headers)
    second = client.get("/mood/prompts", headers=headers)

    assert first.status_code == 200
    assert first.json()["prompt"]
    assert first.json()["prompt"] == second.json()["prompt"]
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_mood_router.py -v
```
Expected: FAIL — `/mood` routes don't exist yet (404s / connection errors against an unregistered router).

- [ ] **Step 3: Implement**

`backend/app/mood/__init__.py`: empty file.

`backend/app/mood/models.py`:
```python
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class MoodEntryCreate(BaseModel):
    logged_at: datetime
    mood_score: int
    tags: list[str] = []
    note: Optional[str] = None

    @field_validator("mood_score")
    @classmethod
    def score_in_range(cls, value: int) -> int:
        if not 1 <= value <= 5:
            raise ValueError("mood_score must be between 1 and 5")
        return value


class MoodEntryUpdate(BaseModel):
    mood_score: Optional[int] = None
    tags: Optional[list[str]] = None
    note: Optional[str] = None

    @field_validator("mood_score")
    @classmethod
    def score_in_range(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and not 1 <= value <= 5:
            raise ValueError("mood_score must be between 1 and 5")
        return value


class MoodEntryOut(MoodEntryCreate):
    id: str
    user_id: str
    created_at: str
    updated_at: str


class JournalEntryCreate(BaseModel):
    written_at: datetime
    prompt: Optional[str] = None
    body: str

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("body must not be empty")
        return value


class JournalEntryUpdate(BaseModel):
    body: Optional[str] = None

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("body must not be empty")
        return value


class JournalEntryOut(JournalEntryCreate):
    id: str
    user_id: str
    created_at: str
    updated_at: str
```

`backend/app/mood/prompts.py`:
```python
from datetime import datetime, timezone

JOURNAL_PROMPTS: list[str] = [
    "What's one thing that went well today?",
    "What's weighing on you right now?",
    "Describe your energy level today and why.",
    "What's something you're looking forward to?",
    "What would make tomorrow feel a little easier?",
    "Who or what are you grateful for today?",
    "What's a small win you can celebrate?",
]


def prompt_for_today() -> str:
    day_index = datetime.now(timezone.utc).date().toordinal()
    return JOURNAL_PROMPTS[day_index % len(JOURNAL_PROMPTS)]
```

`backend/app/mood/router.py`:
```python
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user_id, get_journal_entry_repo, get_mood_entry_repo
from .models import (
    JournalEntryCreate,
    JournalEntryOut,
    JournalEntryUpdate,
    MoodEntryCreate,
    MoodEntryOut,
    MoodEntryUpdate,
)
from .prompts import prompt_for_today

router = APIRouter()


@router.get("/entries", response_model=list[MoodEntryOut])
async def list_mood_entries(
    start: Optional[date] = None,
    end: Optional[date] = None,
    user_id: str = Depends(get_current_user_id),
    mood_entry_repo=Depends(get_mood_entry_repo),
):
    return await mood_entry_repo.list_for_user(user_id, start=start, end=end)


@router.post("/entries", response_model=MoodEntryOut, status_code=status.HTTP_201_CREATED)
async def create_mood_entry(
    body: MoodEntryCreate,
    user_id: str = Depends(get_current_user_id),
    mood_entry_repo=Depends(get_mood_entry_repo),
):
    return await mood_entry_repo.create({**body.model_dump(mode="json"), "user_id": user_id})


@router.patch("/entries/{entry_id}", response_model=MoodEntryOut)
async def update_mood_entry(
    entry_id: str,
    body: MoodEntryUpdate,
    user_id: str = Depends(get_current_user_id),
    mood_entry_repo=Depends(get_mood_entry_repo),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = await mood_entry_repo.update(user_id, entry_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="mood entry not found")
    return updated


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mood_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    mood_entry_repo=Depends(get_mood_entry_repo),
):
    if not await mood_entry_repo.delete(user_id, entry_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="mood entry not found")


@router.get("/journal", response_model=list[JournalEntryOut])
async def list_journal_entries(
    user_id: str = Depends(get_current_user_id),
    journal_entry_repo=Depends(get_journal_entry_repo),
):
    return await journal_entry_repo.list_for_user(user_id)


@router.post("/journal", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    body: JournalEntryCreate,
    user_id: str = Depends(get_current_user_id),
    journal_entry_repo=Depends(get_journal_entry_repo),
):
    return await journal_entry_repo.create({**body.model_dump(mode="json"), "user_id": user_id})


@router.patch("/journal/{entry_id}", response_model=JournalEntryOut)
async def update_journal_entry(
    entry_id: str,
    body: JournalEntryUpdate,
    user_id: str = Depends(get_current_user_id),
    journal_entry_repo=Depends(get_journal_entry_repo),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = await journal_entry_repo.update(user_id, entry_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="journal entry not found")
    return updated


@router.delete("/journal/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    journal_entry_repo=Depends(get_journal_entry_repo),
):
    if not await journal_entry_repo.delete(user_id, entry_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="journal entry not found")


@router.get("/prompts")
async def get_todays_prompt(user_id: str = Depends(get_current_user_id)):
    return {"prompt": prompt_for_today()}
```

In `backend/app/main.py`, add `from .mood.router import router as mood_router` below the existing `from .meals.router import ...` line, and add below the existing `app.include_router(workouts_router, ...)` line:
```python
app.include_router(mood_router, prefix="/mood", tags=["mood"])
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/mood backend/app/main.py backend/tests/test_mood_router.py
git commit -m "$(cat <<'EOF'
Add mood and journal endpoints with validation and ownership checks

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Cosmos DB repositories for mood and journal entries

**Files:**
- Modify: `backend/app/db/cosmos.py`, `backend/app/deps.py`, `backend/tests/test_cosmos_repos.py`

**Interfaces:**
- Consumes: `settings` (existing); implements `MoodEntryRepository`/`JournalEntryRepository` Protocols (Task 3).
- Produces: `CosmosMoodEntryRepository`, `CosmosJournalEntryRepository` from `app.db.cosmos`.

- [ ] **Step 1: Write the failing tests**

Replace the `from app.db.cosmos import (...)` line at the top of `backend/tests/test_cosmos_repos.py` with:
```python
from app.db.cosmos import (
    CosmosExerciseRepository,
    CosmosFoodRepository,
    CosmosJournalEntryRepository,
    CosmosMealEntryRepository,
    CosmosMoodEntryRepository,
    CosmosUserRepository,
    CosmosWorkoutRepository,
)
```

Append to `backend/tests/test_cosmos_repos.py`:
```python
async def test_mood_entry_repository_list_for_user_queries_by_partition_key_and_range():
    container = MagicMock()

    async def fake_query_items(query, parameters, partition_key):
        assert partition_key == "user-1"
        assert "c.logged_at >= @start" in query
        for item in [{"id": "m1", "user_id": "user-1", "logged_at": "2026-10-05T08:00:00", "mood_score": 5}]:
            yield item

    container.query_items = fake_query_items
    repo = CosmosMoodEntryRepository(_client_with_container(container), "health_app")

    from datetime import date

    entries = await repo.list_for_user("user-1", start=date(2026, 10, 1))

    assert [e["id"] for e in entries] == ["m1"]


async def test_mood_entry_repository_create_assigns_id():
    container = MagicMock()
    container.create_item = AsyncMock()
    repo = CosmosMoodEntryRepository(_client_with_container(container), "health_app")

    record = await repo.create({"user_id": "user-1", "logged_at": "2026-10-01T08:00:00", "mood_score": 3, "tags": []})

    assert record["id"]
    container.create_item.assert_awaited_once_with(record)


async def test_journal_entry_repository_list_for_user_queries_by_partition_key():
    container = MagicMock()

    async def fake_query_items(query, parameters, partition_key):
        assert partition_key == "user-1"
        for item in [{"id": "j1", "user_id": "user-1", "written_at": "2026-10-01T08:00:00", "body": "hi"}]:
            yield item

    container.query_items = fake_query_items
    repo = CosmosJournalEntryRepository(_client_with_container(container), "health_app")

    entries = await repo.list_for_user("user-1")

    assert [e["id"] for e in entries] == ["j1"]
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_cosmos_repos.py -v
```
Expected: FAIL — `ImportError: cannot import name 'CosmosMoodEntryRepository'`.

- [ ] **Step 3: Implement**

In `backend/app/db/cosmos.py`, update `init_cosmos` to also create the new containers — append inside the function, before the function ends:
```python
    await database.create_container_if_not_exists(
        id="mood_entries", partition_key=PartitionKey(path="/user_id")
    )
    await database.create_container_if_not_exists(
        id="journal_entries", partition_key=PartitionKey(path="/user_id")
    )
```

Append to `backend/app/db/cosmos.py`:
```python
class CosmosMoodEntryRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("mood_entries")

    async def create(self, entry: dict) -> dict:
        container = self._container()
        now = datetime.now(timezone.utc).isoformat()
        record = {**entry, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        await container.create_item(record)
        return record

    async def list_for_user(
        self, user_id: str, start: Optional[date] = None, end: Optional[date] = None
    ) -> list[dict]:
        container = self._container()
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        params = [{"name": "@user_id", "value": user_id}]
        if start is not None:
            query += " AND c.logged_at >= @start"
            params.append({"name": "@start", "value": start.isoformat()})
        if end is not None:
            query += " AND c.logged_at <= @end"
            params.append({"name": "@end", "value": f"{end.isoformat()}T23:59:59"})
        items = [
            item
            async for item in container.query_items(query=query, parameters=params, partition_key=user_id)
        ]
        return sorted(items, key=lambda e: e["logged_at"], reverse=True)

    async def get(self, user_id: str, entry_id: str) -> Optional[dict]:
        container = self._container()
        try:
            return await container.read_item(item=entry_id, partition_key=user_id)
        except Exception:
            return None

    async def update(self, user_id: str, entry_id: str, updates: dict) -> Optional[dict]:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return None
        entry.update(updates)
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._container().replace_item(item=entry_id, body=entry)
        return entry

    async def delete(self, user_id: str, entry_id: str) -> bool:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return False
        await self._container().delete_item(item=entry_id, partition_key=user_id)
        return True


class CosmosJournalEntryRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("journal_entries")

    async def create(self, entry: dict) -> dict:
        container = self._container()
        now = datetime.now(timezone.utc).isoformat()
        record = {**entry, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        await container.create_item(record)
        return record

    async def list_for_user(self, user_id: str) -> list[dict]:
        container = self._container()
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        params = [{"name": "@user_id", "value": user_id}]
        items = [
            item
            async for item in container.query_items(query=query, parameters=params, partition_key=user_id)
        ]
        return sorted(items, key=lambda e: e["written_at"], reverse=True)

    async def get(self, user_id: str, entry_id: str) -> Optional[dict]:
        container = self._container()
        try:
            return await container.read_item(item=entry_id, partition_key=user_id)
        except Exception:
            return None

    async def update(self, user_id: str, entry_id: str, updates: dict) -> Optional[dict]:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return None
        entry.update(updates)
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._container().replace_item(item=entry_id, body=entry)
        return entry

    async def delete(self, user_id: str, entry_id: str) -> bool:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return False
        await self._container().delete_item(item=entry_id, partition_key=user_id)
        return True
```

In `backend/app/deps.py`, add `CosmosJournalEntryRepository, CosmosMoodEntryRepository` to the existing `from .db.cosmos import (...)` line, then replace the `get_mood_entry_repo` / `get_journal_entry_repo` functions with:
```python
def get_mood_entry_repo():
    if settings.db_backend == "cosmos":
        return CosmosMoodEntryRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_mood_entry_repo


def get_journal_entry_repo():
    if settings.db_backend == "cosmos":
        return CosmosJournalEntryRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_journal_entry_repo
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass. `db_backend` defaults to `"memory"`, so the suite still runs with zero Azure connectivity.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/cosmos.py backend/app/deps.py backend/tests/test_cosmos_repos.py
git commit -m "$(cat <<'EOF'
Add Cosmos DB repositories for mood and journal entries

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Mind client API bindings and types

**Files:**
- Create: `src/modules/mental_health/types.ts`, `src/modules/mental_health/api.ts`

**Interfaces:**
- Consumes: `apiFetch` (`src/lib/api-client.ts`, existing).
- Produces: `MoodEntry`, `MoodEntryInput`, `JournalEntry`, `JournalEntryInput` types; `listMoodEntries(start?, end?)`, `createMoodEntry(entry)`, `deleteMoodEntry(id)`, `listJournalEntries()`, `createJournalEntry(entry)`, `deleteJournalEntry(id)`, `getTodaysPrompt()` — used by Task 7.

- [ ] **Step 1: Define the shared types**

`src/modules/mental_health/types.ts`:
```typescript
export type MoodEntry = {
  id: string;
  user_id: string;
  logged_at: string;
  mood_score: number;
  tags: string[];
  note?: string;
  created_at: string;
  updated_at: string;
};

export type MoodEntryInput = {
  logged_at: string;
  mood_score: number;
  tags?: string[];
  note?: string;
};

export type JournalEntry = {
  id: string;
  user_id: string;
  written_at: string;
  prompt?: string;
  body: string;
  created_at: string;
  updated_at: string;
};

export type JournalEntryInput = {
  written_at: string;
  prompt?: string;
  body: string;
};
```

- [ ] **Step 2: Implement the API bindings**

`src/modules/mental_health/api.ts`:
```typescript
import { apiFetch } from "@/lib/api-client";

import type { JournalEntry, JournalEntryInput, MoodEntry, MoodEntryInput } from "./types";

export function listMoodEntries(start?: string, end?: string): Promise<MoodEntry[]> {
  const params = new URLSearchParams();
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  const query = params.toString();
  return apiFetch<MoodEntry[]>(`/mood/entries${query ? `?${query}` : ""}`);
}

export function createMoodEntry(entry: MoodEntryInput): Promise<MoodEntry> {
  return apiFetch<MoodEntry>("/mood/entries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  });
}

export function deleteMoodEntry(id: string): Promise<void> {
  return apiFetch<void>(`/mood/entries/${id}`, { method: "DELETE" });
}

export function listJournalEntries(): Promise<JournalEntry[]> {
  return apiFetch<JournalEntry[]>("/mood/journal");
}

export function createJournalEntry(entry: JournalEntryInput): Promise<JournalEntry> {
  return apiFetch<JournalEntry>("/mood/journal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  });
}

export function deleteJournalEntry(id: string): Promise<void> {
  return apiFetch<void>(`/mood/journal/${id}`, { method: "DELETE" });
}

export function getTodaysPrompt(): Promise<{ prompt: string }> {
  return apiFetch<{ prompt: string }>("/mood/prompts");
}
```

- [ ] **Step 3: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add src/modules/mental_health/types.ts src/modules/mental_health/api.ts
git commit -m "$(cat <<'EOF'
Add Mind client API bindings and shared types

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Mind screens (check-in, journal, history)

**Files:**
- Create: `src/app/mental-health/_layout.tsx`, `src/app/mental-health/index.tsx`, `src/app/mental-health/journal.tsx`, `src/app/mental-health/history.tsx`

**Interfaces:**
- Consumes: `ScreenContainer`, `Card`, `Button` (`@/components`, Task 2); `useTheme` (`@/lib/theme`, Task 1); `listMoodEntries`, `createMoodEntry`, `listJournalEntries`, `createJournalEntry`, `getTodaysPrompt` (`@/modules/mental_health/api`, Task 6).
- Produces: the `/mental-health` route tree — consumed by the Today dashboard (Task 19).

- [ ] **Step 1: Layout**

`src/app/mental-health/_layout.tsx`:
```tsx
import { Stack } from "expo-router";

export default function MentalHealthLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Mind" }} />
      <Stack.Screen name="journal" options={{ title: "Journal" }} />
      <Stack.Screen name="history" options={{ title: "History" }} />
    </Stack>
  );
}
```

- [ ] **Step 2: Check-in home**

`src/app/mental-health/index.tsx`:
```tsx
import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Pressable, Text, View } from "react-native";

import { Button, Card, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createMoodEntry, getTodaysPrompt, listMoodEntries } from "@/modules/mental_health/api";
import type { MoodEntry } from "@/modules/mental_health/types";

const MOOD_OPTIONS: { score: number; emoji: string; label: string }[] = [
  { score: 1, emoji: "😞", label: "Rough" },
  { score: 2, emoji: "🙁", label: "Low" },
  { score: 3, emoji: "😐", label: "Okay" },
  { score: 4, emoji: "🙂", label: "Good" },
  { score: 5, emoji: "😄", label: "Great" },
];

export default function MentalHealthRoute() {
  const router = useRouter();
  const { colors, pillars, font } = useTheme();
  const accent = pillars.mind.light;
  const [recent, setRecent] = useState<MoodEntry[]>([]);
  const [prompt, setPrompt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [entries, todays] = await Promise.all([listMoodEntries(), getTodaysPrompt()]);
      setRecent(entries.slice(0, 5));
      setPrompt(todays.prompt);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load");
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const checkIn = async (score: number) => {
    setSaving(true);
    try {
      await createMoodEntry({ logged_at: new Date().toISOString(), mood_score: score, tags: [] });
      setError(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to save check-in");
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScreenContainer>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>Mind</Text>
      {error ? <Text style={{ color: "#C0392B" }}>{error}</Text> : null}

      <Card>
        <Text style={{ fontFamily: font.semibold, fontSize: 16, color: colors.textPrimary }}>
          How are you feeling right now?
        </Text>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          {MOOD_OPTIONS.map((option) => (
            <Pressable
              key={option.score}
              disabled={saving}
              onPress={() => checkIn(option.score)}
              style={{ alignItems: "center", gap: 4, opacity: saving ? 0.5 : 1 }}
            >
              <Text style={{ fontSize: 28 }}>{option.emoji}</Text>
              <Text style={{ fontFamily: font.regular, fontSize: 11, color: colors.textSecondary }}>
                {option.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </Card>

      <Card style={{ borderColor: accent, borderWidth: 1.5 }}>
        <Text style={{ fontFamily: font.semibold, fontSize: 13, color: colors.textSecondary }}>
          TODAY'S PROMPT
        </Text>
        <Text style={{ fontFamily: font.regular, fontSize: 15, color: colors.textPrimary }}>
          {prompt ?? "Loading..."}
        </Text>
        <Button
          title="Write in journal"
          variant="secondary"
          color={accent}
          onPress={() => router.push("/mental-health/journal" as Href)}
        />
      </Card>

      <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textSecondary }}>
        Recent check-ins
      </Text>
      {recent.length === 0 ? (
        <Text style={{ color: colors.textSecondary }}>No check-ins yet.</Text>
      ) : (
        recent.map((entry) => (
          <Text key={entry.id} style={{ color: colors.textPrimary }}>
            {MOOD_OPTIONS.find((o) => o.score === entry.mood_score)?.emoji}{" "}
            {new Date(entry.logged_at).toLocaleDateString()}
          </Text>
        ))
      )}

      <Button
        title="View history"
        variant="text"
        color={accent}
        onPress={() => router.push("/mental-health/history" as Href)}
      />
    </ScreenContainer>
  );
}
```

- [ ] **Step 3: Journal screen**

`src/app/mental-health/journal.tsx`:
```tsx
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Text, TextInput } from "react-native";

import { Button, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createJournalEntry, getTodaysPrompt } from "@/modules/mental_health/api";

export default function JournalRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.mind.light;
  const [prompt, setPrompt] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getTodaysPrompt()
      .then((res) => setPrompt(res.prompt))
      .catch(() => setPrompt(null));
  }, []);

  const save = async () => {
    setError(null);
    if (!body.trim()) {
      setError("Write something first.");
      return;
    }
    setSaving(true);
    try {
      await createJournalEntry({ written_at: new Date().toISOString(), prompt: prompt ?? undefined, body });
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to save entry");
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScreenContainer>
      <Text style={{ fontFamily: font.bold, fontSize: 20, color: colors.textPrimary }}>Journal</Text>
      {prompt ? (
        <Text style={{ fontFamily: font.regular, fontSize: 14, color: colors.textSecondary }}>{prompt}</Text>
      ) : null}
      <TextInput
        placeholder="What's on your mind?"
        value={body}
        onChangeText={setBody}
        multiline
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 12,
          padding: spacing.md,
          minHeight: 160,
          fontFamily: font.regular,
          color: colors.textPrimary,
          textAlignVertical: "top",
        }}
      />
      {error ? <Text style={{ color: "#C0392B" }}>{error}</Text> : null}
      <Button title="Save entry" color={accent} onPress={save} disabled={saving} />
    </ScreenContainer>
  );
}
```

- [ ] **Step 4: History screen**

`src/app/mental-health/history.tsx`:
```tsx
import { useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { Text } from "react-native";

import { ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { listJournalEntries, listMoodEntries } from "@/modules/mental_health/api";
import type { JournalEntry, MoodEntry } from "@/modules/mental_health/types";

const MOOD_EMOJI: Record<number, string> = { 1: "😞", 2: "🙁", 3: "😐", 4: "🙂", 5: "😄" };

export default function MentalHealthHistoryRoute() {
  const { colors, font, spacing } = useTheme();
  const [moods, setMoods] = useState<MoodEntry[]>([]);
  const [journals, setJournals] = useState<JournalEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [moodEntries, journalEntries] = await Promise.all([listMoodEntries(), listJournalEntries()]);
      setMoods(moodEntries);
      setJournals(journalEntries);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load history");
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  return (
    <ScreenContainer style={{ gap: spacing.lg }}>
      <Text style={{ fontFamily: font.bold, fontSize: 20, color: colors.textPrimary }}>History</Text>
      {error ? <Text style={{ color: "#C0392B" }}>{error}</Text> : null}

      <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textSecondary }}>
        Mood check-ins
      </Text>
      <Text style={{ fontSize: 22, letterSpacing: 4 }}>
        {moods.length === 0
          ? "No check-ins yet."
          : moods.slice(0, 30).map((m) => MOOD_EMOJI[m.mood_score]).join(" ")}
      </Text>

      <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textSecondary }}>
        Journal entries
      </Text>
      {journals.length === 0 ? (
        <Text style={{ color: colors.textSecondary }}>No journal entries yet.</Text>
      ) : (
        journals.map((entry) => (
          <Text key={entry.id} style={{ color: colors.textPrimary, marginBottom: spacing.sm }}>
            {new Date(entry.written_at).toLocaleDateString()} — {entry.body}
          </Text>
        ))
      )}
    </ScreenContainer>
  );
}
```

- [ ] **Step 5: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 6: Manual verification**

```bash
cd backend && uvicorn app.main:app --reload &
npx expo start
```
Log in, navigate to `/mental-health`. Confirm "No check-ins yet." shows initially, tap an emoji, confirm it appears under "Recent check-ins" and the lavender accent shows on the prompt card. Tap "Write in journal", type something, save, confirm it navigates back. Tap "View history", confirm the mood emoji row and journal entry both appear.

- [ ] **Step 7: Commit**

```bash
git add src/app/mental-health
git commit -m "$(cat <<'EOF'
Add Mind screens: check-in, journal, history

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Screen-time rule repository interface, in-memory implementation, and dependency wiring

**Files:**
- Modify: `backend/app/db/base.py`, `backend/app/db/memory.py`, `backend/app/deps.py`, `backend/tests/conftest.py`, `backend/tests/test_memory_repositories.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `ScreenTimeRuleRepository` Protocol from `app.db.base`; `InMemoryScreenTimeRuleRepository` from `app.db.memory`; `get_screentime_rule_repo()` from `app.deps` — used by Task 9 onward.

- [ ] **Step 1: Write the failing tests**

Replace the `from app.db.memory import (...)` line at the top of `backend/tests/test_memory_repositories.py` with:
```python
from app.db.memory import (
    SEED_EXERCISES,
    SEED_FOODS,
    InMemoryExerciseRepository,
    InMemoryFoodRepository,
    InMemoryJournalEntryRepository,
    InMemoryMealEntryRepository,
    InMemoryMoodEntryRepository,
    InMemoryScreenTimeRuleRepository,
    InMemoryUserRepository,
    InMemoryWorkoutRepository,
)
```

Append to `backend/tests/test_memory_repositories.py`:
```python
async def test_screentime_rule_repository_crud_scoped_by_user():
    repo = InMemoryScreenTimeRuleRepository()

    rule = await repo.create(
        {"user_id": "user-1", "name": "Evening wind-down", "apps_or_categories": ["social"], "enabled": True}
    )

    assert rule["id"]
    mine = await repo.list_for_user("user-1")
    assert [r["id"] for r in mine] == [rule["id"]]
    assert await repo.list_for_user("user-2") == []

    updated = await repo.update("user-1", rule["id"], {"enabled": False})
    assert updated["enabled"] is False
    assert await repo.update("user-2", rule["id"], {"enabled": True}) is None

    assert await repo.delete("user-2", rule["id"]) is False
    assert await repo.delete("user-1", rule["id"]) is True
    assert await repo.get("user-1", rule["id"]) is None
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_memory_repositories.py -v
```
Expected: FAIL with `ImportError: cannot import name 'InMemoryScreenTimeRuleRepository'`.

- [ ] **Step 3: Implement**

Append to `backend/app/db/base.py`:
```python
class ScreenTimeRuleRepository(Protocol):
    async def create(self, rule: dict) -> dict: ...
    async def list_for_user(self, user_id: str) -> list[dict]: ...
    async def get(self, user_id: str, rule_id: str) -> Optional[dict]: ...
    async def update(self, user_id: str, rule_id: str, updates: dict) -> Optional[dict]: ...
    async def delete(self, user_id: str, rule_id: str) -> bool: ...
```

Append to `backend/app/db/memory.py`:
```python
class InMemoryScreenTimeRuleRepository:
    def __init__(self):
        self._rules: dict[str, dict] = {}

    async def create(self, rule: dict) -> dict:
        rule_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {**rule, "id": rule_id, "created_at": now, "updated_at": now}
        self._rules[rule_id] = record
        return record

    async def list_for_user(self, user_id: str) -> list[dict]:
        results = [r for r in self._rules.values() if r["user_id"] == user_id]
        return sorted(results, key=lambda r: r["created_at"], reverse=True)

    async def get(self, user_id: str, rule_id: str) -> Optional[dict]:
        rule = self._rules.get(rule_id)
        return rule if rule and rule["user_id"] == user_id else None

    async def update(self, user_id: str, rule_id: str, updates: dict) -> Optional[dict]:
        rule = await self.get(user_id, rule_id)
        if not rule:
            return None
        rule.update(updates)
        rule["updated_at"] = datetime.now(timezone.utc).isoformat()
        return rule

    async def delete(self, user_id: str, rule_id: str) -> bool:
        rule = await self.get(user_id, rule_id)
        if not rule:
            return False
        del self._rules[rule["id"]]
        return True
```

In `backend/app/deps.py`, add `InMemoryScreenTimeRuleRepository` to the existing `from .db.memory import (...)` line, add below the existing `_memory_journal_entry_repo = ...` line:
```python
_memory_screentime_rule_repo = InMemoryScreenTimeRuleRepository()
```
and add below the existing `get_journal_entry_repo` function:
```python
def get_screentime_rule_repo():
    return _memory_screentime_rule_repo
```

In `backend/tests/conftest.py`, add `InMemoryScreenTimeRuleRepository` to the `from app.db.memory import (...)` line, add inside the `client` fixture below `journal_entry_repo = InMemoryJournalEntryRepository()`:
```python
    screentime_rule_repo = InMemoryScreenTimeRuleRepository()
```
and add below the existing `app.dependency_overrides[deps.get_journal_entry_repo] = ...` line:
```python
    app.dependency_overrides[deps.get_screentime_rule_repo] = lambda: screentime_rule_repo
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/base.py backend/app/db/memory.py backend/app/deps.py backend/tests/conftest.py backend/tests/test_memory_repositories.py
git commit -m "$(cat <<'EOF'
Add screen-time rule repository interface with in-memory implementation

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Screen-time rule endpoints (CRUD, validation, ownership) — phase 1, no enforcement

**Files:**
- Create: `backend/app/screentime/__init__.py`, `backend/app/screentime/models.py`, `backend/app/screentime/router.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_screentime_router.py` (new)

**Interfaces:**
- Consumes: `get_current_user_id`, `get_screentime_rule_repo` (Task 8).
- Produces: `GET/POST /screentime/rules`, `PATCH/DELETE /screentime/rules/{id}`; `ScreenTimeRuleCreate`, `ScreenTimeRuleUpdate`, `ScreenTimeRuleOut` — consumed by the client tasks (Task 11). Deliberately no usage-upload or usage-dashboard endpoints this phase (see spec's "Digital Health phase 1" section).

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_screentime_router.py`:
```python
RULE_PAYLOAD = {"name": "Evening wind-down", "apps_or_categories": ["social", "games"], "daily_limit_minutes": 30}


def test_create_and_list_rule(client, auth_headers):
    headers = auth_headers()

    create = client.post("/screentime/rules", json=RULE_PAYLOAD, headers=headers)
    assert create.status_code == 201
    assert create.json()["enabled"] is True

    listing = client.get("/screentime/rules", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_rule_without_categories_is_rejected(client, auth_headers):
    headers = auth_headers()
    payload = {**RULE_PAYLOAD, "apps_or_categories": []}

    response = client.post("/screentime/rules", json=payload, headers=headers)

    assert response.status_code == 422


def test_rule_with_non_positive_daily_limit_is_rejected(client, auth_headers):
    headers = auth_headers()

    zero = client.post("/screentime/rules", json={**RULE_PAYLOAD, "daily_limit_minutes": 0}, headers=headers)
    negative = client.post("/screentime/rules", json={**RULE_PAYLOAD, "daily_limit_minutes": -5}, headers=headers)

    assert zero.status_code == 422
    assert negative.status_code == 422


def test_rule_with_blank_name_is_rejected(client, auth_headers):
    headers = auth_headers()
    payload = {**RULE_PAYLOAD, "name": "   "}

    response = client.post("/screentime/rules", json=payload, headers=headers)

    assert response.status_code == 422


def test_update_and_delete_own_rule(client, auth_headers):
    headers = auth_headers()
    rule_id = client.post("/screentime/rules", json=RULE_PAYLOAD, headers=headers).json()["id"]

    update = client.patch(f"/screentime/rules/{rule_id}", json={"enabled": False}, headers=headers)
    assert update.status_code == 200
    assert update.json()["enabled"] is False

    delete = client.delete(f"/screentime/rules/{rule_id}", headers=headers)
    assert delete.status_code == 204

    listing = client.get("/screentime/rules", headers=headers)
    assert listing.json() == []


def test_user_cannot_read_or_modify_another_users_rule(client, auth_headers):
    headers_a = auth_headers(email="rule-owner@example.com")
    headers_b = auth_headers(email="rule-intruder@example.com")
    rule_id = client.post("/screentime/rules", json=RULE_PAYLOAD, headers=headers_a).json()["id"]

    update = client.patch(f"/screentime/rules/{rule_id}", json={"enabled": False}, headers=headers_b)
    assert update.status_code == 404

    delete = client.delete(f"/screentime/rules/{rule_id}", headers=headers_b)
    assert delete.status_code == 404

    listing = client.get("/screentime/rules", headers=headers_b)
    assert listing.json() == []


def test_screentime_rules_require_auth(client):
    response = client.get("/screentime/rules")

    assert response.status_code == 403
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_screentime_router.py -v
```
Expected: FAIL — `/screentime` routes don't exist yet.

- [ ] **Step 3: Implement**

`backend/app/screentime/__init__.py`: empty file.

`backend/app/screentime/models.py`:
```python
from typing import Optional

from pydantic import BaseModel, field_validator


class ScreenTimeRuleCreate(BaseModel):
    name: str
    apps_or_categories: list[str]
    daily_limit_minutes: Optional[int] = None
    enabled: bool = True

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be empty")
        return value

    @field_validator("apps_or_categories")
    @classmethod
    def categories_not_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("apps_or_categories must have at least one entry")
        return value

    @field_validator("daily_limit_minutes")
    @classmethod
    def limit_must_be_positive(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("daily_limit_minutes must be greater than 0")
        return value


class ScreenTimeRuleUpdate(BaseModel):
    name: Optional[str] = None
    apps_or_categories: Optional[list[str]] = None
    daily_limit_minutes: Optional[int] = None
    enabled: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("name must not be empty")
        return value

    @field_validator("daily_limit_minutes")
    @classmethod
    def limit_must_be_positive(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("daily_limit_minutes must be greater than 0")
        return value


class ScreenTimeRuleOut(ScreenTimeRuleCreate):
    id: str
    user_id: str
    created_at: str
    updated_at: str
```

`backend/app/screentime/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user_id, get_screentime_rule_repo
from .models import ScreenTimeRuleCreate, ScreenTimeRuleOut, ScreenTimeRuleUpdate

router = APIRouter()


@router.get("/rules", response_model=list[ScreenTimeRuleOut])
async def list_rules(
    user_id: str = Depends(get_current_user_id),
    screentime_rule_repo=Depends(get_screentime_rule_repo),
):
    return await screentime_rule_repo.list_for_user(user_id)


@router.post("/rules", response_model=ScreenTimeRuleOut, status_code=status.HTTP_201_CREATED)
async def create_rule(
    body: ScreenTimeRuleCreate,
    user_id: str = Depends(get_current_user_id),
    screentime_rule_repo=Depends(get_screentime_rule_repo),
):
    return await screentime_rule_repo.create({**body.model_dump(mode="json"), "user_id": user_id})


@router.patch("/rules/{rule_id}", response_model=ScreenTimeRuleOut)
async def update_rule(
    rule_id: str,
    body: ScreenTimeRuleUpdate,
    user_id: str = Depends(get_current_user_id),
    screentime_rule_repo=Depends(get_screentime_rule_repo),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = await screentime_rule_repo.update(user_id, rule_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    return updated


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: str,
    user_id: str = Depends(get_current_user_id),
    screentime_rule_repo=Depends(get_screentime_rule_repo),
):
    if not await screentime_rule_repo.delete(user_id, rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
```

In `backend/app/main.py`, add `from .screentime.router import router as screentime_router` below the `from .mood.router import ...` line, and add below the `app.include_router(mood_router, ...)` line:
```python
app.include_router(screentime_router, prefix="/screentime", tags=["screentime"])
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/screentime backend/app/main.py backend/tests/test_screentime_router.py
git commit -m "$(cat <<'EOF'
Add screen-time rule endpoints, phase 1 (no enforcement)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Cosmos DB repository for screen-time rules

**Files:**
- Modify: `backend/app/db/cosmos.py`, `backend/app/deps.py`, `backend/tests/test_cosmos_repos.py`

**Interfaces:**
- Consumes: `settings` (existing); implements `ScreenTimeRuleRepository` Protocol (Task 8).
- Produces: `CosmosScreenTimeRuleRepository` from `app.db.cosmos`.

- [ ] **Step 1: Write the failing tests**

Replace the `from app.db.cosmos import (...)` line at the top of `backend/tests/test_cosmos_repos.py` with:
```python
from app.db.cosmos import (
    CosmosExerciseRepository,
    CosmosFoodRepository,
    CosmosJournalEntryRepository,
    CosmosMealEntryRepository,
    CosmosMoodEntryRepository,
    CosmosScreenTimeRuleRepository,
    CosmosUserRepository,
    CosmosWorkoutRepository,
)
```

Append to `backend/tests/test_cosmos_repos.py`:
```python
async def test_screentime_rule_repository_list_for_user_queries_by_partition_key():
    container = MagicMock()

    async def fake_query_items(query, parameters, partition_key):
        assert partition_key == "user-1"
        for item in [{"id": "r1", "user_id": "user-1", "name": "Wind-down", "created_at": "2026-10-01T08:00:00"}]:
            yield item

    container.query_items = fake_query_items
    repo = CosmosScreenTimeRuleRepository(_client_with_container(container), "health_app")

    rules = await repo.list_for_user("user-1")

    assert [r["id"] for r in rules] == ["r1"]


async def test_screentime_rule_repository_create_assigns_id():
    container = MagicMock()
    container.create_item = AsyncMock()
    repo = CosmosScreenTimeRuleRepository(_client_with_container(container), "health_app")

    record = await repo.create(
        {"user_id": "user-1", "name": "Wind-down", "apps_or_categories": ["social"], "enabled": True}
    )

    assert record["id"]
    container.create_item.assert_awaited_once_with(record)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_cosmos_repos.py -v
```
Expected: FAIL — `ImportError: cannot import name 'CosmosScreenTimeRuleRepository'`.

- [ ] **Step 3: Implement**

In `backend/app/db/cosmos.py`, update `init_cosmos` to also create the new container — append inside the function, before it ends:
```python
    await database.create_container_if_not_exists(
        id="screentime_rules", partition_key=PartitionKey(path="/user_id")
    )
```

Append to `backend/app/db/cosmos.py`:
```python
class CosmosScreenTimeRuleRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("screentime_rules")

    async def create(self, rule: dict) -> dict:
        container = self._container()
        now = datetime.now(timezone.utc).isoformat()
        record = {**rule, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        await container.create_item(record)
        return record

    async def list_for_user(self, user_id: str) -> list[dict]:
        container = self._container()
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        params = [{"name": "@user_id", "value": user_id}]
        items = [
            item
            async for item in container.query_items(query=query, parameters=params, partition_key=user_id)
        ]
        return sorted(items, key=lambda r: r["created_at"], reverse=True)

    async def get(self, user_id: str, rule_id: str) -> Optional[dict]:
        container = self._container()
        try:
            return await container.read_item(item=rule_id, partition_key=user_id)
        except Exception:
            return None

    async def update(self, user_id: str, rule_id: str, updates: dict) -> Optional[dict]:
        rule = await self.get(user_id, rule_id)
        if not rule:
            return None
        rule.update(updates)
        rule["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._container().replace_item(item=rule_id, body=rule)
        return rule

    async def delete(self, user_id: str, rule_id: str) -> bool:
        rule = await self.get(user_id, rule_id)
        if not rule:
            return False
        await self._container().delete_item(item=rule_id, partition_key=user_id)
        return True
```

In `backend/app/deps.py`, add `CosmosScreenTimeRuleRepository` to the existing `from .db.cosmos import (...)` line, then replace the `get_screentime_rule_repo` function with:
```python
def get_screentime_rule_repo():
    if settings.db_backend == "cosmos":
        return CosmosScreenTimeRuleRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_screentime_rule_repo
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/cosmos.py backend/app/deps.py backend/tests/test_cosmos_repos.py
git commit -m "$(cat <<'EOF'
Add Cosmos DB repository for screen-time rules

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Focus client API bindings and types

**Files:**
- Create: `src/modules/digital_health/types.ts`, `src/modules/digital_health/api.ts`

**Interfaces:**
- Consumes: `apiFetch` (`src/lib/api-client.ts`, existing).
- Produces: `ScreenTimeRule`, `ScreenTimeRuleInput`, `ScreenTimeRuleUpdateInput` types; `listScreenTimeRules()`, `createScreenTimeRule(rule)`, `updateScreenTimeRule(id, updates)`, `deleteScreenTimeRule(id)` — used by Task 12.

- [ ] **Step 1: Define the shared types**

`src/modules/digital_health/types.ts`:
```typescript
export type ScreenTimeRule = {
  id: string;
  user_id: string;
  name: string;
  apps_or_categories: string[];
  daily_limit_minutes?: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type ScreenTimeRuleInput = {
  name: string;
  apps_or_categories: string[];
  daily_limit_minutes?: number;
  enabled?: boolean;
};

export type ScreenTimeRuleUpdateInput = {
  name?: string;
  apps_or_categories?: string[];
  daily_limit_minutes?: number;
  enabled?: boolean;
};
```

- [ ] **Step 2: Implement the API bindings**

`src/modules/digital_health/api.ts`:
```typescript
import { apiFetch } from "@/lib/api-client";

import type { ScreenTimeRule, ScreenTimeRuleInput, ScreenTimeRuleUpdateInput } from "./types";

export function listScreenTimeRules(): Promise<ScreenTimeRule[]> {
  return apiFetch<ScreenTimeRule[]>("/screentime/rules");
}

export function createScreenTimeRule(rule: ScreenTimeRuleInput): Promise<ScreenTimeRule> {
  return apiFetch<ScreenTimeRule>("/screentime/rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rule),
  });
}

export function updateScreenTimeRule(
  id: string,
  updates: ScreenTimeRuleUpdateInput
): Promise<ScreenTimeRule> {
  return apiFetch<ScreenTimeRule>(`/screentime/rules/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
}

export function deleteScreenTimeRule(id: string): Promise<void> {
  return apiFetch<void>(`/screentime/rules/${id}`, { method: "DELETE" });
}
```

- [ ] **Step 3: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add src/modules/digital_health/types.ts src/modules/digital_health/api.ts
git commit -m "$(cat <<'EOF'
Add Focus client API bindings and shared types

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Focus screens (dashboard, rule builder)

**Files:**
- Create: `src/app/digital-health/_layout.tsx`, `src/app/digital-health/index.tsx`, `src/app/digital-health/rule-builder.tsx`

**Interfaces:**
- Consumes: `ScreenContainer`, `Card`, `Button`, `Chip` (`@/components`, Task 2); `useTheme` (`@/lib/theme`, Task 1); `listScreenTimeRules`, `updateScreenTimeRule`, `deleteScreenTimeRule`, `createScreenTimeRule` (`@/modules/digital_health/api`, Task 11).
- Produces: the `/digital-health` route tree — consumed by the Today dashboard (Task 19).

- [ ] **Step 1: Layout**

`src/app/digital-health/_layout.tsx`:
```tsx
import { Stack } from "expo-router";

export default function DigitalHealthLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Focus" }} />
      <Stack.Screen name="rule-builder" options={{ title: "New Rule" }} />
    </Stack>
  );
}
```

- [ ] **Step 2: Dashboard**

`src/app/digital-health/index.tsx`:
```tsx
import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, Text, View } from "react-native";

import { Button, Card, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { deleteScreenTimeRule, listScreenTimeRules, updateScreenTimeRule } from "@/modules/digital_health/api";
import type { ScreenTimeRule } from "@/modules/digital_health/types";

export default function DigitalHealthRoute() {
  const router = useRouter();
  const { colors, pillars, font } = useTheme();
  const accent = pillars.focus.light;
  const [rules, setRules] = useState<ScreenTimeRule[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      setRules(await listScreenTimeRules());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load rules");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const toggleRule = async (rule: ScreenTimeRule) => {
    try {
      await updateScreenTimeRule(rule.id, { enabled: !rule.enabled });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to update rule");
    }
  };

  const removeRule = (rule: ScreenTimeRule) => {
    Alert.alert("Delete rule?", "This can't be undone.", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            await deleteScreenTimeRule(rule.id);
            load();
          } catch (err) {
            setError(err instanceof Error ? err.message : "failed to delete rule");
          }
        },
      },
    ]);
  };

  return (
    <ScreenContainer>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>Focus</Text>
      {error ? <Text style={{ color: "#C0392B" }}>{error}</Text> : null}

      <Card style={{ borderColor: accent, borderWidth: 1.5 }}>
        <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textPrimary }}>
          Enforcement coming soon
        </Text>
        <Text style={{ fontFamily: font.regular, fontSize: 13, color: colors.textSecondary }}>
          You can set up rules now. Actually blocking apps on a schedule needs a deeper platform
          integration we haven't shipped yet — your rules are saved and ready for when it lands.
        </Text>
      </Card>

      {isLoading ? null : rules.length === 0 ? (
        <Text style={{ color: colors.textSecondary }}>No rules yet.</Text>
      ) : (
        rules.map((rule) => (
          <Card key={rule.id}>
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
              <Text style={{ fontFamily: font.semibold, fontSize: 15, color: colors.textPrimary }}>
                {rule.name}
              </Text>
              <Button
                title={rule.enabled ? "Enabled" : "Disabled"}
                variant={rule.enabled ? "primary" : "secondary"}
                color={accent}
                onPress={() => toggleRule(rule)}
              />
            </View>
            <Text style={{ fontFamily: font.regular, fontSize: 13, color: colors.textSecondary }}>
              {rule.apps_or_categories.join(", ")}
              {rule.daily_limit_minutes ? ` · ${rule.daily_limit_minutes} min/day` : ""}
            </Text>
            <Button title="Delete" variant="text" color="#C0392B" onPress={() => removeRule(rule)} />
          </Card>
        ))
      )}

      <Button
        title="Add rule"
        color={accent}
        onPress={() => router.push("/digital-health/rule-builder" as Href)}
      />
    </ScreenContainer>
  );
}
```

- [ ] **Step 3: Rule builder**

`src/app/digital-health/rule-builder.tsx`:
```tsx
import { useRouter } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";

import { Button, Chip, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createScreenTimeRule } from "@/modules/digital_health/api";

const CATEGORY_OPTIONS = ["Social", "Games", "Video", "News", "Shopping", "Other"];

export default function RuleBuilderRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.focus.light;
  const [name, setName] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [limitMinutes, setLimitMinutes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const toggleCategory = (category: string) => {
    setCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    );
  };

  const save = async () => {
    setError(null);
    if (!name.trim()) {
      setError("Give the rule a name.");
      return;
    }
    if (categories.length === 0) {
      setError("Pick at least one category.");
      return;
    }
    setSaving(true);
    try {
      await createScreenTimeRule({
        name,
        apps_or_categories: categories,
        daily_limit_minutes: limitMinutes ? Number(limitMinutes) : undefined,
      });
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to save rule");
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScreenContainer>
      <Text style={{ fontFamily: font.bold, fontSize: 20, color: colors.textPrimary }}>New Rule</Text>
      <TextInput
        placeholder="Name (e.g. Evening wind-down)"
        value={name}
        onChangeText={setName}
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 12,
          padding: spacing.md,
          fontFamily: font.regular,
          color: colors.textPrimary,
        }}
      />
      <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textSecondary }}>
        Which apps?
      </Text>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        {CATEGORY_OPTIONS.map((category) => (
          <Chip
            key={category}
            label={category}
            selected={categories.includes(category)}
            onPress={() => toggleCategory(category)}
            color={accent}
          />
        ))}
      </View>
      <TextInput
        placeholder="Daily limit, minutes (optional)"
        value={limitMinutes}
        onChangeText={setLimitMinutes}
        keyboardType="number-pad"
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 12,
          padding: spacing.md,
          fontFamily: font.regular,
          color: colors.textPrimary,
        }}
      />
      {error ? <Text style={{ color: "#C0392B" }}>{error}</Text> : null}
      <Button title="Save rule" color={accent} onPress={save} disabled={saving} />
    </ScreenContainer>
  );
}
```

- [ ] **Step 4: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 5: Manual verification**

```bash
cd backend && uvicorn app.main:app --reload &
npx expo start
```
Log in, navigate to `/digital-health`. Confirm "No rules yet." and the "Enforcement coming soon" card show. Tap "Add rule", name it, pick two categories, set a daily limit, save, confirm it navigates back and the new rule appears with the right categories and limit. Tap its "Enabled" toggle, confirm it flips to "Disabled". Delete the rule and confirm it disappears.

- [ ] **Step 6: Commit**

```bash
git add src/app/digital-health
git commit -m "$(cat <<'EOF'
Add Focus screens: dashboard, rule builder

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Rebrand to helf

**Files:**
- Modify: `app.json`
- Create: `src/lib/brand.ts`

**Interfaces:**
- Consumes: nothing new.
- Produces: `APP_NAME`, `TAGLINE` from `src/lib/brand.ts` — consumed by the onboarding welcome/recap screens (Task 15, 18).

- [ ] **Step 1: Update `app.json`**

In `app.json`, change `"name": "health_app"` to `"name": "helf"`. Leave `"slug"` and `"scheme"` unchanged (per the spec's open assumption — renaming those could break an EAS project link or OAuth redirect configured outside this repo). Change the splash screen background from the old blue to the new neutral background — in the `expo-splash-screen` plugin config, change `"backgroundColor": "#208AEF"` to `"backgroundColor": "#FBF9F6"`.

- [ ] **Step 2: Add the brand constants**

`src/lib/brand.ts`:
```typescript
export const APP_NAME = "helf";
export const TAGLINE = "Small steps. Every part of you.";
```

- [ ] **Step 3: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Manual verification**

```bash
npx expo start -c
```
(`-c` clears the Metro cache so the `app.json` change is picked up.) Confirm the app still boots with the new splash background color and no crash. The app name itself becomes visible in the OS app switcher / native build name, not inside any screen yet — that's expected until Task 15 renders `APP_NAME`.

- [ ] **Step 5: Commit**

```bash
git add app.json src/lib/brand.ts
git commit -m "$(cat <<'EOF'
Rebrand to helf: app name, splash background, brand constants

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Onboarding answer store

**Files:**
- Create: `src/lib/onboarding-store.ts`
- Package: `@react-native-async-storage/async-storage`

**Interfaces:**
- Consumes: nothing new.
- Produces: `OnboardingAnswers` type; `getPendingAnswers()`, `setPendingAnswer(key, value)`, `clearPendingAnswers()`, `isOnboardingComplete()`, `setOnboardingComplete()`, `getMoveGoalPerWeek()`, `setMoveGoalPerWeek(value)`, `getFuelGoal()`, `setFuelGoal(value)` — consumed by the onboarding screens (Tasks 15, 16, 18) and the routing/dashboard task (Task 19).

- [ ] **Step 1: Install the dependency**

```bash
npx expo install @react-native-async-storage/async-storage
```

- [ ] **Step 2: Write the store**

`src/lib/onboarding-store.ts`:
```typescript
import AsyncStorage from "@react-native-async-storage/async-storage";

export type FuelGoal = "lose" | "maintain" | "build" | "eat_healthier";

export type OnboardingAnswers = {
  moveGoalPerWeek?: number;
  fuelGoal?: FuelGoal;
  mindMoodScore?: number;
  focusCategories?: string[];
};

const PENDING_KEY = "helf.onboarding.pending_answers";
const COMPLETE_KEY = "helf.onboarding.complete";
const MOVE_GOAL_KEY = "helf.onboarding.move_goal_per_week";
const FUEL_GOAL_KEY = "helf.onboarding.fuel_goal";

export async function getPendingAnswers(): Promise<OnboardingAnswers> {
  const raw = await AsyncStorage.getItem(PENDING_KEY);
  return raw ? (JSON.parse(raw) as OnboardingAnswers) : {};
}

export async function setPendingAnswer<K extends keyof OnboardingAnswers>(
  key: K,
  value: OnboardingAnswers[K]
): Promise<void> {
  const current = await getPendingAnswers();
  await AsyncStorage.setItem(PENDING_KEY, JSON.stringify({ ...current, [key]: value }));
}

export async function clearPendingAnswers(): Promise<void> {
  await AsyncStorage.removeItem(PENDING_KEY);
}

export async function isOnboardingComplete(): Promise<boolean> {
  return (await AsyncStorage.getItem(COMPLETE_KEY)) === "true";
}

export async function setOnboardingComplete(): Promise<void> {
  await AsyncStorage.setItem(COMPLETE_KEY, "true");
}

export async function getMoveGoalPerWeek(): Promise<number | null> {
  const raw = await AsyncStorage.getItem(MOVE_GOAL_KEY);
  return raw ? Number(raw) : null;
}

export async function setMoveGoalPerWeek(value: number): Promise<void> {
  await AsyncStorage.setItem(MOVE_GOAL_KEY, String(value));
}

export async function getFuelGoal(): Promise<FuelGoal | null> {
  return (await AsyncStorage.getItem(FUEL_GOAL_KEY)) as FuelGoal | null;
}

export async function setFuelGoal(value: FuelGoal): Promise<void> {
  await AsyncStorage.setItem(FUEL_GOAL_KEY, value);
}
```

- [ ] **Step 3: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors. (Behavioral verification happens end-to-end once the onboarding screens and the register-screen flush exist — Tasks 15–18.)

- [ ] **Step 4: Commit**

```bash
git add src/lib/onboarding-store.ts package.json package-lock.json
git commit -m "$(cat <<'EOF'
Add onboarding answer store backed by AsyncStorage

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 15: Onboarding welcome and pillar carousel

**Files:**
- Create: `src/app/onboarding/_layout.tsx`, `src/app/onboarding/index.tsx`, `src/app/onboarding/pillars.tsx`

**Interfaces:**
- Consumes: `ScreenContainer`, `Button`, `ProgressDots` (`@/components`, Task 2); `useTheme` (`@/lib/theme`, Task 1); `APP_NAME`, `TAGLINE` (`@/lib/brand`, Task 13).
- Produces: `/onboarding`, `/onboarding/pillars` routes — the carousel's "Let's set your goals" CTA links to `/onboarding/goal-move` (Task 16).

Implementation note: the spec describes "swipeable" pillar slides; this implements the same four-slide sequence with a tap-to-advance Next button and a dots indicator instead of horizontal swipe paging — equivalent UX for a 4-item linear intro, and far more reliable to get right without a physical device to tune swipe-paging thresholds on. Revisit if you specifically want swipe gestures.

- [ ] **Step 1: Layout**

`src/app/onboarding/_layout.tsx`:
```tsx
import { Stack } from "expo-router";

export default function OnboardingLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
```

- [ ] **Step 2: Welcome screen**

`src/app/onboarding/index.tsx`:
```tsx
import { useRouter, type Href } from "expo-router";
import { Text } from "react-native";

import { Button, ScreenContainer } from "@/components";
import { APP_NAME, TAGLINE } from "@/lib/brand";
import { useTheme } from "@/lib/theme";

export default function OnboardingWelcomeRoute() {
  const router = useRouter();
  const { colors, font, spacing } = useTheme();

  return (
    <ScreenContainer style={{ justifyContent: "center", alignItems: "center", gap: spacing.lg }}>
      <Text style={{ fontFamily: font.extrabold, fontSize: 40, color: colors.textPrimary }}>{APP_NAME}</Text>
      <Text
        style={{ fontFamily: font.regular, fontSize: 16, color: colors.textSecondary, textAlign: "center" }}
      >
        {TAGLINE}
      </Text>
      <Button title="Get Started" onPress={() => router.push("/onboarding/pillars" as Href)} />
      <Button
        title="Already have an account? Log in"
        variant="text"
        onPress={() => router.push("/login" as Href)}
      />
    </ScreenContainer>
  );
}
```

- [ ] **Step 3: Pillar carousel**

`src/app/onboarding/pillars.tsx`:
```tsx
import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

import { Button, ProgressDots, ScreenContainer } from "@/components";
import { useTheme, type PillarKey } from "@/lib/theme";

const SLIDES: { pillar: PillarKey; copy: string }[] = [
  { pillar: "move", copy: "Log workouts and watch your training add up." },
  { pillar: "fuel", copy: "Track meals without obsessing over every gram." },
  { pillar: "mind", copy: "A daily check-in and a place to write it out." },
  { pillar: "focus", copy: "Set the apps that eat your time — on your terms." },
];

export default function OnboardingPillarsRoute() {
  const router = useRouter();
  const { colors, pillars, mode, font, spacing } = useTheme();
  const [index, setIndex] = useState(0);
  const slide = SLIDES[index];
  const info = pillars[slide.pillar];
  const accent = info[mode];
  const isLast = index === SLIDES.length - 1;

  return (
    <ScreenContainer style={{ justifyContent: "space-between" }}>
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", gap: spacing.lg }}>
        <View
          style={{
            width: 96,
            height: 96,
            borderRadius: 24,
            backgroundColor: accent,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Text style={{ fontSize: 48 }}>{info.icon}</Text>
        </View>
        <Text style={{ fontFamily: font.extrabold, fontSize: 26, color: colors.textPrimary }}>{info.label}</Text>
        <Text
          style={{ fontFamily: font.regular, fontSize: 16, color: colors.textSecondary, textAlign: "center" }}
        >
          {slide.copy}
        </Text>
      </View>

      <ProgressDots count={SLIDES.length} activeIndex={index} color={accent} />
      <Button
        title={isLast ? "Let's set your goals" : "Next"}
        color={accent}
        onPress={() => {
          if (isLast) {
            router.push("/onboarding/goal-move" as Href);
          } else {
            setIndex((i) => i + 1);
          }
        }}
      />
    </ScreenContainer>
  );
}
```

- [ ] **Step 4: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 5: Manual verification**

```bash
npx expo start
```
Navigate to `/onboarding` directly (no route links to it yet — that's Task 19). Confirm the welcome screen shows "helf" and the tagline, "Get Started" moves to the carousel. Tap through all four pillar slides, confirm each shows its icon/color/copy and the dots indicator advances, and the last slide's button reads "Let's set your goals". Confirm "Already have an account? Log in" on the welcome screen navigates to `/login`.

- [ ] **Step 6: Commit**

```bash
git add src/app/onboarding/_layout.tsx src/app/onboarding/index.tsx src/app/onboarding/pillars.tsx
git commit -m "$(cat <<'EOF'
Add onboarding welcome screen and pillar carousel

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 16: Onboarding goal-setting screens (Move, Fuel, Mind, Focus)

**Files:**
- Create: `src/app/onboarding/goal-move.tsx`, `src/app/onboarding/goal-fuel.tsx`, `src/app/onboarding/check-in-mind.tsx`, `src/app/onboarding/goal-focus.tsx`

**Interfaces:**
- Consumes: `ScreenContainer`, `Button`, `Chip` (`@/components`, Task 2); `useTheme` (`@/lib/theme`, Task 1); `setPendingAnswer` (`@/lib/onboarding-store`, Task 14).
- Produces: `/onboarding/goal-move`, `/onboarding/goal-fuel`, `/onboarding/check-in-mind`, `/onboarding/goal-focus` routes, chained in that order, ending at `/onboarding/notifications` (Task 17).

- [ ] **Step 1: Move goal**

`src/app/onboarding/goal-move.tsx`:
```tsx
import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import { Button, ScreenContainer } from "@/components";
import { setPendingAnswer } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";

export default function OnboardingGoalMoveRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.move.light;
  const [goal, setGoal] = useState(3);

  const next = async () => {
    await setPendingAnswer("moveGoalPerWeek", goal);
    router.push("/onboarding/goal-fuel" as Href);
  };

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>
        How many workouts a week are you aiming for?
      </Text>
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.lg }}>
        <Pressable onPress={() => setGoal((g) => Math.max(1, g - 1))}>
          <Text style={{ fontSize: 32, color: accent }}>−</Text>
        </Pressable>
        <Text style={{ fontFamily: font.extrabold, fontSize: 48, color: colors.textPrimary }}>{goal}</Text>
        <Pressable onPress={() => setGoal((g) => Math.min(7, g + 1))}>
          <Text style={{ fontSize: 32, color: accent }}>+</Text>
        </Pressable>
      </View>
      <Button title="Next" color={accent} onPress={next} />
    </ScreenContainer>
  );
}
```

- [ ] **Step 2: Fuel goal**

`src/app/onboarding/goal-fuel.tsx`:
```tsx
import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

import { Button, Chip, ScreenContainer } from "@/components";
import { setPendingAnswer, type FuelGoal } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";

const FUEL_OPTIONS: { value: FuelGoal; label: string }[] = [
  { value: "lose", label: "Lose weight" },
  { value: "maintain", label: "Maintain" },
  { value: "build", label: "Build muscle" },
  { value: "eat_healthier", label: "Eat healthier" },
];

export default function OnboardingGoalFuelRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.fuel.light;
  const [goal, setGoal] = useState<FuelGoal | null>(null);

  const next = async () => {
    if (!goal) return;
    await setPendingAnswer("fuelGoal", goal);
    router.push("/onboarding/check-in-mind" as Href);
  };

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>
        What's your main food goal?
      </Text>
      <View style={{ gap: spacing.sm }}>
        {FUEL_OPTIONS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
            selected={goal === option.value}
            onPress={() => setGoal(option.value)}
            color={accent}
          />
        ))}
      </View>
      <Button title="Next" color={accent} onPress={next} disabled={!goal} />
    </ScreenContainer>
  );
}
```

- [ ] **Step 3: Mind check-in**

`src/app/onboarding/check-in-mind.tsx`:
```tsx
import { useRouter, type Href } from "expo-router";
import { Pressable, Text, View } from "react-native";

import { ScreenContainer } from "@/components";
import { setPendingAnswer } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";

const MOOD_OPTIONS: { score: number; emoji: string; label: string }[] = [
  { score: 1, emoji: "😞", label: "Rough" },
  { score: 2, emoji: "🙁", label: "Low" },
  { score: 3, emoji: "😐", label: "Okay" },
  { score: 4, emoji: "🙂", label: "Good" },
  { score: 5, emoji: "😄", label: "Great" },
];

export default function OnboardingCheckInMindRoute() {
  const router = useRouter();
  const { colors, font, spacing } = useTheme();

  const pick = async (score: number) => {
    await setPendingAnswer("mindMoodScore", score);
    router.push("/onboarding/goal-focus" as Href);
  };

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text
        style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary, textAlign: "center" }}
      >
        How are you feeling right now?
      </Text>
      <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
        {MOOD_OPTIONS.map((option) => (
          <Pressable
            key={option.score}
            onPress={() => pick(option.score)}
            style={{ alignItems: "center", gap: 4 }}
          >
            <Text style={{ fontSize: 32 }}>{option.emoji}</Text>
            <Text style={{ fontFamily: font.regular, fontSize: 12, color: colors.textSecondary }}>
              {option.label}
            </Text>
          </Pressable>
        ))}
      </View>
    </ScreenContainer>
  );
}
```

- [ ] **Step 4: Focus apps**

`src/app/onboarding/goal-focus.tsx`:
```tsx
import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

import { Button, Chip, ScreenContainer } from "@/components";
import { setPendingAnswer } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";

const CATEGORY_OPTIONS = ["Social", "Games", "Video", "News", "Shopping", "Other"];

export default function OnboardingGoalFocusRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.focus.light;
  const [categories, setCategories] = useState<string[]>([]);

  const toggle = (category: string) => {
    setCategories((prev) => (prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]));
  };

  const next = async () => {
    await setPendingAnswer("focusCategories", categories);
    router.push("/onboarding/notifications" as Href);
  };

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>
        Which apps tend to eat your time?
      </Text>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        {CATEGORY_OPTIONS.map((category) => (
          <Chip
            key={category}
            label={category}
            selected={categories.includes(category)}
            onPress={() => toggle(category)}
            color={accent}
          />
        ))}
      </View>
      <Button title="Next" color={accent} onPress={next} disabled={categories.length === 0} />
    </ScreenContainer>
  );
}
```

- [ ] **Step 5: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 6: Manual verification**

```bash
npx expo start
```
Navigate to `/onboarding/goal-move`. Step the counter up/down (clamped 1–7), tap Next. Pick a Fuel goal chip, confirm Next is disabled until one is picked. Tap a Mind mood emoji, confirm it advances immediately (no Next button needed). Pick two Focus categories, confirm Next is disabled with zero picked and enabled with one or more, tap Next and confirm it lands on `/onboarding/notifications` (blank/404 is expected until Task 17 adds that screen).

- [ ] **Step 7: Commit**

```bash
git add src/app/onboarding/goal-move.tsx src/app/onboarding/goal-fuel.tsx src/app/onboarding/check-in-mind.tsx src/app/onboarding/goal-focus.tsx
git commit -m "$(cat <<'EOF'
Add onboarding goal-setting screens for all four pillars

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 17: Notification permission screen with a daily Mind reminder

**Files:**
- Create: `src/app/onboarding/notifications.tsx`
- Modify: `app.json`
- Package: `expo-notifications`

**Interfaces:**
- Consumes: `ScreenContainer`, `Button` (`@/components`, Task 2); `useTheme` (`@/lib/theme`, Task 1).
- Produces: `/onboarding/notifications` route, chained from Task 16's `goal-focus`, continuing to `/onboarding/complete` (Task 18).

- [ ] **Step 1: Install the dependency and add the config plugin**

```bash
npx expo install expo-notifications
```

In `app.json`, add `["expo-notifications", {}]` to the existing `"plugins"` array (alongside `"expo-router"`, `"expo-splash-screen"`, etc.).

- [ ] **Step 2: Write the screen**

`src/app/onboarding/notifications.tsx`:
```tsx
import { useRouter, type Href } from "expo-router";
import * as Notifications from "expo-notifications";
import { Platform, Text } from "react-native";

import { Button, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";

async function scheduleDailyMindReminder() {
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "Default Channel",
      importance: Notifications.AndroidImportance.MAX,
    });
  }
  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== "granted") {
    return;
  }
  await Notifications.scheduleNotificationAsync({
    content: { title: "helf", body: "Time for your Mind check-in." },
    trigger: { type: Notifications.SchedulableTriggerInputTypes.DAILY, hour: 20, minute: 0 },
  });
}

export default function OnboardingNotificationsRoute() {
  const router = useRouter();
  const { colors, font, spacing } = useTheme();

  const next = () => router.push("/onboarding/complete" as Href);

  const enable = async () => {
    try {
      await scheduleDailyMindReminder();
    } catch {
      // best-effort — a denied permission or an unsupported platform (e.g. web) must never block onboarding
    }
    next();
  };

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text
        style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary, textAlign: "center" }}
      >
        Want a nudge for your Mind check-in?
      </Text>
      <Text
        style={{ fontFamily: font.regular, fontSize: 15, color: colors.textSecondary, textAlign: "center" }}
      >
        We'll remind you once a day at 8pm. You can ignore it any time.
      </Text>
      <Button title="Turn on reminders" onPress={enable} />
      <Button title="Not now" variant="text" onPress={next} />
    </ScreenContainer>
  );
}
```

- [ ] **Step 3: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Manual verification**

```bash
npx expo start
```
Navigate to `/onboarding/notifications`. Tap "Turn on reminders", accept the OS permission prompt, confirm it advances to `/onboarding/complete` (blank/404 is expected until Task 18) without crashing. Go back and tap "Not now" instead, confirm it advances the same way with no permission prompt. On web (`npx expo start --web`), confirm tapping "Turn on reminders" doesn't crash the app (notifications aren't supported there — this exercises the catch-and-continue path for real, not just by code reading).

- [ ] **Step 5: Commit**

```bash
git add src/app/onboarding/notifications.tsx app.json package.json package-lock.json
git commit -m "$(cat <<'EOF'
Add onboarding notification permission screen with daily Mind reminder

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 18: Onboarding recap screen and the register-screen data handoff

**Files:**
- Create: `src/app/onboarding/complete.tsx`
- Modify: `src/app/(auth)/register.tsx`

**Interfaces:**
- Consumes: `Button`, `Card`, `ScreenContainer` (`@/components`, Task 2); `useTheme` (`@/lib/theme`, Task 1); `getPendingAnswers`, `clearPendingAnswers`, `setOnboardingComplete`, `setMoveGoalPerWeek`, `setFuelGoal` (`@/lib/onboarding-store`, Task 14); `createMoodEntry` (`@/modules/mental_health/api`, Task 6); `createScreenTimeRule` (`@/modules/digital_health/api`, Task 11); `useAuth` (`@/lib/auth-context`, existing).
- Produces: `/onboarding/complete` route; the register screen now flushes onboarding answers into real data after a successful registration — this is the last task before the routing rewrite (Task 19) wires `/onboarding` into the app's actual entry flow.

- [ ] **Step 1: Recap screen**

`src/app/onboarding/complete.tsx`:
```tsx
import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Text } from "react-native";

import { Button, Card, ScreenContainer } from "@/components";
import { getPendingAnswers, type FuelGoal, type OnboardingAnswers } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";

const FUEL_LABELS: Record<FuelGoal, string> = {
  lose: "Lose weight",
  maintain: "Maintain",
  build: "Build muscle",
  eat_healthier: "Eat healthier",
};

export default function OnboardingCompleteRoute() {
  const router = useRouter();
  const { colors, font, spacing } = useTheme();
  const [answers, setAnswers] = useState<OnboardingAnswers>({});

  useFocusEffect(
    useCallback(() => {
      getPendingAnswers().then(setAnswers);
    }, [])
  );

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>You're all set</Text>
      <Card>
        <Text style={{ color: colors.textPrimary }}>Move: {answers.moveGoalPerWeek ?? "—"} workouts/week</Text>
        <Text style={{ color: colors.textPrimary }}>
          Fuel: {answers.fuelGoal ? FUEL_LABELS[answers.fuelGoal] : "—"}
        </Text>
        <Text style={{ color: colors.textPrimary }}>Mind: check-in logged</Text>
        <Text style={{ color: colors.textPrimary }}>
          Focus: {answers.focusCategories?.length ?? 0} categories picked
        </Text>
      </Card>
      <Button title="Create your account" onPress={() => router.push("/register" as Href)} />
    </ScreenContainer>
  );
}
```

- [ ] **Step 2: Flush onboarding answers on successful registration**

Replace `src/app/(auth)/register.tsx`:
```tsx
import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";

import { Button } from "@/components";
import { useAuth } from "@/lib/auth-context";
import {
  clearPendingAnswers,
  getPendingAnswers,
  setFuelGoal,
  setMoveGoalPerWeek,
  setOnboardingComplete,
} from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";
import { createScreenTimeRule } from "@/modules/digital_health/api";
import { createMoodEntry } from "@/modules/mental_health/api";

async function flushOnboardingAnswers() {
  const answers = await getPendingAnswers();

  if (answers.mindMoodScore) {
    try {
      await createMoodEntry({
        logged_at: new Date().toISOString(),
        mood_score: answers.mindMoodScore,
        tags: [],
      });
    } catch {
      // best-effort — a seed mood entry is a nice-to-have, never worth blocking the hub over
    }
  }

  if (answers.focusCategories && answers.focusCategories.length > 0) {
    try {
      await createScreenTimeRule({
        name: "My first rule",
        apps_or_categories: answers.focusCategories,
        enabled: false,
      });
    } catch {
      // best-effort, same reasoning as above
    }
  }

  if (answers.moveGoalPerWeek) {
    await setMoveGoalPerWeek(answers.moveGoalPerWeek);
  }
  if (answers.fuelGoal) {
    await setFuelGoal(answers.fuelGoal);
  }

  await clearPendingAnswers();
  await setOnboardingComplete();
}

export default function RegisterScreen() {
  const { register } = useAuth();
  const router = useRouter();
  const { colors, font, spacing } = useTheme();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    try {
      await register(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "registration failed");
      return;
    }

    try {
      await flushOnboardingAnswers();
    } catch {
      // best-effort — registration already succeeded; never block reaching the hub over this
    }
    router.replace("/" as Href);
  };

  return (
    <View
      style={{ flex: 1, justifyContent: "center", padding: spacing.xl, gap: spacing.md, backgroundColor: colors.background }}
    >
      <TextInput
        placeholder="Email"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          padding: spacing.md,
          borderRadius: 12,
          fontFamily: font.regular,
          color: colors.textPrimary,
        }}
      />
      <TextInput
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          padding: spacing.md,
          borderRadius: 12,
          fontFamily: font.regular,
          color: colors.textPrimary,
        }}
      />
      {error ? <Text style={{ color: "#C0392B" }}>{error}</Text> : null}
      <Button title="Register" onPress={onSubmit} />
      <Button title="Already have an account? Log in" variant="text" onPress={() => router.push("/login" as Href)} />
    </View>
  );
}
```

Note the two-`try` structure in `onSubmit` is deliberate: a failure in `register()` must show the error and stop (step 1), but a failure in `flushOnboardingAnswers()` must never show an error or block navigation (step 2) — registration already succeeded by that point, and losing a seed mood entry or draft rule is the acceptable best-effort outcome the spec calls for, not a reason to strand a newly-registered user.

- [ ] **Step 3: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Manual verification**

```bash
cd backend && uvicorn app.main:app --reload &
npx expo start
```
Walk the full onboarding flow (`/onboarding` → pillars → all four goal screens → notifications → complete), tap "Create your account", register a new user, and confirm you land on the hub with no error. Then prove the failure-isolation actually holds: stop the backend (`kill %1` or ctrl-C the uvicorn process) right after reaching `/onboarding/complete` but before tapping "Create your account" — tapping it will make `register()` itself fail too (expected, since the backend is down), so instead: restart the backend, repeat onboarding up to `check-in-mind`, then in `src/modules/mental_health/api.ts` temporarily make `createMoodEntry` throw (`throw new Error("test")` as its first line), finish onboarding and register — confirm you still land on the hub with no visible error, then revert that temporary line. This is the concrete version of the Review Focus item about the onboarding-to-data handoff never stranding the user.

- [ ] **Step 5: Commit**

```bash
git add src/app/onboarding/complete.tsx "src/app/(auth)/register.tsx"
git commit -m "$(cat <<'EOF'
Flush onboarding answers into real data on successful registration

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 19: Onboarding-gated routing and the Today dashboard

**Files:**
- Modify: `src/app/index.tsx`

**Interfaces:**
- Consumes: `useAuth` (`@/lib/auth-context`, existing); `isOnboardingComplete`, `getMoveGoalPerWeek` (`@/lib/onboarding-store`, Task 14); `PillarTile`, `ScreenContainer` (`@/components`, Task 2); `useTheme` (`@/lib/theme`, Task 1); `listWorkouts` (`@/modules/training_tracker/api`, existing); `listMoodEntries` (`@/modules/mental_health/api`, Task 6); `listScreenTimeRules` (`@/modules/digital_health/api`, Task 11).
- Produces: the final `/` route — a logged-out, never-onboarded user now lands on `/onboarding` instead of `/login`; a logged-in user sees a four-pillar status dashboard instead of a plain button list.

- [ ] **Step 1: Rebuild the home screen**

Replace `src/app/index.tsx`:
```tsx
import { Redirect, useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Text, View } from "react-native";

import { PillarTile, ScreenContainer } from "@/components";
import { useAuth } from "@/lib/auth-context";
import { getMoveGoalPerWeek, isOnboardingComplete } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";
import { listScreenTimeRules } from "@/modules/digital_health/api";
import { listMoodEntries } from "@/modules/mental_health/api";
import { listWorkouts } from "@/modules/training_tracker/api";

type Statuses = { move: string; fuel: string; mind: string; focus: string };

const INITIAL_STATUSES: Statuses = {
  move: "Loading...",
  fuel: "Log today's meals",
  mind: "Loading...",
  focus: "Loading...",
};

export default function Home() {
  const router = useRouter();
  const { user, isLoading, logout } = useAuth();
  const { colors, font, spacing } = useTheme();
  const [onboardingComplete, setOnboardingComplete] = useState<boolean | null>(null);
  const [statuses, setStatuses] = useState<Statuses>(INITIAL_STATUSES);

  useFocusEffect(
    useCallback(() => {
      if (!user) return;
      (async () => {
        const [workouts, moveGoal, moods, rules] = await Promise.all([
          listWorkouts().catch(() => []),
          getMoveGoalPerWeek(),
          listMoodEntries().catch(() => []),
          listScreenTimeRules().catch(() => []),
        ]);
        const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
        const thisWeek = workouts.filter((w) => new Date(w.started_at).getTime() >= weekAgo).length;
        setStatuses({
          move: moveGoal ? `${thisWeek}/${moveGoal} workouts this week` : `${thisWeek} workouts this week`,
          fuel: "Log today's meals",
          mind:
            moods.length > 0
              ? `Last check-in ${new Date(moods[0].logged_at).toLocaleDateString()}`
              : "No check-ins yet",
          focus: `${rules.filter((r) => r.enabled).length} active rule${rules.filter((r) => r.enabled).length === 1 ? "" : "s"}`,
        });
      })();
    }, [user])
  );

  useFocusEffect(
    useCallback(() => {
      if (user) return;
      isOnboardingComplete().then(setOnboardingComplete);
    }, [user])
  );

  if (isLoading) {
    return null;
  }

  if (!user) {
    if (onboardingComplete === null) {
      return null;
    }
    return <Redirect href={(onboardingComplete ? "/login" : "/onboarding") as Href} />;
  }

  return (
    <ScreenContainer>
      <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>helf</Text>
        <Text onPress={logout} style={{ fontFamily: font.medium, fontSize: 14, color: colors.textSecondary }}>
          Log out
        </Text>
      </View>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.md }}>
        <PillarTile pillar="move" status={statuses.move} onPress={() => router.push("/training-tracker" as Href)} />
        <PillarTile pillar="fuel" status={statuses.fuel} onPress={() => router.push("/meal-tracker" as Href)} />
        <PillarTile pillar="mind" status={statuses.mind} onPress={() => router.push("/mental-health" as Href)} />
        <PillarTile pillar="focus" status={statuses.focus} onPress={() => router.push("/digital-health" as Href)} />
      </View>
    </ScreenContainer>
  );
}
```

- [ ] **Step 2: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 3: Manual verification**

```bash
cd backend && uvicorn app.main:app --reload &
npx expo start -c
```
Three scenarios:
1. Fresh install (clear app data, or a new simulator/web-storage profile): launch, confirm you land on `/onboarding`'s welcome screen, not `/login`.
2. Complete onboarding end-to-end into a new account (per Task 18's verification). Confirm you land on the Today dashboard with four colored tiles, that the Mind tile's status shows today's date (the seeded check-in), and that the Focus tile shows "0 active rules" — the seeded rule is created `enabled: false` by design (it's a draft the user tunes later in the Focus screen), so it should NOT count as active yet.
3. Log out, then relaunch: confirm you now land on `/login` (not `/onboarding` again), since `onboarding_complete` is set. Log back in and confirm the dashboard's tiles still navigate correctly to `/training-tracker`, `/meal-tracker`, `/mental-health`, `/digital-health`, and back.

- [ ] **Step 4: Commit**

```bash
git add src/app/index.tsx
git commit -m "$(cat <<'EOF'
Rebuild the hub as a four-pillar Today dashboard with onboarding gating

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**Spec coverage:** Brand/naming (Task 13), color system + typography + shared components (Tasks 1–2), onboarding flow in full — welcome, carousel, four goal screens, notification permission, recap, register handoff (Tasks 15–18), onboarding routing gate (Task 19), Mind module per the existing approved spec in full — check-in, journal, history, rotating prompts (Tasks 3–4, 6–7), Focus module phase 1 — rules CRUD, no enforcement, "coming soon" messaging (Tasks 8–9, 11–12), Cosmos repositories for both new modules (Tasks 5, 10), hub becomes a tile dashboard (Task 19). All sections of the design spec have a corresponding task.

**Placeholder scan:** No "TBD"/"TODO" markers; every step shows real code or an exact shell command.

**Type consistency:** `PillarKey`/`Pillar`/`useTheme()` (Task 1) are used identically in every component (Task 2) and screen (Tasks 7, 12, 15–19) that references them. `MoodEntry`/`MoodEntryInput` (Task 6) match the backend's `MoodEntryOut`/`MoodEntryCreate` field names exactly (`logged_at`, `mood_score`, `tags`, `note`). `ScreenTimeRule`/`ScreenTimeRuleInput` (Task 11) match `ScreenTimeRuleOut`/`ScreenTimeRuleCreate` (`apps_or_categories`, `daily_limit_minutes`, `enabled`). `OnboardingAnswers` (Task 14) fields (`moveGoalPerWeek`, `fuelGoal`, `mindMoodScore`, `focusCategories`) are the same ones read in Task 18's `flushOnboardingAnswers` and Task 19's dashboard status calculation.

**Review Focus coverage:**
- Force-quit mid-onboarding → AsyncStorage-backed pending answers (Task 14), never React state → covered structurally; not separately re-tested since there's no client test suite, but Task 14's store is the mechanism and Task 18's manual verification exercises a full run through it.
- Reinstall after completing onboarding → Task 19 Step 3's manual verification scenario 3 explicitly checks the "already onboarded → `/login`, not `/onboarding`" path, and Task 15's welcome screen keeps the "Already have an account? Log in" escape hatch as the very first screen.
- Out-of-range `mood_score`/`daily_limit_minutes` → `test_mood_entry_score_out_of_range_is_rejected` (Task 4) and `test_rule_with_non_positive_daily_limit_is_rejected` (Task 9).
- Cross-user ownership on mood/journal/rules → `test_user_cannot_read_or_modify_another_users_mood_entry`, `..._journal_entry` (Task 4), `..._rule` (Task 9).
- Onboarding-to-data handoff failing without stranding the user → the two-`try` structure in Task 18's `onSubmit`, with a manual verification step that forces `createMoodEntry` to throw and confirms the hub is still reached.

