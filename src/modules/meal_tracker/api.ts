import { apiFetch } from "@/lib/api-client";

import type {
  Fast,
  FastingHistory,
  FastingProtocol,
  FoodCreateInput,
  FoodOut,
  Forecast,
  MealEntry,
  MealEntryInput,
  MealSlot,
  PhotoEstimate,
  PlanItem,
  PlanItemInput,
  Profile,
  Recipe,
  RecipeInput,
  ShoppingItem,
  Stats,
  Targets,
  WaterDay,
  WeightEntry,
} from "./types";

const JSON_HEADERS = { "Content-Type": "application/json" };

function send<T>(path: string, method: string, body?: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method,
    headers: JSON_HEADERS,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

const q = (params: Record<string, string | number | boolean | undefined>) => {
  const search = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== "")
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
    .join("&");
  return search ? `?${search}` : "";
};

// ---------------------------------------------------------------- foods
export const createCustomFood = (food: FoodCreateInput) => send<FoodOut>("/meals/foods", "POST", food);
export const updateCustomFood = (id: string, food: Partial<FoodCreateInput>) =>
  send<FoodOut>(`/meals/foods/${id}`, "PATCH", food);
export const deleteCustomFood = (id: string) => send<void>(`/meals/foods/${id}`, "DELETE");
export const getFood = (id: string) => apiFetch<FoodOut>(`/meals/foods/${id}`);
export const searchFoods = (query: string) => apiFetch<FoodOut[]>(`/meals/foods/search${q({ q: query })}`);
export const listMyFoods = () => apiFetch<FoodOut[]>("/meals/foods/mine");
export const listFavorites = () => apiFetch<FoodOut[]>("/meals/foods/favorites");
export const addFavorite = (id: string) => send<void>(`/meals/foods/${id}/favorite`, "PUT");
export const removeFavorite = (id: string) => send<void>(`/meals/foods/${id}/favorite`, "DELETE");
export const lookupBarcode = (barcode: string) =>
  apiFetch<FoodOut>(`/meals/foods/barcode/${encodeURIComponent(barcode)}`);

// ---------------------------------------------------------------- entries
export const listEntriesForDay = (day: string) => apiFetch<MealEntry[]>(`/meals/entries${q({ day })}`);
export const createEntry = (entry: MealEntryInput) => send<MealEntry>("/meals/entries", "POST", entry);
export const updateEntry = (id: string, updates: Partial<MealEntryInput>) =>
  send<MealEntry>(`/meals/entries/${id}`, "PATCH", updates);
export const deleteEntry = (id: string) => send<void>(`/meals/entries/${id}`, "DELETE");
export const logFood = (input: {
  food_id: string;
  amount: number;
  meal_slot: MealSlot;
  day: string;
}) => send<MealEntry>("/meals/entries/from-food", "POST", { ...input, logged_at: new Date().toISOString() });
export const copyEntries = (input: {
  from_day: string;
  to_day: string;
  from_slot?: MealSlot;
  to_slot?: MealSlot;
}) => send<MealEntry[]>("/meals/entries/copy", "POST", input);
export const listRecent = (today: string) => apiFetch<MealEntry[]>(`/meals/entries/recent${q({ today })}`);
export const getStats = (start: string, end: string) =>
  apiFetch<Stats>(`/meals/entries/stats${q({ start, end })}`);

export async function estimateFromPhoto(photoUri: string): Promise<PhotoEstimate> {
  const formData = new FormData();
  formData.append("photo", {
    uri: photoUri,
    name: "meal.jpg",
    type: "image/jpeg",
  } as unknown as Blob);

  return apiFetch<PhotoEstimate>("/meals/photo-estimate", {
    method: "POST",
    body: formData,
  });
}

export const estimateFromDescription = (description: string) =>
  send<PhotoEstimate>("/meals/estimate-from-description", "POST", { description });

// ---------------------------------------------------------------- profile
export const getProfile = () => apiFetch<Profile>("/profile");
export const saveProfile = (profile: Profile) => send<Profile>("/profile", "PUT", profile);
export const getTargets = () => apiFetch<Targets>("/profile/targets");
export const listWeight = (days = 90) => apiFetch<WeightEntry[]>(`/profile/weight${q({ days })}`);
export const logWeight = (day: string, weight_kg: number) =>
  send<WeightEntry>("/profile/weight", "POST", { day, weight_kg });
export const deleteWeight = (id: string) => send<void>(`/profile/weight/${id}`, "DELETE");
export const getForecast = () => apiFetch<Forecast>("/profile/forecast");

// ---------------------------------------------------------------- water
export const getWater = (day: string) => apiFetch<WaterDay>(`/water${q({ day })}`);
export const addWater = (day: string, amount_ml: number) => send<WaterDay>("/water", "POST", { day, amount_ml });
export const deleteWater = (id: string) => send<WaterDay>(`/water/${id}`, "DELETE");

// ---------------------------------------------------------------- recipes
export const listRecipes = (params: { q?: string; meal_type?: MealSlot; mine?: boolean } = {}) =>
  apiFetch<Recipe[]>(`/recipes${q(params)}`);
export const getRecipe = (id: string) => apiFetch<Recipe>(`/recipes/${id}`);
export const createRecipe = (recipe: RecipeInput) => send<Recipe>("/recipes", "POST", recipe);
export const updateRecipe = (id: string, recipe: RecipeInput) => send<Recipe>(`/recipes/${id}`, "PUT", recipe);
export const deleteRecipe = (id: string) => send<void>(`/recipes/${id}`, "DELETE");
export const copyRecipe = (id: string) => send<Recipe>(`/recipes/${id}/copy`, "POST");
export const logRecipe = (id: string, input: { servings: number; meal_slot: MealSlot; day: string }) =>
  send<MealEntry>(`/recipes/${id}/log`, "POST", { ...input, logged_at: new Date().toISOString() });

// ---------------------------------------------------------------- plan & shopping
export const getPlan = (start: string, end: string) => apiFetch<PlanItem[]>(`/plan${q({ start, end })}`);
export const addPlanItem = (item: PlanItemInput) => send<PlanItem>("/plan", "POST", item);
export const deletePlanItem = (id: string) => send<void>(`/plan/${id}`, "DELETE");
export const clearPlan = (start: string, end: string) =>
  send<{ deleted: number }>("/plan/clear", "POST", { start, end });
export const applyPlan = (day: string, meal_slot?: MealSlot) =>
  send<MealEntry[]>("/plan/apply", "POST", { day, meal_slot });
export const generatePlan = (start: string, days: number, calorie_target?: number) =>
  send<PlanItem[]>("/plan/generate", "POST", { start, days, calorie_target, replace: true });

export const getShoppingList = () => apiFetch<ShoppingItem[]>("/shopping");
export const generateShoppingList = (start: string, end: string) =>
  send<ShoppingItem[]>("/shopping/generate", "POST", { start, end });
export const addShoppingItem = (item: { name: string; amount?: number; unit?: string }) =>
  send<ShoppingItem>("/shopping", "POST", item);
export const setShoppingChecked = (id: string, checked: boolean) =>
  send<ShoppingItem>(`/shopping/${id}`, "PATCH", { checked });
export const deleteShoppingItem = (id: string) => send<void>(`/shopping/${id}`, "DELETE");
export const clearCheckedShopping = () => send<ShoppingItem[]>("/shopping/clear-checked", "POST");

// ---------------------------------------------------------------- fasting
export const getCurrentFast = () => apiFetch<Fast | null>("/fasting/current");
export const startFast = (protocol: FastingProtocol, target_hours?: number) =>
  send<Fast>("/fasting/start", "POST", { protocol, target_hours });
export const endFast = () => send<Fast>("/fasting/end", "POST", {});
export const getFastingHistory = (days = 30) => apiFetch<FastingHistory>(`/fasting/history${q({ days })}`);
export const deleteFast = (id: string) => send<void>(`/fasting/${id}`, "DELETE");
