import type { ScreenTimeProvider } from "./types";

/**
 * iOS stub. Real tracking needs the Apple Family Controls (Distribution) entitlement and
 * `react-native-device-activity`; see docs/superpowers/ios-screen-time-setup.md.
 *
 * Until that is approved this reports "unavailable", so the dashboard keeps its
 * "Set up screen-time tracking" state and nothing is synced.
 */

/** iOS only reports usage as threshold events, so durations are known to this granularity. */
export const IOS_THRESHOLD_STEP_MINUTES = 15;

/** What the DeviceActivity extension will write to the shared App Group for the app to read. */
export type IosSharedUsage = {
  /** Local day, `YYYY-MM-DD`. */
  date: string;
  /** Highest threshold event reached today, in minutes (a multiple of IOS_THRESHOLD_STEP_MINUTES). */
  highest_threshold_minutes: number;
};

export const provider: ScreenTimeProvider = {
  pickerMode: "none",
  accuracyNote:
    "iPhone support is coming. Apple has to approve Screen Time access for helf first, and iPhone numbers will be approximate (rounded to 15 minutes).",
  getPermissionState: async () => "unavailable",
  requestPermission: async () => {},
  getDailyUsage: async () => {
    throw new Error("iOS screen-time tracking is not enabled yet");
  },
  listInstalledApps: async () => [],
};
