import { apiFetch } from "@/lib/api-client";

import type { FoodOut, MealEntry, MealEntryInput, PhotoEstimate } from "./types";

export function searchFoods(query: string): Promise<FoodOut[]> {
  return apiFetch<FoodOut[]>(`/meals/foods/search?q=${encodeURIComponent(query)}`);
}

export function listEntriesForDay(day: string): Promise<MealEntry[]> {
  return apiFetch<MealEntry[]>(`/meals/entries?day=${day}`);
}

export function createEntry(entry: MealEntryInput): Promise<MealEntry> {
  return apiFetch<MealEntry>("/meals/entries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  });
}

export function updateEntry(id: string, updates: Partial<MealEntryInput>): Promise<MealEntry> {
  return apiFetch<MealEntry>(`/meals/entries/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
}

export function deleteEntry(id: string): Promise<void> {
  return apiFetch<void>(`/meals/entries/${id}`, { method: "DELETE" });
}

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
