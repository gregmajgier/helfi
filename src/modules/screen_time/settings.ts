import AsyncStorage from "@react-native-async-storage/async-storage";

import type { InstalledApp } from "./types";

export const DEFAULT_FOCUS_BUDGET_MINUTES = 120;
export const MIN_FOCUS_BUDGET_MINUTES = 15;
export const MAX_FOCUS_BUDGET_MINUTES = 720;
export const BUDGET_STEP_MINUTES = 15;
/** Upper bound on stored excluded apps, so a corrupt value cannot grow without limit. */
export const MAX_EXCLUDED_APPS = 2000;

const BUDGET_KEY = "helf.focus.daily_budget_minutes";
const EXCLUDED_KEY = "helf.focus.excluded_apps";

export function clampBudget(minutes: number): number {
  if (!Number.isFinite(minutes)) return DEFAULT_FOCUS_BUDGET_MINUTES;
  const stepped = Math.round(minutes / BUDGET_STEP_MINUTES) * BUDGET_STEP_MINUTES;
  return Math.min(MAX_FOCUS_BUDGET_MINUTES, Math.max(MIN_FOCUS_BUDGET_MINUTES, stepped));
}

export async function getFocusBudget(): Promise<number> {
  const raw = await AsyncStorage.getItem(BUDGET_KEY);
  return raw === null ? DEFAULT_FOCUS_BUDGET_MINUTES : clampBudget(Number(raw));
}

export async function setFocusBudget(minutes: number): Promise<number> {
  const value = clampBudget(minutes);
  await AsyncStorage.setItem(BUDGET_KEY, String(value));
  return value;
}

/** Returns null when the user has never chosen, so the UI can offer defaults. */
export async function getExcludedApps(): Promise<string[] | null> {
  const raw = await AsyncStorage.getItem(EXCLUDED_KEY);
  if (raw === null) return null;
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return null;
    return parsed.filter((v): v is string => typeof v === "string").slice(0, MAX_EXCLUDED_APPS);
  } catch {
    return null;
  }
}

export async function setExcludedApps(ids: string[]): Promise<void> {
  await AsyncStorage.setItem(EXCLUDED_KEY, JSON.stringify(ids.slice(0, MAX_EXCLUDED_APPS)));
}

// ApplicationInfo.category only carries a few Play categories; health, fitness and
// education apps do not expose one, so the user picks those manually.
const DEFAULT_EXCLUDED_CATEGORIES = new Set(["productivity", "maps"]);

export function defaultExcludedApps(apps: InstalledApp[]): string[] {
  return apps.filter((a) => a.category !== null && DEFAULT_EXCLUDED_CATEGORIES.has(a.category)).map((a) => a.id);
}
