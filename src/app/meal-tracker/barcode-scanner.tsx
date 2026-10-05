import { CameraView, useCameraPermissions, type BarcodeScanningResult } from "expo-camera";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

import { Button, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createEntry, lookupBarcode } from "@/modules/meal_tracker/api";
import type { MealSlot } from "@/modules/meal_tracker/types";

export default function BarcodeScannerScreen() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.fuel.light;
  const { mealSlot } = useLocalSearchParams<{ mealSlot: MealSlot }>();
  const [permission, requestPermission] = useCameraPermissions();
  const [status, setStatus] = useState<"scanning" | "looking_up" | "error">("scanning");
  const [error, setError] = useState<string | null>(null);

  const onScanned = async (result: BarcodeScanningResult) => {
    if (status !== "scanning") return;
    setStatus("looking_up");
    try {
      const food = await lookupBarcode(result.data);
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
      setError(err instanceof Error ? err.message : "couldn't find that product");
      setStatus("error");
    }
  };

  if (!permission) {
    return <ScreenContainer>{null}</ScreenContainer>;
  }

  if (!permission.granted) {
    return (
      <ScreenContainer style={{ justifyContent: "center", alignItems: "center" }}>
        <Text style={{ fontFamily: font.medium, fontSize: 16, color: colors.textPrimary, textAlign: "center" }}>
          We need camera access to scan barcodes.
        </Text>
        <Button title="Grant camera access" color={accent} onPress={requestPermission} />
      </ScreenContainer>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <CameraView
        style={{ flex: 1 }}
        barcodeScannerSettings={{ barcodeTypes: ["ean13", "ean8", "upc_a", "upc_e"] }}
        onBarcodeScanned={onScanned}
      />
      <View
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          padding: spacing.lg,
          gap: spacing.sm,
          backgroundColor: colors.surface,
        }}
      >
        {status === "looking_up" ? (
          <Text style={{ fontFamily: font.medium, color: colors.textPrimary, textAlign: "center" }}>
            Looking up product…
          </Text>
        ) : status === "error" ? (
          <>
            <Text style={{ color: colors.danger, fontFamily: font.regular, textAlign: "center" }}>{error}</Text>
            <Button title="Try again" color={accent} onPress={() => setStatus("scanning")} />
          </>
        ) : (
          <Text style={{ fontFamily: font.regular, color: colors.textSecondary, textAlign: "center" }}>
            Point the camera at a barcode.
          </Text>
        )}
        <Button title="Cancel" variant="text" color={accent} onPress={() => router.back()} />
      </View>
    </View>
  );
}
