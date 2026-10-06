import { useFocusEffect, useRouter, type Href } from "expo-router";
import { ArrowDown, ArrowUp, Fire } from "phosphor-react-native";
import { useCallback, useState, type ReactNode } from "react";
import { ScrollView, Text, View } from "react-native";
import Animated from "react-native-reanimated";

import { Button, Card, ScreenContainer } from "@/components";
import { useEnter } from "@/lib/motion";
import { tint, useTheme } from "@/lib/theme";
import { getTodaysPrompt } from "@/modules/mental_health/api";
import { Heatmap, RankRow, Sparkline, StackedBar, TrendChart, WeekdayBars, moodColor } from "@/modules/mental_health/charts";
import { MOOD_COLORS, MOOD_LABEL, MOOD_OPTIONS, SCALES } from "@/modules/mental_health/content";
import { MoodIcon } from "@/modules/mental_health/MoodIcon";
import type { Driver, TrendPoint } from "@/modules/mental_health/stats";
import { useMindStats } from "@/modules/mental_health/useMindStats";

const average = (points: TrendPoint[]): number | null => {
  const values = points.map((p) => p.value).filter((v): v is number => v !== null);
  return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
};

/** Staggered entrance. The order of sections on screen is the order they arrive. */
function Reveal({ index, children }: { index: number; children: ReactNode }) {
  const entering = useEnter(index);
  return <Animated.View entering={entering}>{children}</Animated.View>;
}

export default function MentalHealthRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing, mode } = useTheme();
  const accent = pillars.mind[mode];
  const good = pillars.fuel[mode];
  const { stats, journals, loading, error } = useMindStats();
  const [prompt, setPrompt] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      getTodaysPrompt()
        .then((p) => setPrompt(p.prompt))
        .catch(() => setPrompt(null));
    }, [])
  );

  const goCheckIn = () => router.push("/mental-health/check-in" as Href);
  const sectionTitle = { fontFamily: font.extrabold, fontSize: 20, color: colors.textPrimary, letterSpacing: -0.3 } as const;
  const body = { fontFamily: font.regular, fontSize: 14, lineHeight: 20, color: colors.textSecondary } as const;
  const hairline = { height: 1, backgroundColor: colors.border } as const;

  const todayMood = stats.moodTrend14[stats.moodTrend14.length - 1]?.value ?? null;
  const total = stats.distribution.reduce((a, b) => a + b, 0);
  const topFeeling = stats.topEmotions[0]?.count ?? 1;
  const { lifts, drags } = stats.drivers;
  const change = stats.change7;
  const hasBodyData = average([...stats.energyTrend, ...stats.stressTrend, ...stats.sleepTrend]) !== null;

  const driverRow = (d: Driver, positive: boolean) => {
    const Arrow = positive ? ArrowUp : ArrowDown;
    const color = positive ? good : colors.danger;
    return (
      <View key={d.tag} style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm }}>
        <Arrow size={16} weight="bold" color={color} />
        <Text style={{ flex: 1, fontFamily: font.semibold, fontSize: 15, color: colors.textPrimary }}>{d.tag}</Text>
        <Text style={{ fontFamily: font.bold, fontSize: 14, color }}>
          {positive ? "+" : "-"}
          {Math.abs(d.delta).toFixed(1)}
        </Text>
        <Text style={{ fontFamily: font.regular, fontSize: 12, color: colors.textSecondary, width: 40, textAlign: "right" }}>{d.days} days</Text>
      </View>
    );
  };

  let i = 0;

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={{ gap: spacing.xl + 8, paddingBottom: spacing.xxxl }} showsVerticalScrollIndicator={false}>
        <Reveal index={i++}>
          <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
            <Text style={{ fontFamily: font.extrabold, fontSize: 32, letterSpacing: -0.8, color: colors.textPrimary }}>Mind</Text>
            {stats.streak > 0 ? (
              <View
                accessibilityLabel={`${stats.streak} day streak`}
                style={{ flexDirection: "row", alignItems: "center", gap: 6, paddingVertical: 6, paddingHorizontal: 12, borderRadius: 999, backgroundColor: tint(accent, 0.14) }}
              >
                <Fire size={18} weight="fill" color={accent} />
                <Text style={{ fontFamily: font.bold, fontSize: 14, color: accent }}>{stats.streak} days</Text>
              </View>
            ) : null}
          </View>
        </Reveal>
        {error ? <Text style={{ color: colors.danger }}>{error}</Text> : null}

        <Reveal index={i++}>
          <Card accent={accent} style={{ gap: spacing.md }}>
            {stats.checkedInToday && todayMood !== null ? (
              <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
                <MoodIcon score={todayMood} size={44} />
                <View style={{ flex: 1, gap: 2 }}>
                  <Text style={{ fontFamily: font.extrabold, fontSize: 18, color: colors.textPrimary }}>Logged for today</Text>
                  <Text style={body}>You are feeling {MOOD_LABEL[Math.round(todayMood)].toLowerCase()}. Moods shift, so add another any time.</Text>
                </View>
              </View>
            ) : (
              <View style={{ gap: 4 }}>
                <Text style={{ fontFamily: font.extrabold, fontSize: 22, letterSpacing: -0.4, color: colors.textPrimary }}>
                  {stats.hasData ? "How is today going?" : "Start with one check-in"}
                </Text>
                <Text style={body}>
                  {stats.hasData
                    ? "It takes about a minute and keeps your charts honest."
                    : "Five short steps. Your charts and patterns build from here."}
                </Text>
              </View>
            )}
            <Button title={stats.checkedInToday ? "Add another" : "Check in"} color={accent} onPress={goCheckIn} />
          </Card>
        </Reveal>

        {loading ? null : stats.hasData ? (
          <>
            <Reveal index={i++}>
              <View style={{ gap: spacing.md }}>
                <View style={{ flexDirection: "row", alignItems: "flex-end", justifyContent: "space-between" }}>
                  <View>
                    <Text style={body}>Mood this week</Text>
                    <Text style={{ fontFamily: font.extrabold, fontSize: 56, lineHeight: 62, letterSpacing: -2, color: colors.textPrimary }}>
                      {stats.average7 === null ? "-" : stats.average7.toFixed(1)}
                    </Text>
                  </View>
                  <View style={{ alignItems: "flex-end", gap: 6, paddingBottom: 8 }}>
                    {stats.average7 !== null ? <MoodIcon score={stats.average7} size={40} /> : null}
                    {change !== null && Math.abs(change) >= 0.15 ? (
                      <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
                        {change > 0 ? <ArrowUp size={14} weight="bold" color={good} /> : <ArrowDown size={14} weight="bold" color={colors.danger} />}
                        <Text style={{ fontFamily: font.bold, fontSize: 13, color: change > 0 ? good : colors.danger }}>
                          {Math.abs(change).toFixed(1)} vs last week
                        </Text>
                      </View>
                    ) : change !== null ? (
                      <Text style={{ fontFamily: font.medium, fontSize: 13, color: colors.textSecondary }}>Steady vs last week</Text>
                    ) : null}
                  </View>
                </View>
                <TrendChart points={stats.moodTrend14} color={accent} />
              </View>
            </Reveal>

            <Reveal index={i++}>
              <View style={{ flexDirection: "row" }}>
                {[
                  { value: String(stats.daysLogged), label: "days logged" },
                  { value: `${stats.longestStreak}`, label: "best streak" },
                  { value: String(stats.totalCheckIns), label: "check-ins" },
                ].map((s, idx) => (
                  <View
                    key={s.label}
                    style={{ flex: 1, paddingLeft: idx === 0 ? 0 : spacing.lg, borderLeftWidth: idx === 0 ? 0 : 1, borderLeftColor: colors.border }}
                  >
                    <Text style={{ fontFamily: font.extrabold, fontSize: 26, letterSpacing: -0.6, color: colors.textPrimary }}>{s.value}</Text>
                    <Text style={{ fontFamily: font.medium, fontSize: 12, color: colors.textSecondary }}>{s.label}</Text>
                  </View>
                ))}
              </View>
            </Reveal>

            <Reveal index={i++}>
              <View style={{ gap: spacing.md }}>
                <Text style={sectionTitle}>Last five weeks</Text>
                <Heatmap points={stats.heatmap} />
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                  <Text style={{ fontFamily: font.medium, fontSize: 11, color: colors.textSecondary }}>Rough</Text>
                  {MOOD_COLORS.map((c) => (
                    <View key={c} style={{ flex: 1, height: 8, borderRadius: 4, backgroundColor: c }} />
                  ))}
                  <Text style={{ fontFamily: font.medium, fontSize: 11, color: colors.textSecondary }}>Great</Text>
                </View>
              </View>
            </Reveal>

            <Reveal index={i++}>
              <View style={{ gap: spacing.md }}>
                <Text style={sectionTitle}>Your best days</Text>
                <Text style={body}>Average mood by weekday, with the strongest one in full colour.</Text>
                <WeekdayBars points={stats.weekday} color={accent} />
              </View>
            </Reveal>

            <Reveal index={i++}>
              <View style={{ gap: spacing.md }}>
                <Text style={sectionTitle}>Body and mind</Text>
                <View>
                  {SCALES.map((scale, idx) => {
                    const points = scale.key === "energy" ? stats.energyTrend : scale.key === "stress" ? stats.stressTrend : stats.sleepTrend;
                    const avg = average(points);
                    // For stress a high number is bad, so colour by the inverse.
                    const goodness = avg === null ? null : scale.key === "stress" ? 6 - avg : avg;
                    return (
                      <View
                        key={scale.key}
                        style={[
                          { flexDirection: "row", alignItems: "center", gap: spacing.lg, paddingVertical: spacing.md },
                          idx > 0 ? { borderTopWidth: 1, borderTopColor: colors.border } : null,
                        ]}
                      >
                        <View style={{ width: 76 }}>
                          <Text style={{ fontFamily: font.bold, fontSize: 15, color: colors.textPrimary }}>{scale.title}</Text>
                          <Text style={{ fontFamily: font.regular, fontSize: 12, color: colors.textSecondary }}>
                            {avg === null ? "no data" : `avg ${avg.toFixed(1)}`}
                          </Text>
                        </View>
                        <Sparkline points={points} color={goodness === null ? tint(colors.textSecondary, 0.5) : moodColor(goodness)} />
                      </View>
                    );
                  })}
                </View>
                {hasBodyData ? null : <Text style={body}>Rate energy, stress and sleep in a check-in to fill these in.</Text>}
              </View>
            </Reveal>

            <Reveal index={i++}>
              <View style={{ gap: spacing.md }}>
                <Text style={sectionTitle}>How you have felt</Text>
                <StackedBar counts={stats.distribution} />
                <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
                  {MOOD_OPTIONS.map((o) => (
                    <View key={o.score} style={{ alignItems: "center", gap: 2 }}>
                      <MoodIcon score={o.score} size={22} />
                      <Text style={{ fontFamily: font.bold, fontSize: 13, color: colors.textPrimary }}>{stats.distribution[o.score - 1]}</Text>
                      <Text style={{ fontFamily: font.regular, fontSize: 11, color: colors.textSecondary }}>{o.label}</Text>
                    </View>
                  ))}
                </View>
                {total > 0 && stats.topEmotions.length > 0 ? (
                  <View style={{ gap: spacing.md, marginTop: spacing.sm }}>
                    <Text style={{ fontFamily: font.bold, fontSize: 15, color: colors.textPrimary }}>Feelings that come up most</Text>
                    {stats.topEmotions.map((e) => (
                      <RankRow key={e.label} label={e.label} count={e.count} fraction={e.count / topFeeling} color={accent} />
                    ))}
                  </View>
                ) : null}
              </View>
            </Reveal>

            <Reveal index={i++}>
              <Card accent={lifts.length || drags.length ? accent : undefined} style={{ gap: spacing.md }}>
                <Text style={sectionTitle}>What moves your mood</Text>
                {lifts.length === 0 && drags.length === 0 ? (
                  <Text style={body}>
                    Tag what shaped each day. Once a factor shows up on a few days and is missing on a few others, helf compares your mood on both.
                  </Text>
                ) : (
                  <>
                    {lifts.map((d) => driverRow(d, true))}
                    {drags.map((d) => driverRow(d, false))}
                    <Text style={{ ...body, fontSize: 12 }}>A pattern in your own data, not proof of cause. Numbers show the mood difference on days with the factor.</Text>
                  </>
                )}
              </Card>
            </Reveal>
          </>
        ) : null}

        <Reveal index={i++}>
          <View style={{ gap: spacing.md }}>
            <View style={hairline} />
            <Text style={sectionTitle}>Journal</Text>
            <Text style={{ fontFamily: font.medium, fontSize: 16, lineHeight: 23, color: colors.textPrimary }}>{prompt ?? "Loading today's prompt..."}</Text>
            {journals.length > 0 ? (
              <Text style={body} numberOfLines={2}>
                Last entry, {new Date(journals[0].written_at).toLocaleDateString()}: {journals[0].body}
              </Text>
            ) : null}
            <View style={{ flexDirection: "row", gap: spacing.md }}>
              <View style={{ flex: 1 }}>
                <Button title="Write" variant="secondary" color={accent} onPress={() => router.push("/mental-health/journal" as Href)} />
              </View>
              <View style={{ flex: 1 }}>
                <Button title="History" variant="text" color={accent} onPress={() => router.push("/mental-health/history" as Href)} />
              </View>
            </View>
            <Text style={{ ...body, fontSize: 11, lineHeight: 16, textAlign: "center" }}>
              helf is a self-tracking tool, not a mental health service. If you are struggling, please talk to someone you trust or a professional.
            </Text>
          </View>
        </Reveal>
      </ScrollView>
    </ScreenContainer>
  );
}
