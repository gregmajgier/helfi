import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Button, Image, SafeAreaView, Text, TextInput, View } from "react-native";

import { createEntry, estimateFromPhoto } from "@/modules/meal_tracker/api";
import type { PhotoEstimate } from "@/modules/meal_tracker/types";

export default function ConfirmEstimateScreen() {
  const router = useRouter();
  const { photoUri } = useLocalSearchParams<{ photoUri: string }>();
  const [estimate, setEstimate] = useState<PhotoEstimate | null>(null);
  const [calories, setCalories] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const result = await estimateFromPhoto(photoUri);
        setEstimate(result);
        setCalories(String(Math.round(result.calories)));
      } catch (err) {
        setError(err instanceof Error ? err.message : "estimate failed");
      }
    })();
  }, [photoUri]);

  const confirm = async () => {
    if (!estimate) return;
    try {
      await createEntry({
        meal_slot: "snack",
        source: "photo_ai",
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
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      <Image source={{ uri: photoUri }} style={{ width: "100%", height: 240, borderRadius: 8 }} />
      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}
      {estimate ? (
        <View style={{ gap: 8 }}>
          <Text>{estimate.description}</Text>
          <Text>Confidence: {Math.round(estimate.confidence * 100)}%</Text>
          <Text>Calories (edit if needed):</Text>
          <TextInput
            keyboardType="numeric"
            value={calories}
            onChangeText={setCalories}
            style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
          />
          <Button title="Log This Meal" onPress={confirm} />
        </View>
      ) : !error ? (
        <Text>Estimating…</Text>
      ) : null}
    </SafeAreaView>
  );
}
