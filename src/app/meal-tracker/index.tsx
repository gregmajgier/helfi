import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, FlatList, Pressable, Text, View } from "react-native";

import { Button, Card, ScreenContainer } from "@/components";
import { getDailyCalorieGoal, setDailyCalorieGoal } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";
import { deleteEntry, listEntriesForDay } from "@/modules/meal_tracker/api";
import type { MealEntry } from "@/modules/meal_tracker/types";

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function MealTrackerRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.fuel.light;
  const [entries, setEntries] = useState<MealEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [goal, setGoal] = useState<number | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const [dayEntries, storedGoal] = await Promise.all([
        listEntriesForDay(todayIsoDate()),
        getDailyCalorieGoal(),
      ]);
      setEntries(dayEntries);
      setGoal(storedGoal);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load entries");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const editGoal = () => {
    Alert.prompt?.(
      "Daily calorie goal",
      "Set a target to track against (leave blank to clear).",
      async (text) => {
        const value = Number(text);
        if (text && Number.isFinite(value) && value > 0) {
          await setDailyCalorieGoal(value);
          setGoal(value);
        }
      },
      "plain-text",
      goal ? String(goal) : ""
    );
  };

  const totals = entries.reduce(
    (acc, e) => ({
      calories: acc.calories + e.calories,
      protein_g: acc.protein_g + e.protein_g,
      carbs_g: acc.carbs_g + e.carbs_g,
      fat_g: acc.fat_g + e.fat_g,
    }),
    { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 }
  );

  return (
    <ScreenContainer>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>Today</Text>

      <Card style={{ borderColor: accent, borderWidth: 1.5 }}>
        <Pressable onPress={editGoal}>
          <Text style={{ fontFamily: font.bold, fontSize: 22, color: colors.textPrimary }}>
            {Math.round(totals.calories)}
            {goal ? <Text style={{ color: colors.textSecondary, fontFamily: font.medium }}> / {goal}</Text> : null}
            {" kcal"}
          </Text>
          <Text style={{ fontFamily: font.regular, fontSize: 13, color: colors.textSecondary }}>
            {goal ? "tap to edit goal" : "tap to set a daily goal"}
          </Text>
        </Pressable>
        <Text style={{ fontFamily: font.medium, fontSize: 14, color: colors.textPrimary, marginTop: spacing.xs }}>
          P {Math.round(totals.protein_g)}g · C {Math.round(totals.carbs_g)}g · F {Math.round(totals.fat_g)}g
        </Text>
      </Card>

      {error ? <Text style={{ color: colors.danger, fontFamily: font.regular }}>{error}</Text> : null}

      <FlatList
        data={entries}
        keyExtractor={(item) => item.id}
        refreshing={isLoading}
        onRefresh={load}
        style={{ flex: 1 }}
        ListEmptyComponent={
          <Text style={{ color: colors.textSecondary, fontFamily: font.regular }}>No entries yet today.</Text>
        }
        renderItem={({ item }) => (
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "space-between",
              paddingVertical: spacing.sm,
              borderBottomWidth: 1,
              borderBottomColor: colors.border,
            }}
          >
            <Text style={{ fontFamily: font.medium, color: colors.textPrimary, textTransform: "capitalize" }}>
              {item.meal_slot}: {Math.round(item.calories)} kcal
            </Text>
            <Button
              title="Delete"
              variant="text"
              color={colors.danger}
              onPress={async () => {
                try {
                  await deleteEntry(item.id);
                  setError(null);
                  load();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "failed to delete entry");
                }
              }}
            />
          </View>
        )}
      />

      <Button title="Add Entry" color={accent} onPress={() => router.push("/meal-tracker/add-entry" as Href)} />
    </ScreenContainer>
  );
}
