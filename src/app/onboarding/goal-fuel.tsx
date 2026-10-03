import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

import { Button, Chip, ScreenContainer } from "@/components";
import { setPendingAnswer, type FuelGoal } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";

const FUEL_OPTIONS: { value: FuelGoal; label: string }[] = [
  { value: "lose", label: "Lose weight" },
  { value: "maintain", label: "Maintain" },
  { value: "build", label: "Build muscle" },
  { value: "eat_healthier", label: "Eat healthier" },
];

export default function OnboardingGoalFuelRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.fuel.light;
  const [goal, setGoal] = useState<FuelGoal | null>(null);

  const next = async () => {
    if (!goal) return;
    await setPendingAnswer("fuelGoal", goal);
    router.push("/onboarding/check-in-mind" as Href);
  };

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>
        What's your main food goal?
      </Text>
      <View style={{ gap: spacing.sm }}>
        {FUEL_OPTIONS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
            selected={goal === option.value}
            onPress={() => setGoal(option.value)}
            color={accent}
          />
        ))}
      </View>
      <Button title="Next" color={accent} onPress={next} disabled={!goal} />
    </ScreenContainer>
  );
}
