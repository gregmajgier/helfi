import { createMockProvider } from "../mock";
import { SYNC_INTERVAL_MS, sanitizeUsage, syncScreenTime, type SyncDeps } from "../sync";
import type { DailyUsage } from "../types";

jest.mock("@react-native-async-storage/async-storage", () =>
  jest.requireActual("@react-native-async-storage/async-storage/jest/async-storage-mock")
);
jest.mock("expo-secure-store", () => ({}));

function makeDeps(overrides: Partial<SyncDeps> = {}) {
  const puts: DailyUsage[] = [];
  let last: number | null = null;
  const deps: SyncDeps = {
    provider: createMockProvider({
      usageByDate: { "2026-10-04": { total: 300, dumb: 100 }, "2026-10-05": { total: 200, dumb: 50 } },
    }),
    getExcluded: async () => ["com.productive"],
    put: async (u) => {
      puts.push(u);
    },
    getLastSync: async () => last,
    setLastSync: async (ms) => {
      last = ms;
    },
    now: () => new Date(2026, 9, 5, 12, 0),
    ...overrides,
  };
  return { deps, puts, getLast: () => last };
}

describe("syncScreenTime", () => {
  it("uploads yesterday and today on the first sync", async () => {
    const { deps, puts } = makeDeps();
    expect(await syncScreenTime({}, deps)).toBe("synced");
    expect(puts.map((p) => [p.date, p.total_minutes, p.dumb_minutes])).toEqual([
      ["2026-10-04", 300, 100],
      ["2026-10-05", 200, 50],
    ]);
  });

  it("skips when permission is not granted", async () => {
    const { deps, puts } = makeDeps({ provider: createMockProvider({ permission: "denied" }) });
    expect(await syncScreenTime({}, deps)).toBe("skipped");
    expect(puts).toHaveLength(0);
  });

  it("throttles to once per interval, and force overrides", async () => {
    const { deps, puts } = makeDeps();
    await syncScreenTime({}, deps);
    puts.length = 0;
    expect(await syncScreenTime({}, deps)).toBe("skipped");
    expect(puts).toHaveLength(0);
    expect(await syncScreenTime({ force: true }, deps)).toBe("synced");
    expect(puts.map((p) => p.date)).toEqual(["2026-10-05"]);
  });

  it("syncs again after the interval has passed", async () => {
    let now = new Date(2026, 9, 5, 12, 0);
    const { deps, puts } = makeDeps({ now: () => now });
    await syncScreenTime({}, deps);
    puts.length = 0;
    now = new Date(now.getTime() + SYNC_INTERVAL_MS);
    expect(await syncScreenTime({}, deps)).toBe("synced");
    expect(puts.map((p) => p.date)).toEqual(["2026-10-05"]);
  });

  it("includes yesterday again on the first sync of a new day", async () => {
    let now = new Date(2026, 9, 5, 23, 50);
    const { deps, puts } = makeDeps({ now: () => now });
    await syncScreenTime({}, deps);
    puts.length = 0;
    now = new Date(2026, 9, 6, 8, 0);
    await syncScreenTime({}, deps);
    expect(puts.map((p) => p.date)).toEqual(["2026-10-05", "2026-10-06"]);
  });

  it("is silent on failure and does not record a sync, so it retries", async () => {
    const { deps, getLast } = makeDeps({
      put: async () => {
        throw new Error("network");
      },
    });
    expect(await syncScreenTime({}, deps)).toBe("failed");
    expect(getLast()).toBeNull();
  });

  it("passes the excluded apps to the provider", async () => {
    const getDailyUsage = jest.fn(async (date: string) => ({ date, total_minutes: 1, dumb_minutes: 1 }));
    const { deps } = makeDeps({ provider: { ...createMockProvider(), getDailyUsage } });
    await syncScreenTime({}, deps);
    expect(getDailyUsage).toHaveBeenCalledWith("2026-10-05", ["com.productive"]);
  });
});

describe("sanitizeUsage", () => {
  it("clamps and rounds into backend-valid ranges", () => {
    expect(sanitizeUsage({ date: "d", total_minutes: 5000, dumb_minutes: 9000 })).toEqual({
      date: "d",
      total_minutes: 1440,
      dumb_minutes: 1440,
    });
    expect(sanitizeUsage({ date: "d", total_minutes: 50.4, dumb_minutes: 70 })).toEqual({
      date: "d",
      total_minutes: 50,
      dumb_minutes: 50,
    });
    expect(sanitizeUsage({ date: "d", total_minutes: -3, dumb_minutes: NaN })).toEqual({
      date: "d",
      total_minutes: 0,
      dumb_minutes: 0,
    });
  });
});
