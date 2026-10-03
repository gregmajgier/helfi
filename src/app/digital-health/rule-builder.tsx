import { useRouter } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";

import { Button, Chip, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createScreenTimeRule } from "@/modules/digital_health/api";

const CATEGORY_OPTIONS = ["Social", "Games", "Video", "News", "Shopping", "Other"];

export default function RuleBuilderRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.focus.light;
  const [name, setName] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [limitMinutes, setLimitMinutes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const toggleCategory = (category: string) => {
    setCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    );
  };

  const save = async () => {
    setError(null);
    if (!name.trim()) {
      setError("Give the rule a name.");
      return;
    }
    if (categories.length === 0) {
      setError("Pick at least one category.");
      return;
    }
    setSaving(true);
    try {
      await createScreenTimeRule({
        name,
        apps_or_categories: categories,
        daily_limit_minutes: limitMinutes ? Number(limitMinutes) : undefined,
      });
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to save rule");
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScreenContainer>
      <Text style={{ fontFamily: font.bold, fontSize: 20, color: colors.textPrimary }}>New Rule</Text>
      <TextInput
        placeholder="Name (e.g. Evening wind-down)"
        value={name}
        onChangeText={setName}
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 12,
          padding: spacing.md,
          fontFamily: font.regular,
          color: colors.textPrimary,
        }}
      />
      <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textSecondary }}>
        Which apps?
      </Text>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        {CATEGORY_OPTIONS.map((category) => (
          <Chip
            key={category}
            label={category}
            selected={categories.includes(category)}
            onPress={() => toggleCategory(category)}
            color={accent}
          />
        ))}
      </View>
      <TextInput
        placeholder="Daily limit, minutes (optional)"
        value={limitMinutes}
        onChangeText={setLimitMinutes}
        keyboardType="number-pad"
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 12,
          padding: spacing.md,
          fontFamily: font.regular,
          color: colors.textPrimary,
        }}
      />
      {error ? <Text style={{ color: "#C0392B" }}>{error}</Text> : null}
      <Button title="Save rule" color={accent} onPress={save} disabled={saving} />
    </ScreenContainer>
  );
}
