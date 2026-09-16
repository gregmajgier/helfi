export type MealSlot = "breakfast" | "lunch" | "dinner" | "snack";
export type EntrySource = "search" | "quick_add" | "photo_ai";

export type FoodOut = {
  id: string;
  name: string;
  serving_size: number;
  serving_unit: string;
  calories_per_serving: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
};

export type MealEntry = {
  id: string;
  user_id: string;
  meal_slot: MealSlot;
  source: EntrySource;
  logged_at: string;
  food_id?: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  created_at: string;
  updated_at: string;
};

export type MealEntryInput = {
  meal_slot: MealSlot;
  source: EntrySource;
  logged_at: string;
  food_id?: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
};

export type PhotoEstimate = {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  confidence: number;
  description: string;
};
