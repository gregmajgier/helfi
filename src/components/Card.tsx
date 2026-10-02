import type { ReactNode } from "react";
import { StyleSheet, View, type ViewStyle } from "react-native";

import { useTheme } from "@/lib/theme";

export function Card({ children, style }: { children: ReactNode; style?: ViewStyle }) {
  const { colors, spacing } = useTheme();
  return (
    <View
      style={[
        styles.base,
        { backgroundColor: colors.surface, borderColor: colors.border, padding: spacing.lg },
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  base: { borderRadius: 18, borderWidth: 1, gap: 8 },
});
