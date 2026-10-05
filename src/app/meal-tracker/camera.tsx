import * as ImagePicker from "expo-image-picker";
import { useLocalSearchParams, useRouter, type Href } from "expo-router";
import { useEffect } from "react";
import { Text } from "react-native";

import { ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import type { MealSlot } from "@/modules/meal_tracker/types";

export default function CameraScreen() {
  const router = useRouter();
  const { colors, font } = useTheme();
  const { mealSlot } = useLocalSearchParams<{ mealSlot: MealSlot }>();

  useEffect(() => {
    (async () => {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        router.back();
        return;
      }

      const result = await ImagePicker.launchCameraAsync({ quality: 0.7 });
      if (result.canceled) {
        router.back();
        return;
      }

      router.replace({
        pathname: "/meal-tracker/confirm-estimate",
        params: { photoUri: result.assets[0].uri, mealSlot },
      } as Href);
    })();
  }, [router, mealSlot]);

  return (
    <ScreenContainer style={{ justifyContent: "center", alignItems: "center" }}>
      <Text style={{ fontFamily: font.medium, fontSize: 16, color: colors.textSecondary }}>Opening camera…</Text>
    </ScreenContainer>
  );
}
