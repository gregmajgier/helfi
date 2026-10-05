/**
 * Pure interval summing for Android `UsageStatsManager.queryEvents`.
 *
 * The native module returns raw events; all the logic lives here so it is covered by jest
 * (no JDK or device needed). Event codes are the `UsageEvents.Event` constants.
 */
export const EVENT = {
  /** MOVE_TO_FOREGROUND / ACTIVITY_RESUMED */
  FOREGROUND: 1,
  /** MOVE_TO_BACKGROUND / ACTIVITY_PAUSED */
  BACKGROUND: 2,
  /** ACTIVITY_STOPPED */
  STOPPED: 23,
  /** SCREEN_NON_INTERACTIVE */
  SCREEN_OFF: 16,
  /** DEVICE_SHUTDOWN */
  SHUTDOWN: 26,
} as const;

export type UsageEventRecord = {
  /** Package name; empty for screen and device events. */
  p: string;
  /** `EVENT` code. */
  t: number;
  /** Epoch milliseconds. */
  ts: number;
};

export type SumOptions = {
  windowStart: number;
  windowEnd: number;
  /** An interval still open at the end of the data is closed at min(windowEnd, now). */
  now: number;
  /** Launcher, system UI and helf itself: never counted, not even in the total. */
  ignored?: ReadonlySet<string>;
  /** Productive apps: counted in `totalMinutes` but not in `dumbMinutes`. */
  excluded?: ReadonlySet<string>;
};

export type SumResult = { totalMinutes: number; dumbMinutes: number };

export function sumForegroundIntervals(rawEvents: UsageEventRecord[], options: SumOptions): SumResult {
  const { windowStart, windowEnd, now, ignored = new Set<string>(), excluded = new Set<string>() } = options;
  const events = rawEvents
    .filter((e) => Number.isFinite(e.ts) && e.ts >= windowStart && e.ts < windowEnd)
    .sort((a, b) => a.ts - b.ts);

  let totalMs = 0;
  let dumbMs = 0;
  let open: { pkg: string; start: number } | null = null;

  const close = (end: number) => {
    if (!open) return;
    const ms = Math.max(0, Math.min(end, windowEnd) - Math.max(open.start, windowStart));
    if (!ignored.has(open.pkg)) {
      totalMs += ms;
      if (!excluded.has(open.pkg)) dumbMs += ms;
    }
    open = null;
  };

  events.forEach((e, index) => {
    switch (e.t) {
      case EVENT.FOREGROUND:
        if (open?.pkg === e.p) break; // another activity of the same app: keep the original start
        close(e.ts); // switching apps without an explicit background event
        open = { pkg: e.p, start: e.ts };
        break;
      case EVENT.BACKGROUND:
      case EVENT.STOPPED:
        if (open?.pkg === e.p) close(e.ts);
        // The very first event being a background means the app was already open at the window start.
        else if (open === null && index === 0 && e.t === EVENT.BACKGROUND) {
          open = { pkg: e.p, start: windowStart };
          close(e.ts);
        }
        break;
      case EVENT.SCREEN_OFF:
      case EVENT.SHUTDOWN:
        close(e.ts);
        break;
    }
  });
  close(Math.min(windowEnd, now));

  return { totalMinutes: Math.round(totalMs / 60_000), dumbMinutes: Math.round(dumbMs / 60_000) };
}
