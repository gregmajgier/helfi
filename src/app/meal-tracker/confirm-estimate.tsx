import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Image, Text, TextInput } from "react-native";

import { Button, Card, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createEntry, estimateFromDescription, estimateFromPhoto } from "@/modules/meal_tracker/api";
import type { MealSlot, PhotoEstimate } from "@/modules/meal_tracker/types";

export default function ConfirmEstimateScreen() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.fuel.light;
  const { photoUri, description, mealSlot } = useLocalSearchParams<{
    photoUri?: string;
    description?: string;
    mealSlot: MealSlot;
  }>();
  const [estimate, setEstimate] = useState<PhotoEstimate | null>(null);
  const [calories, setCalories] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const result = photoUri ? await estimateFromPhoto(photoUri) : await estimateFromDescription(description ?? "");
        setEstimate(result);
        setCalories(String(Math.round(result.calories)));
      } catch (err) {
        setError(err instanceof Error ? err.message : "estimate failed");
      }
    })();
  }, [photoUri, description]);

  const confirm = async () => {
    if (!estimate) return;
    try {
      await createEntry({
        meal_slot: mealSlot ?? "snack",
        source: photoUri ? "photo_ai" : "description_ai",
        logged_at: new Date().toISOString(),
        calories: Number(calories) || 0,
        protein_g: estimate.protein_g,
        carbs_g: estimate.carbs_g,
        fat_g: estimate.fat_g,
      });
      router.dismissAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to log meal");
    }
  };

  return (
    <ScreenContainer>
      {photoUri ? (
        <Image source={{ uri: photoUri }} style={{ width: "100%", height: 240, borderRadius: 18 }} />
      ) : (
        <Text style={{ fontFamily: font.medium, color: colors.textPrimary }}>&ldquo;{description}&rdquo;</Text>
      )}
      {error ? <Text style={{ color: colors.danger, fontFamily: font.regular }}>{error}</Text> : null}
      {estimate ? (
        <Card>
          <Text style={{ fontFamily: font.medium, color: colors.textPrimary }}>{estimate.description}</Text>
          <Text style={{ fontFamily: font.regular, color: colors.textSecondary }}>
            Confidence: {Math.round(estimate.confidence * 100)}%
          </Text>
          <Text style={{ fontFamily: font.semibold, color: colors.textSecondary, fontSize: 13 }}>
            Calories (edit if needed)
          </Text>
          <TextInput
            keyboardType="numeric"
            value={calories}
            onChangeText={setCalories}
            style={{
              borderWidth: 1,
              borderColor: colors.border,
              padding: spacing.md,
              borderRadius: 12,
              fontFamily: font.regular,
              color: colors.textPrimary,
              backgroundColor: colors.surface,
            }}
          />
          <Button title="Log This Meal" color={accent} onPress={confirm} />
        </Card>
      ) : !error ? (
        <Text style={{ fontFamily: font.medium, color: colors.textSecondary }}>Estimating…</Text>
      ) : null}
    </ScreenContainer>
  );
}
