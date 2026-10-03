import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Pressable, Text, View } from "react-native";

import { Button, Card, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createMoodEntry, getTodaysPrompt, listMoodEntries } from "@/modules/mental_health/api";
import type { MoodEntry } from "@/modules/mental_health/types";

const MOOD_OPTIONS: { score: number; emoji: string; label: string }[] = [
  { score: 1, emoji: "😞", label: "Rough" },
  { score: 2, emoji: "🙁", label: "Low" },
  { score: 3, emoji: "😐", label: "Okay" },
  { score: 4, emoji: "🙂", label: "Good" },
  { score: 5, emoji: "😄", label: "Great" },
];

export default function MentalHealthRoute() {
  const router = useRouter();
  const { colors, pillars, font } = useTheme();
  const accent = pillars.mind.light;
  const [recent, setRecent] = useState<MoodEntry[]>([]);
  const [prompt, setPrompt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [entries, todays] = await Promise.all([listMoodEntries(), getTodaysPrompt()]);
      setRecent(entries.slice(0, 5));
      setPrompt(todays.prompt);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load");
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const checkIn = async (score: number) => {
    setSaving(true);
    try {
      await createMoodEntry({ logged_at: new Date().toISOString(), mood_score: score, tags: [] });
      setError(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to save check-in");
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScreenContainer>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>Mind</Text>
      {error ? <Text style={{ color: "#C0392B" }}>{error}</Text> : null}

      <Card>
        <Text style={{ fontFamily: font.semibold, fontSize: 16, color: colors.textPrimary }}>
          How are you feeling right now?
        </Text>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          {MOOD_OPTIONS.map((option) => (
            <Pressable
              key={option.score}
              disabled={saving}
              onPress={() => checkIn(option.score)}
              style={{ alignItems: "center", gap: 4, opacity: saving ? 0.5 : 1 }}
            >
              <Text style={{ fontSize: 28 }}>{option.emoji}</Text>
              <Text style={{ fontFamily: font.regular, fontSize: 11, color: colors.textSecondary }}>
                {option.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </Card>

      <Card style={{ borderColor: accent, borderWidth: 1.5 }}>
        <Text style={{ fontFamily: font.semibold, fontSize: 13, color: colors.textSecondary }}>
          TODAY'S PROMPT
        </Text>
        <Text style={{ fontFamily: font.regular, fontSize: 15, color: colors.textPrimary }}>
          {prompt ?? "Loading..."}
        </Text>
        <Button
          title="Write in journal"
          variant="secondary"
          color={accent}
          onPress={() => router.push("/mental-health/journal" as Href)}
        />
      </Card>

      <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textSecondary }}>
        Recent check-ins
      </Text>
      {recent.length === 0 ? (
        <Text style={{ color: colors.textSecondary }}>No check-ins yet.</Text>
      ) : (
        recent.map((entry) => (
          <Text key={entry.id} style={{ color: colors.textPrimary }}>
            {MOOD_OPTIONS.find((o) => o.score === entry.mood_score)?.emoji}{" "}
            {new Date(entry.logged_at).toLocaleDateString()}
          </Text>
        ))
      )}

      <Button
        title="View history"
        variant="text"
        color={accent}
        onPress={() => router.push("/mental-health/history" as Href)}
      />
    </ScreenContainer>
  );
}
