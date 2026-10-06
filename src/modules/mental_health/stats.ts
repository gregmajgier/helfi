import { localDateKey } from "@/modules/dashboard/summary";

import type { MoodEntry } from "./types";

export type DayAggregate = {
  date: string;
  /** Mean mood of that day's check-ins. */
  mood: number;
  energy: number | null;
  stress: number | null;
  sleep: number | null;
  checkIns: number;
  emotions: string[];
  tags: string[];
};

export type TrendPoint = { date: string; value: number | null };
export type Driver = { tag: string; delta: number; days: number };
export type CountItem = { label: string; count: number };

export type MindStats = {
  hasData: boolean;
  checkedInToday: boolean;
  totalCheckIns: number;
  daysLogged: number;
  streak: number;
  longestStreak: number;
  average7: number | null;
  /** Change vs the 7 days before, or null when either window has no data. */
  change7: number | null;
  average30: number | null;
  /** Oldest to newest. */
  moodTrend14: TrendPoint[];
  /** Oldest to newest, 35 days ending today. */
  heatmap: TrendPoint[];
  /** Monday to Sunday. */
  weekday: TrendPoint[];
  /** Check-in counts for scores 1 to 5. */
  distribution: number[];
  energyTrend: TrendPoint[];
  stressTrend: TrendPoint[];
  sleepTrend: TrendPoint[];
  topEmotions: CountItem[];
  drivers: { lifts: Driver[]; drags: Driver[] };
  days: DayAggregate[];
};

const DAY_MS = 86_400_000;
export const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
/** A driver needs this many days with and without the tag before we call it a pattern. */
export const MIN_DRIVER_DAYS = 3;
const MIN_DRIVER_DELTA = 0.3;

const mean = (xs: number[]): number | null => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null);
const present = (xs: (number | null | undefined)[]): number[] => xs.filter((x): x is number => typeof x === "number");

export function addDays(date: Date, n: number): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + n);
}

export function aggregateByDay(entries: MoodEntry[]): DayAggregate[] {
  const groups = new Map<string, MoodEntry[]>();
  for (const e of entries) {
    const when = new Date(e.logged_at);
    if (Number.isNaN(when.getTime())) continue;
    const key = localDateKey(when);
    groups.set(key, [...(groups.get(key) ?? []), e]);
  }
  return [...groups.entries()]
    .map(([date, list]) => ({
      date,
      mood: mean(list.map((e) => e.mood_score)) as number,
      energy: mean(present(list.map((e) => e.energy))),
      stress: mean(present(list.map((e) => e.stress))),
      sleep: mean(present(list.map((e) => e.sleep_quality))),
      checkIns: list.length,
      emotions: [...new Set(list.flatMap((e) => e.emotions ?? []))],
      tags: [...new Set(list.flatMap((e) => e.tags ?? []))],
    }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

/** Consecutive days with a check-in. A streak stays alive until the end of the day after the last check-in. */
export function currentStreak(dates: Set<string>, today: Date): number {
  let cursor = dates.has(localDateKey(today)) ? today : addDays(today, -1);
  let n = 0;
  while (dates.has(localDateKey(cursor))) {
    n += 1;
    cursor = addDays(cursor, -1);
  }
  return n;
}

export function longestStreak(dates: Set<string>): number {
  let best = 0;
  let run = 0;
  let prev: number | null = null;
  for (const key of [...dates].sort()) {
    const [y, m, d] = key.split("-").map(Number);
    const t = Date.UTC(y, m - 1, d);
    run = prev !== null && t - prev === DAY_MS ? run + 1 : 1;
    prev = t;
    best = Math.max(best, run);
  }
  return best;
}

/** `length` days ending on `today`, oldest first, null where the day has no value. */
export function windowOf(
  byDate: Map<string, DayAggregate>,
  today: Date,
  length: number,
  pick: (d: DayAggregate) => number | null
): TrendPoint[] {
  return Array.from({ length }, (_, i) => {
    const key = localDateKey(addDays(today, i - (length - 1)));
    const day = byDate.get(key);
    return { date: key, value: day ? pick(day) : null };
  });
}

/** Mood on days with a factor versus days without it. Needs enough days on both sides to mean anything. */
export function computeDrivers(days: DayAggregate[]): { lifts: Driver[]; drags: Driver[] } {
  const tags = new Set(days.flatMap((d) => d.tags));
  const all: Driver[] = [];
  for (const tag of tags) {
    const withTag = days.filter((d) => d.tags.includes(tag));
    const without = days.filter((d) => !d.tags.includes(tag));
    if (withTag.length < MIN_DRIVER_DAYS || without.length < MIN_DRIVER_DAYS) continue;
    const delta = (mean(withTag.map((d) => d.mood)) as number) - (mean(without.map((d) => d.mood)) as number);
    all.push({ tag, delta, days: withTag.length });
  }
  return {
    lifts: all.filter((d) => d.delta >= MIN_DRIVER_DELTA).sort((a, b) => b.delta - a.delta).slice(0, 3),
    drags: all.filter((d) => d.delta <= -MIN_DRIVER_DELTA).sort((a, b) => a.delta - b.delta).slice(0, 3),
  };
}

export function computeMindStats(entries: MoodEntry[], today: Date = new Date()): MindStats {
  const days = aggregateByDay(entries);
  const byDate = new Map(days.map((d) => [d.date, d]));
  const dates = new Set(days.map((d) => d.date));

  const moodWindow = (length: number, offset = 0) =>
    present(windowOf(byDate, addDays(today, -offset), length, (d) => d.mood).map((p) => p.value));
  const avg7 = mean(moodWindow(7));
  const prev7 = mean(moodWindow(7, 7));

  const weekdayBuckets: number[][] = WEEKDAY_LABELS.map(() => []);
  for (const d of days) {
    const [y, m, dd] = d.date.split("-").map(Number);
    const jsDay = new Date(y, m - 1, dd).getDay(); // 0 = Sunday
    weekdayBuckets[(jsDay + 6) % 7].push(d.mood);
  }

  const distribution = [0, 0, 0, 0, 0];
  const emotionCounts = new Map<string, number>();
  for (const e of entries) {
    if (e.mood_score >= 1 && e.mood_score <= 5) distribution[e.mood_score - 1] += 1;
    for (const em of e.emotions ?? []) emotionCounts.set(em, (emotionCounts.get(em) ?? 0) + 1);
  }

  return {
    hasData: days.length > 0,
    checkedInToday: dates.has(localDateKey(today)),
    totalCheckIns: entries.length,
    daysLogged: days.length,
    streak: currentStreak(dates, today),
    longestStreak: longestStreak(dates),
    average7: avg7,
    change7: avg7 !== null && prev7 !== null ? avg7 - prev7 : null,
    average30: mean(moodWindow(30)),
    moodTrend14: windowOf(byDate, today, 14, (d) => d.mood),
    heatmap: windowOf(byDate, today, 35, (d) => d.mood),
    weekday: WEEKDAY_LABELS.map((label, i) => ({ date: label, value: mean(weekdayBuckets[i]) })),
    distribution,
    energyTrend: windowOf(byDate, today, 14, (d) => d.energy),
    stressTrend: windowOf(byDate, today, 14, (d) => d.stress),
    sleepTrend: windowOf(byDate, today, 14, (d) => d.sleep),
    topEmotions: [...emotionCounts.entries()]
      .map(([label, count]) => ({ label, count }))
      .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label))
      .slice(0, 6),
    drivers: computeDrivers(days),
    days,
  };
}
