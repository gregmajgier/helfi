import { useRouter } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, Text, TextInput, View } from "react-native";

import { Check } from "phosphor-react-native";

import { AnimatedPressable, Button, Chip, ProgressDots, ScreenContainer } from "@/components";
import { onAccent, tint, useTheme } from "@/lib/theme";
import { createMoodEntry } from "@/modules/mental_health/api";
import { EMOTION_GROUPS, FACTORS, MOOD_COLORS, MOOD_OPTIONS, SCALES, type ScaleKey } from "@/modules/mental_health/content";
import { MoodIcon } from "@/modules/mental_health/MoodIcon";

const STEPS = ["Mood", "Feelings", "Body & mind", "Influences", "Note"] as const;
const MAX_EMOTIONS = 5;
const NOTE_LIMIT = 500;

function toggle(list: string[], item: string, max = Infinity): string[] {
  if (list.includes(item)) return list.filter((x) => x !== item);
  return list.length >= max ? list : [...list, item];
}

export default function CheckInRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing, radius, mode } = useTheme();
  const accent = pillars.mind[mode];

  const [step, setStep] = useState(0);
  const [mood, setMood] = useState<number | null>(null);
  const [emotions, setEmotions] = useState<string[]>([]);
  const [scales, setScales] = useState<Partial<Record<ScaleKey, number>>>({});
  const [factors, setFactors] = useState<string[]>([]);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const last = step === STEPS.length - 1;

  const save = async () => {
    if (mood === null) return;
    setSaving(true);
    setError(null);
    try {
      await createMoodEntry({
        logged_at: new Date().toISOString(),
        mood_score: mood,
        ...scales,
        emotions,
        tags: factors,
        note: note.trim() || undefined,
      });
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to save check-in");
      setSaving(false);
    }
  };

  const heading = { fontFamily: font.extrabold, fontSize: 28, letterSpacing: -0.6, color: colors.textPrimary } as const;
  const sub = { fontFamily: font.regular, fontSize: 15, lineHeight: 21, color: colors.textSecondary } as const;

  return (
    <ScreenContainer>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <ProgressDots count={STEPS.length} activeIndex={step} color={accent} />
        <ScrollView contentContainerStyle={{ gap: spacing.lg, paddingVertical: spacing.lg }} keyboardShouldPersistTaps="handled">
          {step === 0 ? (
            <>
              <Text style={heading}>How are you feeling right now?</Text>
              <Text style={sub}>Pick the one that fits best. You can add detail next.</Text>
              <View style={{ gap: spacing.sm }}>
                {MOOD_OPTIONS.slice()
                  .reverse()
                  .map((o) => {
                    const selected = mood === o.score;
                    const fill = MOOD_COLORS[o.score - 1];
                    return (
                      <AnimatedPressable
                        key={o.score}
                        accessibilityRole="button"
                        accessibilityLabel={`${o.label}. ${o.hint}`}
                        accessibilityState={{ selected }}
                        onPress={() => setMood(o.score)}
                        style={{
                          flexDirection: "row",
                          alignItems: "center",
                          gap: spacing.md,
                          padding: spacing.md,
                          borderRadius: radius.md,
                          backgroundColor: selected ? fill : tint(fill, 0.12),
                        }}
                      >
                        <View style={{ width: 48, height: 48, borderRadius: 24, alignItems: "center", justifyContent: "center", backgroundColor: selected ? "rgba(255,255,255,0.55)" : tint(fill, 0.2) }}>
                          <MoodIcon score={o.score} size={32} color={selected ? "#14151F" : fill} />
                        </View>
                        <View style={{ flex: 1 }}>
                          <Text style={{ fontFamily: font.bold, fontSize: 18, color: selected ? onAccent(fill) : colors.textPrimary }}>{o.label}</Text>
                          <Text style={{ fontFamily: font.regular, fontSize: 13, color: selected ? onAccent(fill) : colors.textSecondary }}>{o.hint}</Text>
                        </View>
                        {selected ? <Check size={22} weight="bold" color={onAccent(fill)} /> : null}
                      </AnimatedPressable>
                    );
                  })}
              </View>
            </>
          ) : null}

          {step === 1 ? (
            <>
              <Text style={heading}>What are you feeling?</Text>
              <Text style={sub}>Naming a feeling helps. Pick up to {MAX_EMOTIONS}, or skip.</Text>
              {EMOTION_GROUPS.map((group) => (
                <View key={group.title} style={{ gap: spacing.sm }}>
                  <Text style={{ fontFamily: font.semibold, fontSize: 13, color: colors.textSecondary }}>{group.title}</Text>
                  <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                    {group.emotions.map((e) => (
                      <Chip key={e} label={e} color={accent} selected={emotions.includes(e)} onPress={() => setEmotions((prev) => toggle(prev, e, MAX_EMOTIONS))} />
                    ))}
                  </View>
                </View>
              ))}
            </>
          ) : null}

          {step === 2 ? (
            <>
              <Text style={heading}>Body and mind</Text>
              <Text style={sub}>Three quick reads. Skip any you are unsure about.</Text>
              {SCALES.map((scale) => {
                const value = scales[scale.key];
                return (
                  <View key={scale.key} style={{ gap: spacing.sm }}>
                    <Text style={{ fontFamily: font.semibold, fontSize: 15, color: colors.textPrimary }}>{scale.question}</Text>
                    <View style={{ flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs }}>
                      {[1, 2, 3, 4, 5].map((n) => {
                        const selected = value === n;
                        return (
                          <AnimatedPressable
                            key={n}
                            accessibilityRole="button"
                            accessibilityLabel={`${scale.title} ${n} of 5, ${scale.labels[n - 1]}`}
                            accessibilityState={{ selected }}
                            onPress={() => setScales((prev) => (prev[scale.key] === n ? { ...prev, [scale.key]: undefined } : { ...prev, [scale.key]: n }))}
                            style={{
                              flex: 1,
                              height: 46,
                              alignItems: "center",
                              justifyContent: "center",
                              borderRadius: radius.sm,
                              backgroundColor: selected ? accent : tint(accent, 0.12),
                            }}
                          >
                            <Text style={{ fontFamily: font.bold, fontSize: 16, color: selected ? onAccent(accent) : accent }}>{n}</Text>
                          </AnimatedPressable>
                        );
                      })}
                    </View>
                    <Text style={{ fontFamily: font.medium, fontSize: 12, color: colors.textSecondary, minHeight: 16 }}>
                      {value ? scale.labels[value - 1] : `${scale.labels[0]} to ${scale.labels[4]}`}
                    </Text>
                  </View>
                );
              })}
            </>
          ) : null}

          {step === 3 ? (
            <>
              <Text style={heading}>What shaped today?</Text>
              <Text style={sub}>Over time helf shows which of these lift or drag your mood.</Text>
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                {FACTORS.map((f) => (
                  <Chip key={f} label={f} color={accent} selected={factors.includes(f)} onPress={() => setFactors((prev) => toggle(prev, f))} />
                ))}
              </View>
            </>
          ) : null}

          {step === 4 ? (
            <>
              <Text style={heading}>Anything to add?</Text>
              <Text style={sub}>Optional. A line or two is plenty.</Text>
              <TextInput
                value={note}
                onChangeText={(t) => setNote(t.slice(0, NOTE_LIMIT))}
                placeholder="What is on your mind?"
                placeholderTextColor={colors.textSecondary}
                multiline
                style={{
                  minHeight: 120,
                  textAlignVertical: "top",
                  borderWidth: 1,
                  borderColor: colors.border,
                  borderRadius: radius.sm,
                  padding: spacing.md,
                  fontFamily: font.regular,
                  fontSize: 15,
                  color: colors.textPrimary,
                }}
              />
              <Text style={{ ...sub, fontSize: 12, textAlign: "right" }}>
                {note.length}/{NOTE_LIMIT}
              </Text>
              {error ? <Text style={{ color: colors.danger }}>{error}</Text> : null}
            </>
          ) : null}
        </ScrollView>

        <View style={{ flexDirection: "row", gap: spacing.md }}>
          {step > 0 ? (
            <View style={{ flex: 1 }}>
              <Button title="Back" variant="secondary" color={accent} onPress={() => setStep(step - 1)} disabled={saving} />
            </View>
          ) : null}
          <View style={{ flex: 2 }}>
            {last ? (
              <Button title={saving ? "Saving..." : "Save check-in"} color={accent} onPress={save} disabled={saving || mood === null} />
            ) : (
              <Button title="Next" color={accent} onPress={() => setStep(step + 1)} disabled={mood === null} />
            )}
          </View>
        </View>
      </KeyboardAvoidingView>
    </ScreenContainer>
  );
}
