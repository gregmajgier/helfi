import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, ScrollView, Text, View } from "react-native";

import { Button, Card, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { deleteScreenTimeRule, listScreenTimeRules, updateScreenTimeRule } from "@/modules/digital_health/api";
import type { ScreenTimeRule } from "@/modules/digital_health/types";

export default function DigitalHealthRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.focus.light;
  const [rules, setRules] = useState<ScreenTimeRule[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      setRules(await listScreenTimeRules());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load rules");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const toggleRule = async (rule: ScreenTimeRule) => {
    try {
      await updateScreenTimeRule(rule.id, { enabled: !rule.enabled });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to update rule");
    }
  };

  const removeRule = (rule: ScreenTimeRule) => {
    Alert.alert("Delete rule?", "This can't be undone.", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            await deleteScreenTimeRule(rule.id);
            load();
          } catch (err) {
            setError(err instanceof Error ? err.message : "failed to delete rule");
          }
        },
      },
    ]);
  };

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={{ gap: spacing.md }}>
        <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>Focus</Text>
        {error ? <Text style={{ color: colors.danger }}>{error}</Text> : null}

        <Card style={{ borderColor: accent, borderWidth: 1.5 }}>
          <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textPrimary }}>
            Enforcement coming soon
          </Text>
          <Text style={{ fontFamily: font.regular, fontSize: 13, color: colors.textSecondary }}>
            You can set up rules now. Actually blocking apps on a schedule needs a deeper platform
            integration we haven&apos;t shipped yet — your rules are saved and ready for when it lands.
          </Text>
        </Card>

        {isLoading ? null : rules.length === 0 ? (
          <Text style={{ color: colors.textSecondary }}>No rules yet.</Text>
        ) : (
          rules.map((rule) => (
            <Card key={rule.id}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                <Text style={{ fontFamily: font.semibold, fontSize: 15, color: colors.textPrimary }}>
                  {rule.name}
                </Text>
                <Button
                  title={rule.enabled ? "Enabled" : "Disabled"}
                  variant={rule.enabled ? "primary" : "secondary"}
                  color={accent}
                  onPress={() => toggleRule(rule)}
                />
              </View>
              <Text style={{ fontFamily: font.regular, fontSize: 13, color: colors.textSecondary }}>
                {rule.apps_or_categories.join(", ")}
                {rule.daily_limit_minutes ? ` · ${rule.daily_limit_minutes} min/day` : ""}
              </Text>
              <Button title="Delete" variant="text" color={colors.danger} onPress={() => removeRule(rule)} />
            </Card>
          ))
        )}

        <Button
          title="Add rule"
          color={accent}
          onPress={() => router.push("/digital-health/rule-builder" as Href)}
        />
      </ScrollView>
    </ScreenContainer>
  );
}
