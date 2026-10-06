import type { MoodEntry } from "@/modules/mental_health/types";
import type { Workout } from "@/modules/training_tracker/types";

import { computeSummary, localDateKey, rangeFor } from "../summary";

const workout = (minutes: number) => ({ duration_s: minutes * 60 }) as Workout;
const mood = (score: number) => ({ mood_score: score }) as MoodEntry;

const base = { workouts: [], moveGoalPerWeek: null, calories: 0, calorieGoal: null, moods: [] };
const ring = (s: ReturnType<typeof computeSummary>, p: string) => s.rings.find((r) => r.pillar === p)!;

describe("rangeFor", () => {
  it("day mode covers a single local day", () => {
    const { start, end, days } = rangeFor(new Date(2026, 9, 7, 15, 30), "day");
    expect(days).toHaveLength(1);
    expect(localDateKey(start)).toBe("2026-10-07");
    expect(localDateKey(end)).toBe("2026-10-08");
  });

  it("week mode starts on Monday and spans 7 days", () => {
    // 2026-10-07 is a Wednesday; 2026-10-04 is a Sunday (belongs to the prior week).
    expect(localDateKey(rangeFor(new Date(2026, 9, 7), "week").start)).toBe("2026-10-05");
    expect(localDateKey(rangeFor(new Date(2026, 9, 4), "week").start)).toBe("2026-09-28");
    const { days, end } = rangeFor(new Date(2026, 9, 7), "week");
    expect(days).toHaveLength(7);
    expect(localDateKey(end)).toBe("2026-10-12");
  });
});

describe("computeSummary", () => {
  it("marks pillars without goals/data as untracked", () => {
    const s = computeSummary({ ...base, mode: "day" });
    expect(ring(s, "move")).toMatchObject({ percent: 0, tracked: false });
    expect(ring(s, "fuel")).toMatchObject({ percent: 0, tracked: false });
    expect(ring(s, "mind")).toMatchObject({ percent: 0, tracked: false });
    expect(ring(s, "focus").tracked).toBe(false);
    expect(s.stats.caloriePercent).toBeNull();
    expect(s.stats.rating).toBeNull();
  });

  it("caps ring percent at 100%", () => {
    const s = computeSummary({
      ...base,
      mode: "day",
      workouts: [workout(300)],
      moveGoalPerWeek: 3,
      calories: 5000,
      calorieGoal: 2000,
    });
    expect(ring(s, "move").percent).toBe(1);
    expect(ring(s, "fuel").percent).toBe(1);
    expect(s.stats.caloriePercent).toBe(250);
  });

  it("scales calorie goal by 7 in week mode", () => {
    const s = computeSummary({ ...base, mode: "week", calories: 7000, calorieGoal: 2000 });
    expect(ring(s, "fuel").percent).toBeCloseTo(0.5);
    expect(s.cards.fuel.caption).toContain("14,000");
  });

  it("week move percent is workouts over weekly goal", () => {
    const s = computeSummary({ ...base, mode: "week", workouts: [workout(30), workout(30)], moveGoalPerWeek: 4 });
    expect(ring(s, "move")).toMatchObject({ percent: 0.5, tracked: true });
    expect(s.cards.move).toMatchObject({ headline: "2/4", caption: "workouts", progress: 0.5 });
  });

  it("averages mood and reports hours", () => {
    const s = computeSummary({ ...base, mode: "day", moods: [mood(4), mood(5)], workouts: [workout(90)] });
    expect(s.stats.rating).toBe(4.5);
    expect(ring(s, "mind")).toMatchObject({ percent: 0.9, tracked: true });
    expect(s.stats.trainingHours).toBe(1.5);
    expect(s.cards.move.details[0]).toEqual({ label: "Time", value: "1h 30m" });
    expect(s.cards.mind.headline).toBe("4.5/5");
  });
});
