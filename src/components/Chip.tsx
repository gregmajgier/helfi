import { Pressable, StyleSheet, Text } from "react-native";

import { useTheme } from "@/lib/theme";

export function Chip({
  label,
  selected,
  onPress,
  color,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
  color?: string;
}) {
  const { colors, font, spacing } = useTheme();
  const accent = color ?? colors.textPrimary;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        {
          backgroundColor: selected ? accent : colors.surface,
          borderColor: accent,
          paddingVertical: spacing.sm,
          paddingHorizontal: spacing.lg,
          opacity: pressed ? 0.85 : 1,
        },
      ]}
    >
      <Text style={{ color: selected ? "#FFFFFF" : accent, fontFamily: font.medium, fontSize: 14 }}>
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: { borderRadius: 999, borderWidth: 1.5 },
});
