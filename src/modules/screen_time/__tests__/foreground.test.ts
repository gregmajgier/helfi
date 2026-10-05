import { EVENT, sumForegroundIntervals, type UsageEventRecord } from "../foreground";

const MIN = 60_000;
const START = Date.UTC(2026, 9, 5, 0, 0);
const END = START + 24 * 60 * MIN;
const at = (minutes: number) => START + minutes * MIN;
const ev = (p: string, t: number, minute: number): UsageEventRecord => ({ p, t, ts: at(minute) });
const run = (events: UsageEventRecord[], extra: Partial<Parameters<typeof sumForegroundIntervals>[1]> = {}) =>
  sumForegroundIntervals(events, { windowStart: START, windowEnd: END, now: END, ...extra });

describe("sumForegroundIntervals", () => {
  it("sums simple foreground/background pairs across apps", () => {
    const r = run([
      ev("a", EVENT.FOREGROUND, 60),
      ev("a", EVENT.BACKGROUND, 90),
      ev("b", EVENT.FOREGROUND, 100),
      ev("b", EVENT.BACKGROUND, 110),
    ]);
    expect(r).toEqual({ totalMinutes: 40, dumbMinutes: 40 });
  });

  it("returns zero for no events", () => {
    expect(run([])).toEqual({ totalMinutes: 0, dumbMinutes: 0 });
  });

  it("removes excluded apps from dumb minutes but keeps them in the total", () => {
    const r = run(
      [
        ev("docs", EVENT.FOREGROUND, 0),
        ev("docs", EVENT.BACKGROUND, 30),
        ev("social", EVENT.FOREGROUND, 30),
        ev("social", EVENT.BACKGROUND, 45),
      ],
      { excluded: new Set(["docs"]) }
    );
    expect(r).toEqual({ totalMinutes: 45, dumbMinutes: 15 });
  });

  it("drops ignored packages from both totals", () => {
    const r = run(
      [
        ev("launcher", EVENT.FOREGROUND, 0),
        ev("launcher", EVENT.BACKGROUND, 20),
        ev("a", EVENT.FOREGROUND, 20),
        ev("a", EVENT.BACKGROUND, 30),
      ],
      { ignored: new Set(["launcher"]) }
    );
    expect(r).toEqual({ totalMinutes: 10, dumbMinutes: 10 });
  });

  it("does not double count multiple activities of the same app", () => {
    const r = run([
      ev("a", EVENT.FOREGROUND, 0),
      ev("a", EVENT.BACKGROUND, 5),
      ev("a", EVENT.FOREGROUND, 5), // second activity resumes right away
      ev("a", EVENT.FOREGROUND, 5),
      ev("a", EVENT.BACKGROUND, 20),
    ]);
    expect(r.totalMinutes).toBe(20);
  });

  it("closes the previous app when another comes to the foreground without a background event", () => {
    const r = run([ev("a", EVENT.FOREGROUND, 0), ev("b", EVENT.FOREGROUND, 10), ev("b", EVENT.BACKGROUND, 15)]);
    expect(r.totalMinutes).toBe(15);
  });

  it("ends the interval when the screen turns off or the device shuts down", () => {
    expect(run([ev("a", EVENT.FOREGROUND, 0), ev("", EVENT.SCREEN_OFF, 12)]).totalMinutes).toBe(12);
    expect(run([ev("a", EVENT.FOREGROUND, 0), ev("", EVENT.SHUTDOWN, 7)]).totalMinutes).toBe(7);
  });

  it("treats ACTIVITY_STOPPED as a background for the open app", () => {
    expect(run([ev("a", EVENT.FOREGROUND, 0), ev("a", EVENT.STOPPED, 9)]).totalMinutes).toBe(9);
  });

  it("ignores a background event for an app that is not the open one", () => {
    const r = run([ev("a", EVENT.FOREGROUND, 0), ev("b", EVENT.BACKGROUND, 5), ev("a", EVENT.BACKGROUND, 10)]);
    expect(r.totalMinutes).toBe(10);
  });

  it("credits an app already open at the window start when the first event is its background", () => {
    expect(run([ev("a", EVENT.BACKGROUND, 25)]).totalMinutes).toBe(25);
  });

  it("does not credit a stray background that is not the first event", () => {
    const r = run([ev("a", EVENT.FOREGROUND, 0), ev("a", EVENT.BACKGROUND, 5), ev("b", EVENT.BACKGROUND, 50)]);
    expect(r.totalMinutes).toBe(5);
  });

  it("caps an interval still open at the end to now", () => {
    const r = sumForegroundIntervals([ev("a", EVENT.FOREGROUND, 600)], {
      windowStart: START,
      windowEnd: END,
      now: at(630),
    });
    expect(r.totalMinutes).toBe(30);
  });

  it("caps an open interval at the window end for past days", () => {
    const r = run([ev("a", EVENT.FOREGROUND, 24 * 60 - 10)], { now: END + 5 * 60 * MIN });
    expect(r.totalMinutes).toBe(10);
  });

  it("sorts unordered events and ignores events outside the window", () => {
    const r = run([
      ev("a", EVENT.BACKGROUND, 30),
      ev("a", EVENT.FOREGROUND, 10),
      { p: "z", t: EVENT.FOREGROUND, ts: START - MIN },
      { p: "z", t: EVENT.BACKGROUND, ts: END + MIN },
    ]);
    expect(r.totalMinutes).toBe(20);
  });

  it("rounds to whole minutes", () => {
    const r = run([
      { p: "a", t: EVENT.FOREGROUND, ts: at(0) },
      { p: "a", t: EVENT.BACKGROUND, ts: at(0) + 90_000 },
    ]);
    expect(r.totalMinutes).toBe(2);
  });

  it("never reports dumb above total", () => {
    const r = run(
      [ev("a", EVENT.FOREGROUND, 0), ev("a", EVENT.BACKGROUND, 40)],
      { excluded: new Set(["a"]) }
    );
    expect(r).toEqual({ totalMinutes: 40, dumbMinutes: 0 });
  });
});
