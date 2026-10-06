import { useRouter } from "expo-router";
import { Alert, ScrollView, Text, View } from "react-native";

import { AnimatedPressable, ScreenContainer } from "@/components";
import { tint, useTheme } from "@/lib/theme";
import { deleteMoodEntry } from "@/modules/mental_health/api";
import { MOOD_COLORS, MOOD_LABEL } from "@/modules/mental_health/content";
import { MoodIcon } from "@/modules/mental_health/MoodIcon";
import { useMindStats } from "@/modules/mental_health/useMindStats";

export default function MentalHealthHistoryRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing, mode } = useTheme();
  const accent = pillars.mind[mode];
  const { entries, journals, error, reload } = useMindStats();

  const confirmDelete = (id: string) =>
    Alert.alert("Delete check-in?", "This can't be undone.", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          await deleteMoodEntry(id).catch(() => undefined);
          reload();
        },
      },
    ]);

  const sectionTitle = { fontFamily: font.extrabold, fontSize: 20, letterSpacing: -0.3, color: colors.textPrimary } as const;

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={{ gap: spacing.lg, paddingBottom: spacing.xxxl }} showsVerticalScrollIndicator={false}>
        <Text style={{ fontFamily: font.extrabold, fontSize: 32, letterSpacing: -0.8, color: colors.textPrimary }}>History</Text>
        {error ? <Text style={{ color: colors.danger }}>{error}</Text> : null}

        <Text style={sectionTitle}>Check-ins</Text>
        {entries.length === 0 ? (
          <Text style={{ fontFamily: font.regular, fontSize: 14, color: colors.textSecondary }}>
            Nothing here yet. Your first check-in will show up in this list.
          </Text>
        ) : (
          <View>
            {entries.slice(0, 60).map((e, idx) => {
              const chips = [...(e.emotions ?? []), ...e.tags];
              const metrics = [
                e.energy ? `energy ${e.energy}/5` : null,
                e.stress ? `stress ${e.stress}/5` : null,
                e.sleep_quality ? `sleep ${e.sleep_quality}/5` : null,
              ].filter(Boolean);
              return (
                <AnimatedPressable
                  key={e.id}
                  onLongPress={() => confirmDelete(e.id)}
                  accessibilityHint="Long press to delete"
                  style={[
                    { flexDirection: "row", gap: spacing.md, paddingVertical: spacing.md },
                    idx > 0 ? { borderTopWidth: 1, borderTopColor: colors.border } : null,
                  ]}
                >
                  <View style={{ width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: tint(MOOD_COLORS[e.mood_score - 1], 0.18) }}>
                    <MoodIcon score={e.mood_score} size={28} />
                  </View>
                  <View style={{ flex: 1, gap: 4 }}>
                    <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
                      <Text style={{ fontFamily: font.bold, fontSize: 16, color: colors.textPrimary }}>{MOOD_LABEL[e.mood_score]}</Text>
                      <Text style={{ fontFamily: font.regular, fontSize: 12, color: colors.textSecondary }}>
                        {new Date(e.logged_at).toLocaleString([], { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                      </Text>
                    </View>
                    {metrics.length > 0 ? (
                      <Text style={{ fontFamily: font.medium, fontSize: 12, color: colors.textSecondary }}>{metrics.join(", ")}</Text>
                    ) : null}
                    {chips.length > 0 ? (
                      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
                        {chips.map((c) => (
                          <View key={c} style={{ backgroundColor: tint(accent, 0.14), borderRadius: 999, paddingVertical: 3, paddingHorizontal: 10 }}>
                            <Text style={{ fontFamily: font.medium, fontSize: 12, color: accent }}>{c}</Text>
                          </View>
                        ))}
                      </View>
                    ) : null}
                    {e.note ? <Text style={{ fontFamily: font.regular, fontSize: 14, lineHeight: 20, color: colors.textPrimary }}>{e.note}</Text> : null}
                  </View>
                </AnimatedPressable>
              );
            })}
          </View>
        )}

        <Text style={{ ...sectionTitle, marginTop: spacing.md }}>Journal</Text>
        {journals.length === 0 ? (
          <Text style={{ fontFamily: font.regular, fontSize: 14, color: colors.textSecondary }}>No entries yet. Today&apos;s prompt is on the Mind screen.</Text>
        ) : (
          <View>
            {journals.map((j, idx) => (
              <View
                key={j.id}
                style={[{ gap: 4, paddingVertical: spacing.md }, idx > 0 ? { borderTopWidth: 1, borderTopColor: colors.border } : null]}
              >
                <Text style={{ fontFamily: font.medium, fontSize: 12, color: colors.textSecondary }}>
                  {new Date(j.written_at).toLocaleDateString()}
                  {j.prompt ? `, ${j.prompt}` : ""}
                </Text>
                <Text style={{ fontFamily: font.regular, fontSize: 15, lineHeight: 22, color: colors.textPrimary }}>{j.body}</Text>
              </View>
            ))}
          </View>
        )}

        <Text onPress={() => router.back()} style={{ textAlign: "center", color: accent, fontFamily: font.semibold, marginTop: spacing.md }}>
          Back to Mind
        </Text>
      </ScrollView>
    </ScreenContainer>
  );
}
