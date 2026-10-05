import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

import { AnimatedPressable, Button, ScreenContainer } from "@/components";
import { setPendingAnswer } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";

export default function OnboardingGoalMoveRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.move.light;
  const [goal, setGoal] = useState(3);

  const next = async () => {
    await setPendingAnswer("moveGoalPerWeek", goal);
    router.push("/onboarding/goal-fuel" as Href);
  };

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>
        How many workouts a week are you aiming for?
      </Text>
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.lg }}>
        <AnimatedPressable onPress={() => setGoal((g) => Math.max(1, g - 1))}>
          <Text style={{ fontSize: 32, color: accent }}>−</Text>
        </AnimatedPressable>
        <Text style={{ fontFamily: font.extrabold, fontSize: 48, color: colors.textPrimary }}>{goal}</Text>
        <AnimatedPressable onPress={() => setGoal((g) => Math.min(7, g + 1))}>
          <Text style={{ fontSize: 32, color: accent }}>+</Text>
        </AnimatedPressable>
      </View>
      <Button title="Next" color={accent} onPress={next} />
    </ScreenContainer>
  );
}
