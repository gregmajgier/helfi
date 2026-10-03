import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Text } from "react-native";

import { Button, Card, ScreenContainer } from "@/components";
import { getPendingAnswers, type FuelGoal, type OnboardingAnswers } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";

const FUEL_LABELS: Record<FuelGoal, string> = {
  lose: "Lose weight",
  maintain: "Maintain",
  build: "Build muscle",
  eat_healthier: "Eat healthier",
};

export default function OnboardingCompleteRoute() {
  const router = useRouter();
  const { colors, font, spacing } = useTheme();
  const [answers, setAnswers] = useState<OnboardingAnswers>({});

  useFocusEffect(
    useCallback(() => {
      getPendingAnswers().then(setAnswers);
    }, [])
  );

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>You're all set</Text>
      <Card>
        <Text style={{ color: colors.textPrimary }}>Move: {answers.moveGoalPerWeek ?? "—"} workouts/week</Text>
        <Text style={{ color: colors.textPrimary }}>
          Fuel: {answers.fuelGoal ? FUEL_LABELS[answers.fuelGoal] : "—"}
        </Text>
        <Text style={{ color: colors.textPrimary }}>Mind: check-in logged</Text>
        <Text style={{ color: colors.textPrimary }}>
          Focus: {answers.focusCategories?.length ?? 0} categories picked
        </Text>
      </Card>
      <Button title="Create your account" onPress={() => router.push("/register" as Href)} />
    </ScreenContainer>
  );
}
