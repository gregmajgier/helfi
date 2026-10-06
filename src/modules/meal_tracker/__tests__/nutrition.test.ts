import { addDays, dayLabel, mondayOf, parseDay } from "../dates";
import {
  amountToServings,
  entryLabel,
  formatAmount,
  groupBySlot,
  nutrientsForAmount,
  parseDecimal,
  progress,
  scaleNutrients,
  servingsToAmount,
  sumNutrients,
} from "../nutrition";
import type { FoodOut, MealEntry } from "../types";

const banana: FoodOut = {
  id: "b",
  name: "Banana",
  serving_size: 118,
  serving_unit: "g",
  calories_per_serving: 105,
  protein_g: 1.3,
  carbs_g: 27,
  fat_g: 0.4,
  fiber_g: 3.1,
  sugar_g: 14.4,
  saturated_fat_g: 0.1,
  sodium_mg: 1,
};

const entry = (over: Partial<MealEntry>): MealEntry =>
  ({
    id: "1",
    user_id: "u",
    meal_slot: "lunch",
    source: "search",
    logged_at: "2026-10-06T12:00:00Z",
    calories: 100,
    protein_g: 0,
    carbs_g: 0,
    fat_g: 0,
    fiber_g: 0,
    sugar_g: 0,
    saturated_fat_g: 0,
    sodium_mg: 0,
    created_at: "",
    updated_at: "",
    ...over,
  }) as MealEntry;

describe("nutrition math", () => {
  it("scales a food to an amount in its own unit", () => {
    const n = nutrientsForAmount(banana, 236);
    expect(n.calories).toBe(210);
    expect(n.fiber_g).toBe(6.2);
  });

  it("converts between servings and amount", () => {
    expect(servingsToAmount(banana, 1.5)).toBe(177);
    expect(amountToServings(banana, 177)).toBe(1.5);
  });

  it("sums partial nutrient objects and ignores missing fields", () => {
    expect(sumNutrients([{ calories: 100, protein_g: 5 }, { calories: 50.5 }]).calories).toBe(150.5);
    expect(sumNutrients([]).sodium_mg).toBe(0);
  });

  it("scaleNutrients tolerates missing keys", () => {
    expect(scaleNutrients({ calories: 200 }, 0.5).calories).toBe(100);
  });
});

describe("diary helpers", () => {
  it("groups entries by slot ordered by time", () => {
    const groups = groupBySlot([
      entry({ id: "late", logged_at: "2026-10-06T19:00:00Z", meal_slot: "dinner" }),
      entry({ id: "b", logged_at: "2026-10-06T13:00:00Z" }),
      entry({ id: "a", logged_at: "2026-10-06T12:00:00Z" }),
    ]);
    expect(groups.lunch.map((e) => e.id)).toEqual(["a", "b"]);
    expect(groups.dinner).toHaveLength(1);
    expect(groups.breakfast).toEqual([]);
  });

  it("labels legacy entries by source", () => {
    expect(entryLabel({ name: "Rice", source: "search" })).toBe("Rice");
    expect(entryLabel({ name: undefined, source: "photo_ai" })).toBe("Photo estimate");
    expect(entryLabel({ name: " ", source: "search" })).toBe("Logged item");
  });

  it("formats amounts", () => {
    expect(formatAmount(150, "g")).toBe("150 g");
    expect(formatAmount(1, "serving")).toBe("1 serving");
    expect(formatAmount(1.5, "serving")).toBe("1.5 servings");
    expect(formatAmount(undefined, "g")).toBe("");
  });

  it("clamps progress and handles missing goals", () => {
    expect(progress(500, 1000)).toBe(0.5);
    expect(progress(2000, 1000)).toBe(1);
    expect(progress(5, null)).toBe(0);
    expect(progress(-5, 100)).toBe(0);
  });

  it("parses decimals with comma or dot", () => {
    expect(parseDecimal("1,5")).toBe(1.5);
    expect(parseDecimal(" 200 ")).toBe(200);
    expect(parseDecimal("0")).toBeNull();
    expect(parseDecimal("abc")).toBeNull();
    expect(parseDecimal("")).toBeNull();
  });
});

describe("local day maths", () => {
  it("adds days across month and DST boundaries without shifting", () => {
    expect(addDays("2026-10-31", 1)).toBe("2026-11-01");
    expect(addDays("2026-03-01", -1)).toBe("2026-02-28");
    expect(addDays("2026-10-25", 1)).toBe("2026-10-26"); // EU DST change weekend
    expect(addDays("2026-03-29", 1)).toBe("2026-03-30");
  });

  it("finds the Monday of a week", () => {
    expect(mondayOf("2026-10-07")).toBe("2026-10-05");
    expect(mondayOf("2026-10-04")).toBe("2026-09-28");
    expect(mondayOf("2026-10-05")).toBe("2026-10-05");
  });

  it("labels today, yesterday and tomorrow relative to a given today", () => {
    expect(dayLabel("2026-10-06", "2026-10-06")).toBe("Today");
    expect(dayLabel("2026-10-05", "2026-10-06")).toBe("Yesterday");
    expect(dayLabel("2026-10-07", "2026-10-06")).toBe("Tomorrow");
    expect(parseDay("2026-10-06").getDate()).toBe(6);
  });
});
