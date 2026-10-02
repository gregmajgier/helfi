import type { ReactNode } from "react";
import { SafeAreaView, View, type ViewStyle } from "react-native";

import { useTheme } from "@/lib/theme";

export function ScreenContainer({
  children,
  style,
}: {
  children: ReactNode;
  style?: ViewStyle;
}) {
  const { colors, spacing } = useTheme();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
      <View style={[{ flex: 1, padding: spacing.lg, gap: spacing.md }, style]}>{children}</View>
    </SafeAreaView>
  );
}
