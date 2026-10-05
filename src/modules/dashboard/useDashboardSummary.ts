import { useCallback, useEffect, useState } from "react";

import { getDailyCalorieGoal, getMoveGoalPerWeek } from "@/lib/onboarding-store";
import { listEntriesForDay } from "@/modules/meal_tracker/api";
import { listMoodEntries } from "@/modules/mental_health/api";
import { listDailyUsage } from "@/modules/screen_time/api";
import { getExcludedApps, getFocusBudget, screenTime } from "@/modules/screen_time";
import { listWorkouts } from "@/modules/training_tracker/api";

import { computeSummary, localDateKey, rangeFor, type FocusInput } from "./summary";
import type { DashboardSummary, ViewMode } from "./types";

/** Today comes from the device (always fresh); past days come from what the backend has synced. */
async function loadFocus(days: Date[]): Promise<FocusInput> {
  const [permission, budget] = await Promise.all([
    screenTime.getPermissionState().catch(() => "unavailable" as const),
    getFocusBudget().catch(() => 120),
  ]);
  const dumbMinutesByDay: Record<string, number> = {};
  if (permission !== "granted") return { permission, budget, dumbMinutesByDay };

  const keys = days.map(localDateKey);
  const todayKey = localDateKey(new Date());
  const past = keys.filter((k) => k < todayKey);
  if (past.length > 0) {
    const rows = await listDailyUsage(past[0], past[past.length - 1]).catch(() => []);
    for (const row of rows) if (past.includes(row.date)) dumbMinutesByDay[row.date] = row.dumb_minutes;
  }
  if (keys.includes(todayKey)) {
    const excluded = (await getExcludedApps().catch(() => null)) ?? [];
    const usage = await screenTime.getDailyUsage(todayKey, excluded).catch(() => null);
    if (usage) dumbMinutesByDay[todayKey] = usage.dumb_minutes;
  }
  return { permission, budget, dumbMinutesByDay };
}

export function useDashboardSummary(anchor: Date, mode: ViewMode, enabled: boolean) {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const key = localDateKey(anchor);

  const reload = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    const { start, end, days } = rangeFor(new Date(`${key}T12:00:00`), mode);
    const [allWorkouts, moveGoal, calorieGoal, moods, dayEntries, focus] = await Promise.all([
      listWorkouts().catch(() => []),
      getMoveGoalPerWeek().catch(() => null),
      getDailyCalorieGoal().catch(() => null),
      listMoodEntries(start.toISOString(), end.toISOString()).catch(() => []),
      Promise.all(days.map((d) => listEntriesForDay(localDateKey(d)).catch(() => []))),
      loadFocus(days),
    ]);
    const inRange = (iso: string) => {
      const t = new Date(iso).getTime();
      return t >= start.getTime() && t < end.getTime();
    };
    setSummary(
      computeSummary({
        mode,
        workouts: allWorkouts.filter((w) => inRange(w.started_at)),
        moveGoalPerWeek: moveGoal,
        calories: dayEntries.flat().reduce((sum, e) => sum + e.calories, 0),
        calorieGoal,
        moods: moods.filter((m) => inRange(m.logged_at)),
        focus,
      })
    );
    setLoading(false);
  }, [key, mode, enabled]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch on mount/param change; reload() sets loading state
    reload();
  }, [reload]);

  return { summary, loading, reload };
}
