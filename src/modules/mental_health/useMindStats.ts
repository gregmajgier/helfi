import { useFocusEffect } from "expo-router";
import { useCallback, useMemo, useState } from "react";

import { localDateKey } from "@/modules/dashboard/summary";

import { listJournalEntries, listMoodEntries } from "./api";
import { addDays, computeMindStats, type MindStats } from "./stats";
import type { JournalEntry, MoodEntry } from "./types";

/** History window the dashboard reads. Covers the 30-day average and the previous-week comparison. */
const HISTORY_DAYS = 120;

export function useMindStats(): {
  stats: MindStats;
  entries: MoodEntry[];
  journals: JournalEntry[];
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
} {
  const [entries, setEntries] = useState<MoodEntry[]>([]);
  const [journals, setJournals] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const start = localDateKey(addDays(new Date(), -HISTORY_DAYS));
      const [moods, notes] = await Promise.all([listMoodEntries(start), listJournalEntries()]);
      setEntries(moods);
      setJournals(notes);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load your check-ins");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      reload();
    }, [reload])
  );

  const stats = useMemo(() => computeMindStats(entries), [entries]);
  return { stats, entries, journals, loading, error, reload };
}
