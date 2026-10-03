import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

import { Button, ProgressDots, ScreenContainer } from "@/components";
import { useTheme, type PillarKey } from "@/lib/theme";

const SLIDES: { pillar: PillarKey; copy: string }[] = [
  { pillar: "move", copy: "Log workouts and watch your training add up." },
  { pillar: "fuel", copy: "Track meals without obsessing over every gram." },
  { pillar: "mind", copy: "A daily check-in and a place to write it out." },
  { pillar: "focus", copy: "Set the apps that eat your time — on your terms." },
];

export default function OnboardingPillarsRoute() {
  const router = useRouter();
  const { colors, pillars, mode, font, spacing } = useTheme();
  const [index, setIndex] = useState(0);
  const slide = SLIDES[index];
  const info = pillars[slide.pillar];
  const accent = info[mode];
  const isLast = index === SLIDES.length - 1;

  return (
    <ScreenContainer style={{ justifyContent: "space-between" }}>
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", gap: spacing.lg }}>
        <View
          style={{
            width: 96,
            height: 96,
            borderRadius: 24,
            backgroundColor: accent,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Text style={{ fontSize: 48 }}>{info.icon}</Text>
        </View>
        <Text style={{ fontFamily: font.extrabold, fontSize: 26, color: colors.textPrimary }}>{info.label}</Text>
        <Text
          style={{ fontFamily: font.regular, fontSize: 16, color: colors.textSecondary, textAlign: "center" }}
        >
          {slide.copy}
        </Text>
      </View>

      <ProgressDots count={SLIDES.length} activeIndex={index} color={accent} />
      <Button
        title={isLast ? "Let's set your goals" : "Next"}
        color={accent}
        onPress={() => {
          if (isLast) {
            router.push("/onboarding/goal-move" as Href);
          } else {
            setIndex((i) => i + 1);
          }
        }}
      />
    </ScreenContainer>
  );
}
