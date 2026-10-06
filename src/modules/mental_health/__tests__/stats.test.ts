import { addDays, computeMindStats, currentStreak, longestStreak } from "../stats";
import type { MoodEntry } from "../types";

const TODAY = new Date(2026, 9, 6, 12); // Tue 6 Oct 2026, local
let id = 0;

function entry(daysAgo: number, mood: number, extra: Partial<MoodEntry> = {}): MoodEntry {
  const d = addDays(TODAY, -daysAgo);
  d.setHours(9, 0, 0, 0);
  return { id: String(id++), user_id: "u", logged_at: d.toISOString(), mood_score: mood, tags: [], created_at: "", updated_at: "", ...extra };
}

const keys = (...daysAgo: number[]) =>
  new Set(
    daysAgo.map((n) => {
      const d = addDays(TODAY, -n);
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    })
  );

describe("streaks", () => {
  it("counts consecutive days ending today", () => expect(currentStreak(keys(0, 1, 2), TODAY)).toBe(3));
  it("stays alive when only yesterday is logged", () => expect(currentStreak(keys(1, 2), TODAY)).toBe(2));
  it("is zero after a missed day", () => expect(currentStreak(keys(2, 3), TODAY)).toBe(0));
  it("finds the longest run", () => expect(longestStreak(keys(0, 1, 5, 6, 7, 8, 12))).toBe(4));
  it("handles empty", () => {
    expect(currentStreak(new Set(), TODAY)).toBe(0);
    expect(longestStreak(new Set())).toBe(0);
  });
});

describe("computeMindStats", () => {
  it("reports no data for no entries", () => {
    const s = computeMindStats([], TODAY);
    expect(s.hasData).toBe(false);
    expect(s.average7).toBeNull();
    expect(s.moodTrend14).toHaveLength(14);
    expect(s.heatmap).toHaveLength(35);
    expect(s.weekday.every((w) => w.value === null)).toBe(true);
  });

  it("averages several check-ins on one day", () => {
    const s = computeMindStats([entry(0, 2), entry(0, 4)], TODAY);
    expect(s.daysLogged).toBe(1);
    expect(s.totalCheckIns).toBe(2);
    expect(s.moodTrend14[13].value).toBe(3);
    expect(s.checkedInToday).toBe(true);
  });

  it("computes the 7-day average and change vs the previous week", () => {
    const s = computeMindStats([entry(0, 4), entry(1, 4), entry(8, 2), entry(9, 2)], TODAY);
    expect(s.average7).toBe(4);
    expect(s.change7).toBe(2);
  });

  it("has no change when the previous week is empty", () => {
    expect(computeMindStats([entry(0, 4)], TODAY).change7).toBeNull();
  });

  it("buckets weekdays Monday-first", () => {
    // TODAY is a Tuesday, index 1.
    const s = computeMindStats([entry(0, 5), entry(7, 3)], TODAY);
    expect(s.weekday[1].value).toBe(4);
    expect(s.weekday[0].value).toBeNull();
  });

  it("builds the mood distribution and top emotions", () => {
    const s = computeMindStats(
      [entry(0, 5, { emotions: ["calm", "happy"] }), entry(1, 5, { emotions: ["calm"] }), entry(2, 1, { emotions: ["anxious"] })],
      TODAY
    );
    expect(s.distribution).toEqual([1, 0, 0, 0, 2]);
    expect(s.topEmotions[0]).toEqual({ label: "calm", count: 2 });
  });

  it("tracks energy, stress and sleep only where present", () => {
    const s = computeMindStats([entry(0, 3, { energy: 4, stress: 2, sleep_quality: 5 }), entry(1, 3)], TODAY);
    expect(s.energyTrend[13].value).toBe(4);
    expect(s.energyTrend[12].value).toBeNull();
    expect(s.sleepTrend[13].value).toBe(5);
  });

  it("ignores entries with unparseable dates", () => {
    expect(computeMindStats([{ ...entry(0, 3), logged_at: "nope" }], TODAY).hasData).toBe(false);
  });
});

describe("drivers", () => {
  const tagged = (n: number, mood: number, tag: string) => entry(n, mood, { tags: [tag] });

  it("finds what lifts and drags mood, with enough days on both sides", () => {
    const entries = [
      tagged(0, 5, "exercise"), tagged(1, 5, "exercise"), tagged(2, 4, "exercise"),
      tagged(3, 2, "poor sleep"), tagged(4, 2, "poor sleep"), tagged(5, 1, "poor sleep"),
      entry(6, 3), entry(7, 3), entry(8, 3),
    ];
    const { lifts, drags } = computeMindStats(entries, TODAY).drivers;
    expect(lifts[0].tag).toBe("exercise");
    expect(lifts[0].delta).toBeGreaterThan(0.3);
    expect(drags[0].tag).toBe("poor sleep");
  });

  it("stays quiet with too little data", () => {
    const { lifts, drags } = computeMindStats([tagged(0, 5, "exercise"), entry(1, 3), entry(2, 3)], TODAY).drivers;
    expect(lifts).toEqual([]);
    expect(drags).toEqual([]);
  });
});
