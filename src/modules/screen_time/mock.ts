import type { DailyUsage, InstalledApp, PermissionState, ScreenTimeProvider } from "./types";

/** In-memory provider for jest and for previewing the UI without a native build. */
export function createMockProvider(
  options: {
    permission?: PermissionState;
    usageByDate?: Record<string, { total: number; dumb: number }>;
    apps?: InstalledApp[];
  } = {}
): ScreenTimeProvider & { permission: PermissionState } {
  const state = { permission: options.permission ?? "granted" };
  return {
    get permission() {
      return state.permission;
    },
    pickerMode: "list",
    accuracyNote: "Mock data.",
    getPermissionState: async () => state.permission,
    requestPermission: async () => {
      state.permission = "granted";
    },
    getDailyUsage: async (date: string): Promise<DailyUsage> => {
      const u = options.usageByDate?.[date];
      return { date, total_minutes: u?.total ?? 0, dumb_minutes: u?.dumb ?? 0 };
    },
    listInstalledApps: async () => options.apps ?? [],
  };
}
