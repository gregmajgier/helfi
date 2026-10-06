import { localDateKey } from "@/modules/dashboard/summary";

export { localDateKey };

export const todayKey = () => localDateKey(new Date());

/** Parses YYYY-MM-DD as a local date (not UTC), so day maths never shifts at midnight. */
export function parseDay(key: string): Date {
  const [y, m, d] = key.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function addDays(key: string, days: number): string {
  const date = parseDay(key);
  date.setDate(date.getDate() + days);
  return localDateKey(date);
}

export function mondayOf(key: string): string {
  const date = parseDay(key);
  date.setDate(date.getDate() - ((date.getDay() + 6) % 7));
  return localDateKey(date);
}

export function dayLabel(key: string, today = todayKey()): string {
  if (key === today) return "Today";
  if (key === addDays(today, -1)) return "Yesterday";
  if (key === addDays(today, 1)) return "Tomorrow";
  return parseDay(key).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
}

export function shortWeekday(key: string): string {
  return parseDay(key).toLocaleDateString(undefined, { weekday: "short" });
}
