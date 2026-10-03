import { useRouter, type Href } from "expo-router";
import { Text } from "react-native";

import { Button, ScreenContainer } from "@/components";
import { APP_NAME, TAGLINE } from "@/lib/brand";
import { useTheme } from "@/lib/theme";

export default function OnboardingWelcomeRoute() {
  const router = useRouter();
  const { colors, font, spacing } = useTheme();

  return (
    <ScreenContainer style={{ justifyContent: "center", alignItems: "center", gap: spacing.lg }}>
      <Text style={{ fontFamily: font.extrabold, fontSize: 40, color: colors.textPrimary }}>{APP_NAME}</Text>
      <Text
        style={{ fontFamily: font.regular, fontSize: 16, color: colors.textSecondary, textAlign: "center" }}
      >
        {TAGLINE}
      </Text>
      <Button title="Get Started" onPress={() => router.push("/onboarding/pillars" as Href)} />
      <Button
        title="Already have an account? Log in"
        variant="text"
        onPress={() => router.push("/login" as Href)}
      />
    </ScreenContainer>
  );
}
