import { requireOptionalNativeModule } from "expo";

export type NativeUsageEvent = {
  /** Package name; empty for screen and device events. */
  p: string;
  /** `UsageEvents.Event` code. */
  t: number;
  /** Epoch milliseconds. */
  ts: number;
};

export type NativeLaunchableApp = {
  id: string;
  label: string;
  category: string | null;
};

export interface ScreenTimeNativeModule {
  hasUsageAccess(): boolean;
  openUsageAccessSettings(): void;
  queryForegroundEvents(startMs: number, endMs: number): Promise<NativeUsageEvent[]>;
  listLaunchableApps(): Promise<NativeLaunchableApp[]>;
  getIgnoredPackages(): string[];
}

/** Null when the app was not built with this module (Expo Go, web, iOS). */
export default requireOptionalNativeModule<ScreenTimeNativeModule>("ScreenTime");
