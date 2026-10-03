import { Redirect, useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Text, View } from "react-native";

import { PillarTile, ScreenContainer } from "@/components";
import { useAuth } from "@/lib/auth-context";
import { getMoveGoalPerWeek, isOnboardingComplete } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";
import { listScreenTimeRules } from "@/modules/digital_health/api";
import { listMoodEntries } from "@/modules/mental_health/api";
import { listWorkouts } from "@/modules/training_tracker/api";

type Statuses = { move: string; fuel: string; mind: string; focus: string };

const INITIAL_STATUSES: Statuses = {
  move: "Loading...",
  fuel: "Log today's meals",
  mind: "Loading...",
  focus: "Loading...",
};

export default function Home() {
  const router = useRouter();
  const { user, isLoading, logout } = useAuth();
  const { colors, font, spacing } = useTheme();
  const [onboardingComplete, setOnboardingComplete] = useState<boolean | null>(null);
  const [statuses, setStatuses] = useState<Statuses>(INITIAL_STATUSES);

  useFocusEffect(
    useCallback(() => {
      if (!user) return;
      (async () => {
        const [workouts, moveGoal, moods, rules] = await Promise.all([
          listWorkouts().catch(() => []),
          getMoveGoalPerWeek(),
          listMoodEntries().catch(() => []),
          listScreenTimeRules().catch(() => []),
        ]);
        const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
        const thisWeek = workouts.filter((w) => new Date(w.started_at).getTime() >= weekAgo).length;
        setStatuses({
          move: moveGoal ? `${thisWeek}/${moveGoal} workouts this week` : `${thisWeek} workouts this week`,
          fuel: "Log today's meals",
          mind:
            moods.length > 0
              ? `Last check-in ${new Date(moods[0].logged_at).toLocaleDateString()}`
              : "No check-ins yet",
          focus: `${rules.filter((r) => r.enabled).length} active rule${rules.filter((r) => r.enabled).length === 1 ? "" : "s"}`,
        });
      })();
    }, [user])
  );

  useFocusEffect(
    useCallback(() => {
      if (user) return;
      isOnboardingComplete().then(setOnboardingComplete);
    }, [user])
  );

  if (isLoading) {
    return null;
  }

  if (!user) {
    if (onboardingComplete === null) {
      return null;
    }
    return <Redirect href={(onboardingComplete ? "/login" : "/onboarding") as Href} />;
  }

  return (
    <ScreenContainer>
      <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>helf</Text>
        <Text onPress={logout} style={{ fontFamily: font.medium, fontSize: 14, color: colors.textSecondary }}>
          Log out
        </Text>
      </View>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.md }}>
        <PillarTile pillar="move" status={statuses.move} onPress={() => router.push("/training-tracker" as Href)} />
        <PillarTile pillar="fuel" status={statuses.fuel} onPress={() => router.push("/meal-tracker" as Href)} />
        <PillarTile pillar="mind" status={statuses.mind} onPress={() => router.push("/mental-health" as Href)} />
        <PillarTile pillar="focus" status={statuses.focus} onPress={() => router.push("/digital-health" as Href)} />
      </View>
    </ScreenContainer>
  );
}
