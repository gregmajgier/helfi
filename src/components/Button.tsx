import { StyleSheet, Text } from "react-native";

import { accentShadow, onAccent, tint, useTheme } from "@/lib/theme";

import { AnimatedPressable } from "./AnimatedPressable";

type ButtonVariant = "primary" | "secondary" | "text";

export function Button({
  title,
  onPress,
  variant = "primary",
  color,
  disabled = false,
}: {
  title: string;
  onPress: () => void;
  variant?: ButtonVariant;
  color?: string;
  disabled?: boolean;
}) {
  const { colors, font, spacing, radius } = useTheme();
  const accent = color ?? colors.textPrimary;

  const backgroundColor =
    variant === "primary" ? accent : variant === "secondary" ? tint(accent, 0.14) : "transparent";
  const textColor = variant === "primary" ? (color ? onAccent(color) : colors.background) : accent;

  return (
    <AnimatedPressable
      onPress={onPress}
      disabled={disabled}
      style={[
        styles.base,
        { backgroundColor, borderRadius: radius.md, paddingHorizontal: spacing.lg },
        variant === "primary" && color ? accentShadow(color) : null,
      ]}
    >
      <Text style={{ color: textColor, fontFamily: font.bold, fontSize: 16, textAlign: "center" }}>{title}</Text>
    </AnimatedPressable>
  );
}

const styles = StyleSheet.create({
  base: { minHeight: 52, alignItems: "center", justifyContent: "center" },
});
