import AsyncStorage from "@react-native-async-storage/async-storage";

import { localDateKey } from "@/modules/dashboard/summary";

import { putDailyUsage } from "./api";
import { getExcludedApps } from "./settings";
import { provider } from "./usage";
import type { DailyUsage, ScreenTimeProvider } from "./types";

export const SYNC_INTERVAL_MS = 15 * 60 * 1000;
const LAST_SYNC_KEY = "helf.focus.last_sync";

export type SyncResult = "synced" | "skipped" | "failed";

export type SyncDeps = {
  provider: ScreenTimeProvider;
  getExcluded: () => Promise<string[] | null>;
  put: (usage: DailyUsage) => Promise<unknown>;
  getLastSync: () => Promise<number | null>;
  setLastSync: (ms: number) => Promise<void>;
  now: () => Date;
};

const defaultDeps: SyncDeps = {
  provider,
  getExcluded: getExcludedApps,
  put: putDailyUsage,
  getLastSync: async () => {
    const raw = await AsyncStorage.getItem(LAST_SYNC_KEY);
    const n = raw === null ? NaN : Number(raw);
    return Number.isFinite(n) ? n : null;
  },
  setLastSync: (ms) => AsyncStorage.setItem(LAST_SYNC_KEY, String(ms)),
  now: () => new Date(),
};

/** Keeps what we upload inside the backend's accepted ranges. */
export function sanitizeUsage(usage: DailyUsage): DailyUsage {
  const whole = (n: number) => (Number.isFinite(n) ? Math.max(0, Math.min(1440, Math.round(n))) : 0);
  const total = whole(usage.total_minutes);
  return { date: usage.date, total_minutes: total, dumb_minutes: Math.min(total, whole(usage.dumb_minutes)) };
}

/**
 * Uploads today's daily aggregate (and yesterday's, once per day, so it ends final).
 * At most once per SYNC_INTERVAL_MS unless `force`. Never throws: failures are silent
 * and retried on the next call.
 */
export async function syncScreenTime(options: { force?: boolean } = {}, deps: SyncDeps = defaultDeps): Promise<SyncResult> {
  try {
    if ((await deps.provider.getPermissionState()) !== "granted") return "skipped";

    const now = deps.now();
    const last = await deps.getLastSync();
    if (!options.force && last !== null && now.getTime() - last >= 0 && now.getTime() - last < SYNC_INTERVAL_MS) {
      return "skipped";
    }

    const todayKey = localDateKey(now);
    const dates = [todayKey];
    if (last === null || localDateKey(new Date(last)) !== todayKey) {
      dates.unshift(localDateKey(new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1)));
    }

    const excluded = (await deps.getExcluded()) ?? [];
    for (const date of dates) {
      const usage = await deps.provider.getDailyUsage(date, excluded);
      await deps.put(sanitizeUsage({ ...usage, date }));
    }
    await deps.setLastSync(now.getTime());
    return "synced";
  } catch {
    return "failed";
  }
}
