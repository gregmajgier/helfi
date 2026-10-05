import { useMemo, useState } from "react";
import { FlatList, Modal, Text, TextInput, View } from "react-native";

import { AnimatedPressable, Button, ScreenContainer } from "@/components";
import { onAccent, tint, useTheme } from "@/lib/theme";

import type { InstalledApp } from "./types";

export function ExcludedAppsPicker({
  visible,
  apps,
  initiallyExcluded,
  onDone,
  onCancel,
}: {
  visible: boolean;
  apps: InstalledApp[];
  initiallyExcluded: string[];
  onDone: (excluded: string[]) => void;
  onCancel: () => void;
}) {
  const { colors, font, spacing, radius, pillars, mode } = useTheme();
  const accent = pillars.focus[mode];
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(() => new Set(initiallyExcluded));

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? apps.filter((a) => a.label.toLowerCase().includes(q)) : apps;
  }, [apps, query]);

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onCancel}>
      <ScreenContainer>
        <Text style={{ fontFamily: font.extrabold, fontSize: 22, color: colors.textPrimary }}>Productive apps</Text>
        <Text style={{ fontFamily: font.regular, fontSize: 13, color: colors.textSecondary }}>
          Time in these apps does not count towards your Focus budget. This list stays on your phone.
        </Text>
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="Search apps"
          placeholderTextColor={colors.textSecondary}
          autoCorrect={false}
          autoCapitalize="none"
          maxLength={60}
          style={{
            fontFamily: font.regular,
            fontSize: 15,
            color: colors.textPrimary,
            backgroundColor: colors.surface,
            borderColor: colors.border,
            borderWidth: 1,
            borderRadius: radius.md,
            paddingHorizontal: spacing.lg,
            paddingVertical: spacing.md,
          }}
        />
        <FlatList
          data={shown}
          keyExtractor={(a) => a.id}
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{ gap: spacing.sm }}
          ListEmptyComponent={
            <Text style={{ fontFamily: font.regular, color: colors.textSecondary }}>No apps match.</Text>
          }
          renderItem={({ item }) => {
            const on = selected.has(item.id);
            return (
              <AnimatedPressable
                onPress={() => toggle(item.id)}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  gap: spacing.md,
                  padding: spacing.md,
                  borderRadius: radius.md,
                  backgroundColor: on ? tint(accent, 0.14) : colors.surface,
                }}
              >
                <View
                  style={{
                    width: 24,
                    height: 24,
                    borderRadius: radius.pill,
                    borderWidth: 2,
                    borderColor: accent,
                    backgroundColor: on ? accent : "transparent",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  {on ? <Text style={{ color: onAccent(accent), fontSize: 14, fontFamily: font.bold }}>✓</Text> : null}
                </View>
                <Text style={{ flex: 1, fontFamily: font.semibold, fontSize: 15, color: colors.textPrimary }} numberOfLines={1}>
                  {item.label}
                </Text>
              </AnimatedPressable>
            );
          }}
        />
        <View style={{ flexDirection: "row", gap: spacing.md }}>
          <View style={{ flex: 1 }}>
            <Button title="Cancel" variant="secondary" color={accent} onPress={onCancel} />
          </View>
          <View style={{ flex: 1 }}>
            <Button title={`Save (${selected.size})`} color={accent} onPress={() => onDone([...selected])} />
          </View>
        </View>
      </ScreenContainer>
    </Modal>
  );
}
