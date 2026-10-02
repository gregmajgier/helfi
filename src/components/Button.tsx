import { Pressable, StyleSheet, Text } from "react-native";

import { useTheme } from "@/lib/theme";

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
  const { colors, font, spacing } = useTheme();
  const accent = color ?? colors.textPrimary;

  const backgroundColor =
    variant === "primary" ? accent : variant === "secondary" ? colors.surface : "transparent";
  const textColor = variant === "primary" ? "#FFFFFF" : accent;

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.base,
        {
          backgroundColor,
          borderColor: accent,
          borderWidth: variant === "secondary" ? 1.5 : 0,
          paddingVertical: spacing.md,
          paddingHorizontal: spacing.lg,
          opacity: disabled ? 0.5 : pressed ? 0.8 : 1,
        },
      ]}
    >
      <Text style={{ color: textColor, fontFamily: font.semibold, fontSize: 16, textAlign: "center" }}>
        {title}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: { borderRadius: 14, alignItems: "center", justifyContent: "center" },
});
