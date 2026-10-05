import { useRouter, type Href } from "expo-router";
import { Text, View } from "react-native";

import { AnimatedPressable, ScreenContainer } from "@/components";
import { setPendingAnswer } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";

const MOOD_OPTIONS: { score: number; emoji: string; label: string }[] = [
  { score: 1, emoji: "😞", label: "Rough" },
  { score: 2, emoji: "🙁", label: "Low" },
  { score: 3, emoji: "😐", label: "Okay" },
  { score: 4, emoji: "🙂", label: "Good" },
  { score: 5, emoji: "😄", label: "Great" },
];

export default function OnboardingCheckInMindRoute() {
  const router = useRouter();
  const { colors, font, spacing } = useTheme();

  const pick = async (score: number) => {
    await setPendingAnswer("mindMoodScore", score);
    router.push("/onboarding/goal-focus" as Href);
  };

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text
        style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary, textAlign: "center" }}
      >
        How are you feeling right now?
      </Text>
      <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
        {MOOD_OPTIONS.map((option) => (
          <AnimatedPressable
            key={option.score}
            onPress={() => pick(option.score)}
            style={{ alignItems: "center", gap: 4 }}
          >
            <Text style={{ fontSize: 32 }}>{option.emoji}</Text>
            <Text style={{ fontFamily: font.regular, fontSize: 12, color: colors.textSecondary }}>
              {option.label}
            </Text>
          </AnimatedPressable>
        ))}
      </View>
    </ScreenContainer>
  );
}
