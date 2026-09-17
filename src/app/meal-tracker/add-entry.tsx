import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Button, FlatList, SafeAreaView, Text, TextInput, View } from "react-native";

import { createEntry, searchFoods } from "@/modules/meal_tracker/api";
import type { FoodOut, MealSlot } from "@/modules/meal_tracker/types";

const MEAL_SLOTS: MealSlot[] = ["breakfast", "lunch", "dinner", "snack"];

export default function AddEntryScreen() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<FoodOut[]>([]);
  const [mealSlot, setMealSlot] = useState<MealSlot>("breakfast");
  const [quickAddCalories, setQuickAddCalories] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onSearch = async (text: string) => {
    setQuery(text);
    try {
      setResults(text.length >= 2 ? await searchFoods(text) : []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "search failed");
    }
  };

  const logFood = async (food: FoodOut) => {
    try {
      await createEntry({
        meal_slot: mealSlot,
        source: "search",
        logged_at: new Date().toISOString(),
        food_id: food.id,
        calories: food.calories_per_serving,
        protein_g: food.protein_g,
        carbs_g: food.carbs_g,
        fat_g: food.fat_g,
      });
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to log food");
    }
  };

  const logQuickAdd = async () => {
    const calories = Number(quickAddCalories);
    if (!Number.isFinite(calories) || calories <= 0) return;
    try {
      await createEntry({
        meal_slot: mealSlot,
        source: "quick_add",
        logged_at: new Date().toISOString(),
        calories,
        protein_g: 0,
        carbs_g: 0,
        fat_g: 0,
      });
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to log quick add");
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}
      <View style={{ flexDirection: "row", gap: 8 }}>
        {MEAL_SLOTS.map((slot) => (
          <Button
            key={slot}
            title={slot}
            color={slot === mealSlot ? "#208AEF" : undefined}
            onPress={() => setMealSlot(slot)}
          />
        ))}
      </View>

      <Button
        title="Take a Photo"
        onPress={() => router.push("/meal-tracker/camera" as Href)}
      />

      <TextInput
        placeholder="Search foods"
        value={query}
        onChangeText={onSearch}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <FlatList
        data={results}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Button title={`${item.name} (${item.calories_per_serving} kcal)`} onPress={() => logFood(item)} />
        )}
      />

      <Text>Quick add (calories only)</Text>
      <TextInput
        placeholder="e.g. 250"
        keyboardType="numeric"
        value={quickAddCalories}
        onChangeText={setQuickAddCalories}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <Button title="Log Quick Add" onPress={logQuickAdd} />
    </SafeAreaView>
  );
}
