import type { MoodEntry } from "@/modules/mental_health/types";
import type { PermissionState } from "@/modules/screen_time/types";
import type { Workout } from "@/modules/training_tracker/types";

import type { DashboardSummary, ViewMode } from "./types";

export const ASSUMED_SESSION_MINUTES = 45;

export function localDateKey(d: Date): string {
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

export function rangeFor(anchor: Date, mode: ViewMode): { start: Date; end: Date; days: Date[] } {
  const start = new Date(anchor.getFullYear(), anchor.getMonth(), anchor.getDate());
  if (mode === "week") start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
  const count = mode === "week" ? 7 : 1;
  const days = Array.from({ length: count }, (_, i) => new Date(start.getFullYear(), start.getMonth(), start.getDate() + i));
  const end = new Date(start.getFullYear(), start.getMonth(), start.getDate() + count);
  return { start, end, days };
}

function formatDuration(minutes: number): string {
  const total = Math.round(minutes);
  const h = Math.floor(total / 60);
  const m = total % 60;
  return h ? `${h}h ${m}m` : `${m}m`;
}

const clamp01 = (n: number) => Math.max(0, Math.min(1, n));

export function formatMinutes(total: number): string {
  const m = Math.max(0, Math.round(total));
  const h = Math.floor(m / 60);
  const rest = m % 60;
  if (h === 0) return `${rest}m`;
  return rest === 0 ? `${h}h` : `${h}h ${rest}m`;
}

/** Screen-time inputs for the range. `dumbMinutesByDay` only holds days that have data. */
export type FocusInput = {
  permission: PermissionState;
  budget: number;
  dumbMinutesByDay: Record<string, number>;
};

export function computeFocus(focus: FocusInput | undefined, mode: ViewMode) {
  const values = focus ? Object.values(focus.dumbMinutesByDay) : [];
  const granted = focus?.permission === "granted" && focus.budget > 0;
  if (!focus || !granted) {
    return { percent: 0, tracked: false, hours: null, headline: "-", caption: "Set up screen-time tracking" };
  }
  if (values.length === 0) {
    return { percent: 0, tracked: false, hours: null, headline: "-", caption: "No screen-time data yet" };
  }
  const total = values.reduce((a, b) => a + b, 0);
  const percent = values.reduce((sum, v) => sum + clamp01(1 - v / focus.budget), 0) / values.length;
  const shown = mode === "week" ? total / values.length : total;
  return {
    percent,
    tracked: true,
    hours: Math.round((total / 60) * 10) / 10,
    headline: formatMinutes(shown),
    caption: `${mode === "week" ? "avg " : ""}of ${formatMinutes(focus.budget)} budget`,
  };
}

export type SummaryInput = {
  mode: ViewMode;
  workouts: Workout[];
  moveGoalPerWeek: number | null;
  calories: number;
  calorieGoal: number | null;
  macros?: { protein_g: number; carbs_g: number; fat_g: number };
  moods: MoodEntry[];
  focus?: FocusInput;
};

export function computeSummary(input: SummaryInput): DashboardSummary {
  const { mode, workouts, moveGoalPerWeek, calories, calorieGoal, moods, focus, macros = { protein_g: 0, carbs_g: 0, fat_g: 0 } } = input;
  const focusResult = computeFocus(focus, mode);
  const minutes = workouts.reduce((sum, w) => sum + w.duration_s / 60, 0);
  const distanceM = workouts.reduce((sum, w) => sum + (w.distance_m ?? 0), 0);
  const days = mode === "week" ? 7 : 1;

  let movePercent = 0;
  if (moveGoalPerWeek) {
    movePercent =
      mode === "week"
        ? workouts.length / moveGoalPerWeek
        : minutes / ((moveGoalPerWeek * ASSUMED_SESSION_MINUTES) / 7);
  }

  const fuelPercent = calorieGoal ? calories / (calorieGoal * days) : 0;
  const rating = moods.length ? moods.reduce((s, m) => s + m.mood_score, 0) / moods.length : null;

  const period = mode === "week" ? "this week" : "today";
  return {
    rings: [
      { pillar: "move", percent: clamp01(movePercent), tracked: moveGoalPerWeek !== null },
      { pillar: "fuel", percent: clamp01(fuelPercent), tracked: calorieGoal !== null },
      { pillar: "mind", percent: rating === null ? 0 : clamp01(rating / 5), tracked: rating !== null },
      { pillar: "focus", percent: focusResult.percent, tracked: focusResult.tracked },
    ],
    stats: {
      caloriePercent: calorieGoal ? Math.round((calories / (calorieGoal * days)) * 100) : null,
      trainingHours: Math.round((minutes / 60) * 10) / 10,
      rating: rating === null ? null : Math.round(rating * 10) / 10,
      screenTimeHours: focusResult.hours,
    },
    cards: {
      move: {
        headline: mode === "week" && moveGoalPerWeek ? `${workouts.length}/${moveGoalPerWeek}` : String(workouts.length),
        caption: workouts.length === 1 && !(mode === "week" && moveGoalPerWeek) ? "workout" : "workouts",
        progress: moveGoalPerWeek ? clamp01(movePercent) : null,
        details: [
          { label: "Time", value: formatDuration(minutes) },
          { label: "Distance", value: `${Math.round((distanceM / 1000) * 10) / 10} km` },
        ],
      },
      fuel: {
        headline: Math.round(calories).toLocaleString(),
        caption: calorieGoal ? `/ ${(calorieGoal * days).toLocaleString()} kcal` : `kcal ${period}`,
        progress: calorieGoal ? clamp01(fuelPercent) : null,
        details: [
          { label: "Protein", value: `${Math.round(macros.protein_g)}g` },
          { label: "Carbs", value: `${Math.round(macros.carbs_g)}g` },
          { label: "Fat", value: `${Math.round(macros.fat_g)}g` },
        ],
      },
      mind: {
        headline: rating === null ? "-" : `${Math.round(rating * 10) / 10}/5`,
        caption: moods.length ? `avg mood \u00b7 ${moods.length} check-in${moods.length === 1 ? "" : "s"}` : "No check-ins yet",
        progress: rating === null ? null : clamp01(rating / 5),
        details: [],
      },
      focus: {
        headline: focusResult.headline,
        caption: focusResult.caption,
        progress: focusResult.tracked ? focusResult.percent : null,
        details: [],
      },
    },
  };
}
