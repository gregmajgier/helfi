import { Text } from "react-native";

import { onAccent, tint, useTheme } from "@/lib/theme";

import { AnimatedPressable } from "./AnimatedPressable";

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
  const { colors, font, spacing, radius } = useTheme();
  const accent = color ?? colors.textPrimary;

  return (
    <AnimatedPressable
      onPress={onPress}
      style={{
        backgroundColor: selected ? accent : tint(accent, 0.12),
        borderRadius: radius.pill,
        paddingVertical: spacing.sm + 2,
        paddingHorizontal: spacing.lg,
      }}
    >
      <Text
        style={{
          color: selected ? (color ? onAccent(color) : colors.background) : accent,
          fontFamily: font.semibold,
          fontSize: 14,
        }}
      >
        {label}
      </Text>
    </AnimatedPressable>
  );
}
