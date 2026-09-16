import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Button, FlatList, SafeAreaView, Text, View } from "react-native";

import { deleteEntry, listEntriesForDay } from "@/modules/meal_tracker/api";
import type { MealEntry } from "@/modules/meal_tracker/types";

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function MealTrackerRoute() {
  const router = useRouter();
  const [entries, setEntries] = useState<MealEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      setEntries(await listEntriesForDay(todayIsoDate()));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

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
    <SafeAreaView style={{ flex: 1, padding: 16 }}>
      <Text style={{ fontSize: 20, fontWeight: "600" }}>Today</Text>
      <Text>
        {Math.round(totals.calories)} kcal · P {Math.round(totals.protein_g)}g · C{" "}
        {Math.round(totals.carbs_g)}g · F {Math.round(totals.fat_g)}g
      </Text>

      <FlatList
        data={entries}
        keyExtractor={(item) => item.id}
        refreshing={isLoading}
        onRefresh={load}
        ListEmptyComponent={<Text>No entries yet today.</Text>}
        renderItem={({ item }) => (
          <View style={{ flexDirection: "row", justifyContent: "space-between", paddingVertical: 8 }}>
            <Text>
              {item.meal_slot}: {Math.round(item.calories)} kcal
            </Text>
            <Button
              title="Delete"
              onPress={async () => {
                await deleteEntry(item.id);
                load();
              }}
            />
          </View>
        )}
      />

      <Button title="Add Entry" onPress={() => router.push("/meal-tracker/add-entry" as Href)} />
    </SafeAreaView>
  );
}
