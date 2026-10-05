export type DailyUsage = { date: string; total_minutes: number; dumb_minutes: number };

export type PermissionState = "granted" | "denied" | "unavailable";

export type InstalledApp = {
  /** Android package name. Never uploaded; the excluded set stays on the device. */
  id: string;
  label: string;
  /** ApplicationInfo.category name (e.g. "productivity"), or null when the app has none. */
  category: string | null;
};

/** How the user picks productive (excluded) apps on this platform. */
export type ExcludedPickerMode = "list" | "system" | "none";

export interface ScreenTimeProvider {
  readonly pickerMode: ExcludedPickerMode;
  /** Shown in the UI so the user knows how precise the numbers are. */
  readonly accuracyNote: string;
  getPermissionState(): Promise<PermissionState>;
  /** Opens the system flow that grants access. Resolves once it has been launched. */
  requestPermission(): Promise<void>;
  /** Minutes of foreground use on a local day (`YYYY-MM-DD`), with excluded apps removed from `dumb_minutes`. */
  getDailyUsage(date: string, excludedAppIds: string[]): Promise<DailyUsage>;
  listInstalledApps(): Promise<InstalledApp[]>;
}
