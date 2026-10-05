import AsyncStorage from "@react-native-async-storage/async-storage";

import {
  clampBudget,
  defaultExcludedApps,
  getExcludedApps,
  getFocusBudget,
  setExcludedApps,
  setFocusBudget,
} from "../settings";

jest.mock("@react-native-async-storage/async-storage", () =>
  jest.requireActual("@react-native-async-storage/async-storage/jest/async-storage-mock")
);

beforeEach(async () => {
  await AsyncStorage.clear();
});

describe("focus budget", () => {
  it("defaults to 120 minutes", async () => {
    expect(await getFocusBudget()).toBe(120);
  });

  it("clamps to 15-720 and snaps to 15-minute steps", () => {
    expect(clampBudget(0)).toBe(15);
    expect(clampBudget(5000)).toBe(720);
    expect(clampBudget(100)).toBe(105);
    expect(clampBudget(NaN)).toBe(120);
  });

  it("persists the clamped value and survives corrupt storage", async () => {
    expect(await setFocusBudget(10_000)).toBe(720);
    expect(await getFocusBudget()).toBe(720);
    await AsyncStorage.setItem("helf.focus.daily_budget_minutes", "garbage");
    expect(await getFocusBudget()).toBe(120);
  });
});

describe("excluded apps", () => {
  it("is null until chosen, then round-trips", async () => {
    expect(await getExcludedApps()).toBeNull();
    await setExcludedApps(["a", "b"]);
    expect(await getExcludedApps()).toEqual(["a", "b"]);
  });

  it("ignores corrupt or non-string data", async () => {
    await AsyncStorage.setItem("helf.focus.excluded_apps", "{not json");
    expect(await getExcludedApps()).toBeNull();
    await AsyncStorage.setItem("helf.focus.excluded_apps", JSON.stringify(["a", 3, null, "b"]));
    expect(await getExcludedApps()).toEqual(["a", "b"]);
  });

  it("pre-selects productivity and maps apps by default", () => {
    const apps = [
      { id: "docs", label: "Docs", category: "productivity" },
      { id: "maps", label: "Maps", category: "maps" },
      { id: "game", label: "Game", category: "game" },
      { id: "x", label: "X", category: null },
    ];
    expect(defaultExcludedApps(apps)).toEqual(["docs", "maps"]);
  });
});
