import { Redirect, useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { ScrollView, Text, View } from "react-native";

import { Chip, PillarCard, RingCluster, ScreenContainer, StatTile } from "@/components";
import { useAuth } from "@/lib/auth-context";
import { isOnboardingComplete } from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";
import { rangeFor } from "@/modules/dashboard/summary";
import type { ViewMode } from "@/modules/dashboard/types";
import { useDashboardSummary } from "@/modules/dashboard/useDashboardSummary";
import { useScreenTimeSync } from "@/modules/screen_time";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function sameDay(a: Date, b: Date) {
  return a.toDateString() === b.toDateString();
}

function labelFor(anchor: Date, mode: ViewMode): { main: string; sub: string } {
  const today = new Date();
  const { days } = rangeFor(anchor, mode);
  const fmt = (d: Date) => `${MONTHS[d.getMonth()]} ${d.getDate()}`;
  if (mode === "day") {
    const yesterday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1);
    const main = sameDay(anchor, today) ? "Today" : sameDay(anchor, yesterday) ? "Yesterday" : fmt(anchor);
    return { main, sub: fmt(anchor) };
  }
  const thisWeek = sameDay(rangeFor(today, "week").days[0], days[0]);
  return { main: thisWeek ? "This week" : "Week of", sub: `${fmt(days[0])} - ${fmt(days[6])}` };
}

export default function Home() {
  const router = useRouter();
  const { user, isLoading, logout } = useAuth();
  const { colors, font, spacing, pillars, mode: theme } = useTheme();
  const [onboardingComplete, setOnboardingComplete] = useState<boolean | null>(null);
  const [mode, setMode] = useState<ViewMode>("day");
  const [anchor, setAnchor] = useState(() => new Date());
  const { summary, reload } = useDashboardSummary(anchor, mode, !!user);
  useScreenTimeSync(!!user);

  useFocusEffect(
    useCallback(() => {
      if (user) reload();
    }, [user, reload])
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

  const step = mode === "week" ? 7 : 1;
  const shift = (dir: number) => setAnchor((a) => new Date(a.getFullYear(), a.getMonth(), a.getDate() + dir * step));
  // eslint-disable-next-line react-hooks/purity -- range-in-future check is intentionally evaluated at render time
  const atPresent = rangeFor(anchor, mode).end.getTime() > Date.now();
  const label = labelFor(anchor, mode);
  const timeUnit = mode === "week" ? "Week rating" : "Day rating";
  const stats = summary?.stats;

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={{ gap: spacing.lg, paddingBottom: spacing.xl }} showsVerticalScrollIndicator={false}>
        <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
          <Text style={{ fontFamily: font.extrabold, fontSize: 28 }}>
            {["h", "e", "l", "f"].map((ch, i) => (
              <Text key={ch} style={{ color: pillars[(["move", "fuel", "mind", "focus"] as const)[i]][theme] }}>
                {ch}
              </Text>
            ))}
          </Text>
          <Text onPress={logout} style={{ fontFamily: font.medium, fontSize: 14, color: colors.textSecondary }}>
            Log out
          </Text>
        </View>

        <View style={{ flexDirection: "row", gap: spacing.sm, justifyContent: "center" }}>
          <Chip label="Day" selected={mode === "day"} onPress={() => setMode("day")} />
          <Chip label="Week" selected={mode === "week"} onPress={() => setMode("week")} />
        </View>

        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
          <Text onPress={() => shift(-1)} style={{ fontFamily: font.bold, fontSize: 28, color: colors.textPrimary, paddingHorizontal: spacing.md }}>
            {"\u2039"}
          </Text>
          <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textSecondary }}>{label.sub}</Text>
          <Text
            onPress={atPresent ? undefined : () => shift(1)}
            style={{ fontFamily: font.bold, fontSize: 28, color: colors.textPrimary, opacity: atPresent ? 0.25 : 1, paddingHorizontal: spacing.md }}
          >
            {"\u203A"}
          </Text>
        </View>

        <RingCluster rings={summary?.rings ?? []}>
          <Text style={{ fontFamily: font.extrabold, fontSize: 22, color: colors.textPrimary }}>{label.main}</Text>
        </RingCluster>

        <View style={{ flexDirection: "row", gap: spacing.sm }}>
          <StatTile index={0} value={stats?.caloriePercent == null ? "-" : `${stats.caloriePercent}%`} label="Calorie goal" />
          <StatTile index={1} value={stats ? `${stats.trainingHours}h` : "-"} label="Trained" />
          <StatTile index={2} value={stats?.screenTimeHours == null ? "-" : `${stats.screenTimeHours}h`} label="Screen time" />
          <StatTile index={3} value={stats?.rating == null ? "-" : `${stats.rating}/5`} label={timeUnit} />
        </View>

        <View style={{ gap: spacing.md }}>
          <PillarCard index={0} pillar="move" data={summary?.cards.move} onPress={() => router.push("/training-tracker" as Href)} />
          <PillarCard index={1} pillar="fuel" data={summary?.cards.fuel} onPress={() => router.push("/meal-tracker" as Href)} />
          <PillarCard index={2} pillar="mind" data={summary?.cards.mind} onPress={() => router.push("/mental-health" as Href)} />
          <PillarCard index={3} pillar="focus" data={summary?.cards.focus} onPress={() => router.push("/digital-health" as Href)} />
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
