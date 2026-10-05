import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";

import { Button, Chip, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import type { MealSlot } from "@/modules/meal_tracker/types";

const MEAL_SLOTS: MealSlot[] = ["breakfast", "lunch", "dinner", "snack"];

export default function AddEntryScreen() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.fuel.light;
  const [mealSlot, setMealSlot] = useState<MealSlot>("breakfast");
  const [description, setDescription] = useState("");

  return (
    <ScreenContainer>
      <View style={{ flexDirection: "row", gap: spacing.sm, flexWrap: "wrap" }}>
        {MEAL_SLOTS.map((slot) => (
          <Chip key={slot} label={slot} selected={slot === mealSlot} onPress={() => setMealSlot(slot)} color={accent} />
        ))}
      </View>

      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        <View style={{ flex: 1 }}>
          <Button
            title="Scan Barcode"
            variant="secondary"
            color={accent}
            onPress={() => router.push({ pathname: "/meal-tracker/barcode-scanner", params: { mealSlot } } as Href)}
          />
        </View>
        <View style={{ flex: 1 }}>
          <Button
            title="Take a Photo"
            variant="secondary"
            color={accent}
            onPress={() => router.push({ pathname: "/meal-tracker/camera", params: { mealSlot } } as Href)}
          />
        </View>
      </View>

      <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textSecondary }}>
        Or describe what you ate
      </Text>
      <TextInput
        placeholder="e.g. a bowl of oatmeal with banana and peanut butter"
        placeholderTextColor={colors.textSecondary}
        value={description}
        onChangeText={setDescription}
        multiline
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          padding: spacing.md,
          borderRadius: 12,
          fontFamily: font.regular,
          color: colors.textPrimary,
          backgroundColor: colors.surface,
          minHeight: 80,
          textAlignVertical: "top",
        }}
      />
      <Button
        title="Estimate nutrition"
        color={accent}
        disabled={!description.trim()}
        onPress={() =>
          router.push({
            pathname: "/meal-tracker/confirm-estimate",
            params: { description: description.trim(), mealSlot },
          } as Href)
        }
      />

      <Button
        title="Create custom food"
        variant="text"
        color={accent}
        onPress={() => router.push({ pathname: "/meal-tracker/custom-food", params: { mealSlot } } as Href)}
      />
    </ScreenContainer>
  );
}
