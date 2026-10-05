import type { ReactNode } from "react";
import { StyleSheet, View, type ViewStyle } from "react-native";

import { cardShadow, tint, useTheme } from "@/lib/theme";

export function Card({
  children,
  style,
  accent,
}: {
  children: ReactNode;
  style?: ViewStyle;
  accent?: string;
}) {
  const { colors, spacing, radius, mode } = useTheme();
  return (
    <View
      style={[
        styles.base,
        {
          backgroundColor: accent ? tint(accent, mode === "dark" ? 0.16 : 0.12) : colors.surface,
          borderColor: colors.border,
          borderWidth: mode === "dark" && !accent ? 1 : 0,
          borderRadius: radius.lg,
          padding: spacing.lg,
        },
        accent ? null : cardShadow(mode),
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  base: { gap: 8 },
});
