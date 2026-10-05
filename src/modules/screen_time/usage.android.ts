import native from "../../../modules/screen-time";

import { sumForegroundIntervals } from "./foreground";
import type { DailyUsage, ScreenTimeProvider } from "./types";

const DATE_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

export const provider: ScreenTimeProvider = {
  pickerMode: native ? "list" : "none",
  accuracyNote: native
    ? "Exact on Android. Time in apps you mark as productive is left out of your budget."
    : "Screen-time tracking needs the helf app on your phone (a development build), not Expo Go.",

  getPermissionState: async () => {
    if (!native) return "unavailable";
    return native.hasUsageAccess() ? "granted" : "denied";
  },

  requestPermission: async () => {
    native?.openUsageAccessSettings();
  },

  getDailyUsage: async (date, excludedAppIds): Promise<DailyUsage> => {
    const match = DATE_RE.exec(date);
    if (!native || !match) throw new Error("screen-time usage unavailable");
    const [y, m, d] = [Number(match[1]), Number(match[2]), Number(match[3])];
    // Local midnight to local midnight, so DST days are 23 or 25 hours long.
    const windowStart = new Date(y, m - 1, d).getTime();
    const windowEnd = new Date(y, m - 1, d + 1).getTime();
    const now = Date.now();
    if (windowStart >= now) return { date, total_minutes: 0, dumb_minutes: 0 };

    const events = await native.queryForegroundEvents(windowStart, Math.min(windowEnd, now));
    const { totalMinutes, dumbMinutes } = sumForegroundIntervals(events, {
      windowStart,
      windowEnd,
      now,
      ignored: new Set(native.getIgnoredPackages()),
      excluded: new Set(excludedAppIds),
    });
    return { date, total_minutes: totalMinutes, dumb_minutes: dumbMinutes };
  },

  listInstalledApps: async () => (native ? native.listLaunchableApps() : []),
};
