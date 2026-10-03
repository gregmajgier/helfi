import { useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { ScrollView, Text } from "react-native";

import { ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { listJournalEntries, listMoodEntries } from "@/modules/mental_health/api";
import type { JournalEntry, MoodEntry } from "@/modules/mental_health/types";

const MOOD_EMOJI: Record<number, string> = { 1: "😞", 2: "🙁", 3: "😐", 4: "🙂", 5: "😄" };

export default function MentalHealthHistoryRoute() {
  const { colors, font, spacing } = useTheme();
  const [moods, setMoods] = useState<MoodEntry[]>([]);
  const [journals, setJournals] = useState<JournalEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [moodEntries, journalEntries] = await Promise.all([listMoodEntries(), listJournalEntries()]);
      setMoods(moodEntries);
      setJournals(journalEntries);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load history");
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  return (
    <ScreenContainer style={{ gap: spacing.lg }}>
      <ScrollView contentContainerStyle={{ gap: spacing.lg }}>
        <Text style={{ fontFamily: font.bold, fontSize: 20, color: colors.textPrimary }}>History</Text>
        {error ? <Text style={{ color: "#C0392B" }}>{error}</Text> : null}

        <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textSecondary }}>
          Mood check-ins
        </Text>
        <Text style={{ fontSize: 22, letterSpacing: 4 }}>
          {moods.length === 0
            ? "No check-ins yet."
            : moods.slice(0, 30).map((m) => MOOD_EMOJI[m.mood_score]).join(" ")}
        </Text>

        <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textSecondary }}>
          Journal entries
        </Text>
        {journals.length === 0 ? (
          <Text style={{ color: colors.textSecondary }}>No journal entries yet.</Text>
        ) : (
          journals.map((entry) => (
            <Text key={entry.id} style={{ color: colors.textPrimary, marginBottom: spacing.sm }}>
              {new Date(entry.written_at).toLocaleDateString()} — {entry.body}
            </Text>
          ))
        )}
      </ScrollView>
    </ScreenContainer>
  );
}
