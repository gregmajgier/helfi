import type { ScreenTimeProvider } from "./types";

/**
 * Fallback provider used on web and anywhere a native implementation is missing.
 * Platform files (`usage.android.ts`, `usage.ios.ts`) replace this one at bundle time.
 */
export const provider: ScreenTimeProvider = {
  pickerMode: "none",
  accuracyNote: "Screen-time tracking needs the helf app on your phone (a development build).",
  getPermissionState: async () => "unavailable",
  requestPermission: async () => {},
  getDailyUsage: async (date) => ({ date, total_minutes: 0, dumb_minutes: 0 }),
  listInstalledApps: async () => [],
};
