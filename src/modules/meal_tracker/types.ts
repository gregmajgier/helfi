export type MealSlot = "breakfast" | "lunch" | "dinner" | "snack";
export type EntrySource =
  | "search"
  | "quick_add"
  | "photo_ai"
  | "description_ai"
  | "barcode"
  | "custom"
  | "recipe"
  | "plan";

export const MEAL_SLOTS: MealSlot[] = ["breakfast", "lunch", "dinner", "snack"];

export type Nutrients = {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  sugar_g: number;
  saturated_fat_g: number;
  sodium_mg: number;
};

export type FoodOut = {
  id: string;
  name: string;
  brand?: string;
  serving_size: number;
  serving_unit: string;
  calories_per_serving: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  sugar_g: number;
  saturated_fat_g: number;
  sodium_mg: number;
  barcode?: string;
  created_by_user_id?: string;
};

export type FoodCreateInput = Omit<FoodOut, "id" | "created_by_user_id" | "barcode">;

export type MealEntry = Nutrients & {
  id: string;
  user_id: string;
  meal_slot: MealSlot;
  source: EntrySource;
  logged_at: string;
  day?: string;
  food_id?: string;
  name?: string;
  amount?: number;
  unit?: string;
  created_at: string;
  updated_at: string;
};

export type MealEntryInput = Partial<Nutrients> & {
  meal_slot: MealSlot;
  source: EntrySource;
  logged_at: string;
  day?: string;
  food_id?: string;
  name?: string;
  amount?: number;
  unit?: string;
  calories: number;
};

export type DayTotals = Nutrients & { day: string; entries: number };

export type Stats = {
  start: string;
  end: string;
  days: DayTotals[];
  logged_days: number;
  average_calories: number;
  average_protein_g: number;
  average_carbs_g: number;
  average_fat_g: number;
};

export type PhotoEstimate = {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  confidence: number;
  description: string;
};

// ---- profile & goals
export type Sex = "male" | "female";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "active" | "very_active";
export type Goal = "lose" | "maintain" | "build";

export type MacroSplit = { protein_pct: number; carbs_pct: number; fat_pct: number };

export type Profile = {
  sex: Sex;
  birth_year: number;
  height_cm: number;
  weight_kg: number;
  activity_level: ActivityLevel;
  goal: Goal;
  goal_weight_kg?: number | null;
  weekly_change_kg: number;
  calorie_override?: number | null;
  macro_split?: MacroSplit | null;
  water_goal_ml_override?: number | null;
};

export type Targets = {
  bmr: number;
  tdee: number;
  daily_delta: number;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  macro_split: MacroSplit;
  water_ml: number;
  fiber_g: number;
  sugar_g_limit: number;
  saturated_fat_g_limit: number;
  sodium_mg_limit: number;
  warnings: string[];
};

export type WeightEntry = { id: string; day: string; weight_kg: number };

export type Forecast = {
  current_kg: number;
  goal_kg?: number | null;
  planned_weekly_change_kg: number;
  planned_eta?: string | null;
  trend_kg_per_week?: number | null;
  trend_eta?: string | null;
  reached: boolean;
};

// ---- water
export type WaterDay = {
  day: string;
  total_ml: number;
  goal_ml: number;
  entries: { id: string; day: string; amount_ml: number; logged_at: string }[];
};

// ---- recipes
export type Ingredient = Partial<Nutrients> & {
  name: string;
  amount: number;
  unit: string;
  food_id?: string;
};

export type RecipeInput = {
  name: string;
  servings: number;
  meal_types: MealSlot[];
  prep_minutes?: number | null;
  ingredients: Ingredient[];
  instructions: string[];
};

export type Recipe = RecipeInput & {
  id: string;
  curated: boolean;
  totals: Nutrients;
  per_serving: Nutrients;
};

// ---- planning
export type PlanItem = Nutrients & {
  id: string;
  day: string;
  meal_slot: MealSlot;
  name: string;
  recipe_id?: string;
  food_id?: string;
  amount: number;
  unit: string;
  ingredients: { name: string; amount: number; unit: string }[];
};

export type PlanItemInput =
  | { day: string; meal_slot: MealSlot; recipe_id: string; servings: number }
  | { day: string; meal_slot: MealSlot; food_id: string; amount: number };

export type ShoppingItem = {
  id: string;
  name: string;
  amount?: number | null;
  unit?: string | null;
  checked: boolean;
  source: "plan" | "manual";
};

// ---- fasting
export type FastingProtocol = "12:12" | "14:10" | "16:8" | "18:6" | "20:4" | "custom";

export type Fast = {
  id: string;
  protocol: FastingProtocol;
  target_hours: number;
  started_at: string;
  ended_at?: string | null;
  elapsed_hours: number;
  completed: boolean;
};

export type FastingHistory = {
  sessions: Fast[];
  stats: {
    total: number;
    completed: number;
    average_hours: number;
    longest_hours: number;
    current_streak: number;
  };
};
