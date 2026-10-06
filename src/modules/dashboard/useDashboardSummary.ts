import { useCallback, useEffect, useState } from "react";

import { getDailyCalorieGoal, getMoveGoalPerWeek } from "@/lib/onboarding-store";
import { listEntriesForDay } from "@/modules/meal_tracker/api";
import { listMoodEntries } from "@/modules/mental_health/api";
import { listWorkouts } from "@/modules/training_tracker/api";

import { computeSummary, localDateKey, rangeFor } from "./summary";
import type { DashboardSummary, ViewMode } from "./types";

export function useDashboardSummary(anchor: Date, mode: ViewMode, enabled: boolean) {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const key = localDateKey(anchor);

  const reload = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    const { start, end, days } = rangeFor(new Date(`${key}T12:00:00`), mode);
    const [allWorkouts, moveGoal, calorieGoal, moods, dayEntries] = await Promise.all([
      listWorkouts().catch(() => []),
      getMoveGoalPerWeek().catch(() => null),
      getDailyCalorieGoal().catch(() => null),
      listMoodEntries(start.toISOString(), end.toISOString()).catch(() => []),
      Promise.all(days.map((d) => listEntriesForDay(localDateKey(d)).catch(() => []))),
    ]);
    const inRange = (iso: string) => {
      const t = new Date(iso).getTime();
      return t >= start.getTime() && t < end.getTime();
    };
    const meals = dayEntries.flat();
    const sumOf = (pick: (e: (typeof meals)[number]) => number) => meals.reduce((sum, e) => sum + pick(e), 0);
    setSummary(
      computeSummary({
        mode,
        workouts: allWorkouts.filter((w) => inRange(w.started_at)),
        moveGoalPerWeek: moveGoal,
        calories: sumOf((e) => e.calories),
        macros: { protein_g: sumOf((e) => e.protein_g), carbs_g: sumOf((e) => e.carbs_g), fat_g: sumOf((e) => e.fat_g) },
        calorieGoal,
        moods: moods.filter((m) => inRange(m.logged_at)),
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
