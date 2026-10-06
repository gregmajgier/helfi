import { computeSummary, formatMinutes } from "../summary";

const base = { workouts: [], moveGoalPerWeek: null, calories: 0, calorieGoal: null, moods: [] };
const focusRing = (s: ReturnType<typeof computeSummary>) => s.rings.find((r) => r.pillar === "focus")!;

describe("formatMinutes", () => {
  it("formats minutes, hours and mixed", () => {
    expect(formatMinutes(0)).toBe("0m");
    expect(formatMinutes(45)).toBe("45m");
    expect(formatMinutes(120)).toBe("2h");
    expect(formatMinutes(80)).toBe("1h 20m");
    expect(formatMinutes(79.6)).toBe("1h 20m");
  });
});

describe("computeSummary focus", () => {
  it("is untracked with a setup prompt when no focus input is given", () => {
    const s = computeSummary({ ...base, mode: "day" });
    expect(focusRing(s)).toEqual({ pillar: "focus", percent: 0, tracked: false });
    expect(s.cards.focus).toMatchObject({ headline: "-", caption: "Set up screen-time tracking", progress: null });
    expect(s.stats.screenTimeHours).toBeNull();
  });

  it("is untracked when permission is not granted", () => {
    for (const permission of ["denied", "unavailable"] as const) {
      const s = computeSummary({
        ...base,
        mode: "day",
        focus: { permission, budget: 120, dumbMinutesByDay: { "2026-10-05": 30 } },
      });
      expect(focusRing(s).tracked).toBe(false);
      expect(s.cards.focus).toMatchObject({ headline: "-", caption: "Set up screen-time tracking", progress: null });
    }
  });

  it("is untracked with a distinct message when permission is granted but no day has data", () => {
    const s = computeSummary({ ...base, mode: "day", focus: { permission: "granted", budget: 120, dumbMinutesByDay: {} } });
    expect(focusRing(s)).toMatchObject({ percent: 0, tracked: false });
    expect(s.cards.focus).toMatchObject({ headline: "-", caption: "No screen-time data yet", progress: null });
    expect(s.stats.screenTimeHours).toBeNull();
  });

  it("shows budget remaining when under budget", () => {
    const s = computeSummary({
      ...base,
      mode: "day",
      focus: { permission: "granted", budget: 120, dumbMinutesByDay: { "2026-10-05": 80 } },
    });
    expect(focusRing(s).tracked).toBe(true);
    expect(focusRing(s).percent).toBeCloseTo(1 / 3);
    expect(s.cards.focus).toMatchObject({ headline: "1h 20m", caption: "of 2h budget" });
    expect(s.stats.screenTimeHours).toBe(1.3);
  });

  it("clamps to 0 when over budget", () => {
    const s = computeSummary({
      ...base,
      mode: "day",
      focus: { permission: "granted", budget: 60, dumbMinutesByDay: { "2026-10-05": 200 } },
    });
    expect(focusRing(s).percent).toBe(0);
    expect(focusRing(s).tracked).toBe(true);
    expect(s.cards.focus).toMatchObject({ headline: "3h 20m", caption: "of 1h budget" });
  });

  it("is a full ring for a day with no dumb-app time", () => {
    const s = computeSummary({
      ...base,
      mode: "day",
      focus: { permission: "granted", budget: 120, dumbMinutesByDay: { "2026-10-05": 0 } },
    });
    expect(focusRing(s).percent).toBe(1);
  });

  it("averages per-day percents in week mode, over days with data only", () => {
    const s = computeSummary({
      ...base,
      mode: "week",
      focus: {
        permission: "granted",
        budget: 100,
        // 100% (0 min), 50% (50 min), 0% (300 min, clamped): mean 0.5. Missing days are ignored.
        dumbMinutesByDay: { "2026-10-05": 0, "2026-10-06": 50, "2026-10-07": 300 },
      },
    });
    expect(focusRing(s).percent).toBeCloseTo(0.5);
    expect(s.cards.focus).toMatchObject({ headline: "1h 57m", caption: "avg of 1h 40m budget" });
    expect(s.stats.screenTimeHours).toBe(5.8);
  });
});
