import type { FoodOut, MealEntry, MealSlot, Nutrients } from "./types";
import { MEAL_SLOTS } from "./types";

export const EMPTY_NUTRIENTS: Nutrients = {
  calories: 0,
  protein_g: 0,
  carbs_g: 0,
  fat_g: 0,
  fiber_g: 0,
  sugar_g: 0,
  saturated_fat_g: 0,
  sodium_mg: 0,
};

export const NUTRIENT_KEYS = Object.keys(EMPTY_NUTRIENTS) as (keyof Nutrients)[];

/** Nutrition of one serving of a food (serving_size serving_unit). */
export function foodNutrients(food: FoodOut): Nutrients {
  return {
    calories: food.calories_per_serving ?? 0,
    protein_g: food.protein_g ?? 0,
    carbs_g: food.carbs_g ?? 0,
    fat_g: food.fat_g ?? 0,
    fiber_g: food.fiber_g ?? 0,
    sugar_g: food.sugar_g ?? 0,
    saturated_fat_g: food.saturated_fat_g ?? 0,
    sodium_mg: food.sodium_mg ?? 0,
  };
}

export function scaleNutrients(n: Partial<Nutrients>, factor: number): Nutrients {
  const out = { ...EMPTY_NUTRIENTS };
  for (const key of NUTRIENT_KEYS) out[key] = Math.round((n[key] ?? 0) * factor * 100) / 100;
  return out;
}

/** Nutrition for `amount` of the food, in the food's own serving unit. */
export function nutrientsForAmount(food: FoodOut, amount: number): Nutrients {
  return scaleNutrients(foodNutrients(food), amount / food.serving_size);
}

export function sumNutrients(items: Partial<Nutrients>[]): Nutrients {
  const total = { ...EMPTY_NUTRIENTS };
  for (const item of items) for (const key of NUTRIENT_KEYS) total[key] += item[key] ?? 0;
  for (const key of NUTRIENT_KEYS) total[key] = Math.round(total[key] * 100) / 100;
  return total;
}

export function groupBySlot(entries: MealEntry[]): Record<MealSlot, MealEntry[]> {
  const groups = { breakfast: [], lunch: [], dinner: [], snack: [] } as Record<MealSlot, MealEntry[]>;
  for (const entry of entries) groups[entry.meal_slot]?.push(entry);
  for (const slot of MEAL_SLOTS) groups[slot].sort((a, b) => a.logged_at.localeCompare(b.logged_at));
  return groups;
}

const SOURCE_LABELS: Record<string, string> = {
  photo_ai: "Photo estimate",
  description_ai: "Described meal",
  quick_add: "Quick add",
  recipe: "Recipe",
  plan: "Planned meal",
};

/** Entries logged before names existed have none; fall back by source. */
export function entryLabel(entry: Pick<MealEntry, "name" | "source">): string {
  return entry.name?.trim() || SOURCE_LABELS[entry.source] || "Logged item";
}

export function formatAmount(amount: number | undefined, unit: string | undefined): string {
  if (!amount) return "";
  const rounded = Math.round(amount * 10) / 10;
  return unit === "serving" ? `${rounded} ${rounded === 1 ? "serving" : "servings"}` : `${rounded} ${unit ?? ""}`.trim();
}

/** Amount that makes sense to start from: one serving of the food. */
export function defaultAmount(food: FoodOut): number {
  return food.serving_size;
}

export function servingsToAmount(food: FoodOut, servings: number): number {
  return Math.round(servings * food.serving_size * 10) / 10;
}

export function amountToServings(food: FoodOut, amount: number): number {
  return Math.round((amount / food.serving_size) * 100) / 100;
}

/** Share of a goal consumed, clamped to 0..1 for drawing; 0 when there is no goal. */
export function progress(value: number, goal: number | null | undefined): number {
  if (!goal || goal <= 0) return 0;
  return Math.max(0, Math.min(1, value / goal));
}

/** Parses a user-typed decimal ("1,5" or "1.5"); returns null if not a positive finite number. */
export function parseDecimal(text: string): number | null {
  const value = Number(text.trim().replace(",", "."));
  return Number.isFinite(value) && value > 0 ? value : null;
}
