import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";

import { Button, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createCustomFood, createEntry } from "@/modules/meal_tracker/api";
import type { MealSlot } from "@/modules/meal_tracker/types";

function inputStyle(colors: ReturnType<typeof useTheme>["colors"], font: ReturnType<typeof useTheme>["font"], spacing: ReturnType<typeof useTheme>["spacing"]) {
  return {
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    borderRadius: 12,
    fontFamily: font.regular,
    color: colors.textPrimary,
    backgroundColor: colors.surface,
  } as const;
}

export default function CustomFoodScreen() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.fuel.light;
  const { mealSlot } = useLocalSearchParams<{ mealSlot: MealSlot }>();
  const [name, setName] = useState("");
  const [calories, setCalories] = useState("");
  const [protein, setProtein] = useState("");
  const [carbs, setCarbs] = useState("");
  const [fat, setFat] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const style = inputStyle(colors, font, spacing);

  const save = async () => {
    const parsedCalories = Number(calories);
    if (!name.trim()) {
      setError("Give this food a name.");
      return;
    }
    if (!Number.isFinite(parsedCalories) || parsedCalories <= 0) {
      setError("Enter a valid calorie count.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const food = await createCustomFood({
        name: name.trim(),
        serving_size: 1,
        serving_unit: "serving",
        calories_per_serving: parsedCalories,
        protein_g: Number(protein) || 0,
        carbs_g: Number(carbs) || 0,
        fat_g: Number(fat) || 0,
      });
      await createEntry({
        meal_slot: (mealSlot as MealSlot) ?? "snack",
        source: "search",
        logged_at: new Date().toISOString(),
        food_id: food.id,
        calories: food.calories_per_serving,
        protein_g: food.protein_g,
        carbs_g: food.carbs_g,
        fat_g: food.fat_g,
      });
      router.dismissAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to save custom food");
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScreenContainer>
      <Text style={{ fontFamily: font.bold, fontSize: 20, color: colors.textPrimary }}>Create custom food</Text>
      <TextInput placeholder="Name" placeholderTextColor={colors.textSecondary} value={name} onChangeText={setName} style={style} />
      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        <TextInput
          placeholder="Calories"
          placeholderTextColor={colors.textSecondary}
          keyboardType="numeric"
          value={calories}
          onChangeText={setCalories}
          style={[style, { flex: 1 }]}
        />
      </View>
      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        <TextInput
          placeholder="Protein (g)"
          placeholderTextColor={colors.textSecondary}
          keyboardType="numeric"
          value={protein}
          onChangeText={setProtein}
          style={[style, { flex: 1 }]}
        />
        <TextInput
          placeholder="Carbs (g)"
          placeholderTextColor={colors.textSecondary}
          keyboardType="numeric"
          value={carbs}
          onChangeText={setCarbs}
          style={[style, { flex: 1 }]}
        />
        <TextInput
          placeholder="Fat (g)"
          placeholderTextColor={colors.textSecondary}
          keyboardType="numeric"
          value={fat}
          onChangeText={setFat}
          style={[style, { flex: 1 }]}
        />
      </View>
      {error ? <Text style={{ color: colors.danger, fontFamily: font.regular }}>{error}</Text> : null}
      <Button title="Save and log" color={accent} onPress={save} disabled={saving} />
    </ScreenContainer>
  );
}
