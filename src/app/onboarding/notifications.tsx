import { useRouter, type Href } from "expo-router";
import * as Notifications from "expo-notifications";
import { Platform, Text } from "react-native";

import { Button, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";

async function scheduleDailyMindReminder() {
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "Default Channel",
      importance: Notifications.AndroidImportance.MAX,
    });
  }
  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== "granted") {
    return;
  }
  await Notifications.scheduleNotificationAsync({
    content: { title: "helf", body: "Time for your Mind check-in." },
    trigger: { type: Notifications.SchedulableTriggerInputTypes.DAILY, hour: 20, minute: 0 },
  });
}

export default function OnboardingNotificationsRoute() {
  const router = useRouter();
  const { colors, font, spacing } = useTheme();

  const next = () => router.push("/onboarding/complete" as Href);

  const enable = async () => {
    try {
      await scheduleDailyMindReminder();
    } catch {
      // best-effort — a denied permission or an unsupported platform (e.g. web) must never block onboarding
    }
    next();
  };

  return (
    <ScreenContainer style={{ justifyContent: "center", gap: spacing.lg }}>
      <Text
        style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary, textAlign: "center" }}
      >
        Want a nudge for your Mind check-in?
      </Text>
      <Text
        style={{ fontFamily: font.regular, fontSize: 15, color: colors.textSecondary, textAlign: "center" }}
      >
        We'll remind you once a day at 8pm. You can ignore it any time.
      </Text>
      <Button title="Turn on reminders" onPress={enable} />
      <Button title="Not now" variant="text" onPress={next} />
    </ScreenContainer>
  );
}
