import { apiFetch } from "@/lib/api-client";

import type { JournalEntry, JournalEntryInput, MoodEntry, MoodEntryInput } from "./types";

export function listMoodEntries(start?: string, end?: string): Promise<MoodEntry[]> {
  const params = new URLSearchParams();
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  const query = params.toString();
  return apiFetch<MoodEntry[]>(`/mood/entries${query ? `?${query}` : ""}`);
}

export function createMoodEntry(entry: MoodEntryInput): Promise<MoodEntry> {
  return apiFetch<MoodEntry>("/mood/entries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  });
}

export function deleteMoodEntry(id: string): Promise<void> {
  return apiFetch<void>(`/mood/entries/${id}`, { method: "DELETE" });
}

export function listJournalEntries(): Promise<JournalEntry[]> {
  return apiFetch<JournalEntry[]>("/mood/journal");
}

export function createJournalEntry(entry: JournalEntryInput): Promise<JournalEntry> {
  return apiFetch<JournalEntry>("/mood/journal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  });
}

export function deleteJournalEntry(id: string): Promise<void> {
  return apiFetch<void>(`/mood/journal/${id}`, { method: "DELETE" });
}

export function getTodaysPrompt(): Promise<{ prompt: string }> {
  return apiFetch<{ prompt: string }>("/mood/prompts");
}
