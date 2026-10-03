import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

import { Button, Chip, ScreenContainer } from "@/components";
import { setPendingAnswer } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";

const CATEGORY_OPTIONS = ["Social", "Games", "Video", "News", "Shopping", "Other"];

export default function OnboardingGoalFocusRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.focus.light;
  const [categories, setCategories] = useState<string[]>([]);

  const toggle = (category: string) => {
    setCategories((prev) => (prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]));
  };

  const next = async () => {
    await setPendingAnswer("focusCategories", categories);
    router.push("/onboarding/notifications" as Href);
  };

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>
        Which apps tend to eat your time?
      </Text>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        {CATEGORY_OPTIONS.map((category) => (
          <Chip
            key={category}
            label={category}
            selected={categories.includes(category)}
            onPress={() => toggle(category)}
            color={accent}
          />
        ))}
      </View>
      <Button title="Next" color={accent} onPress={next} disabled={categories.length === 0} />
    </ScreenContainer>
  );
}
