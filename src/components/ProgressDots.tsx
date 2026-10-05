import { StyleSheet, View } from "react-native";
import Animated, { useAnimatedStyle, withSpring } from "react-native-reanimated";

import { MOTION, useTheme } from "@/lib/theme";

function Dot({ active, accent, idle }: { active: boolean; accent: string; idle: string }) {
  const style = useAnimatedStyle(() => ({ width: withSpring(active ? 24 : 8, MOTION.spring) }));
  return <Animated.View style={[styles.dot, { backgroundColor: active ? accent : idle }, style]} />;
}

export function ProgressDots({
  count,
  activeIndex,
  color,
}: {
  count: number;
  activeIndex: number;
  color?: string;
}) {
  const { colors } = useTheme();
  const accent = color ?? colors.textPrimary;

  return (
    <View style={styles.row}>
      {Array.from({ length: count }, (_, i) => (
        <Dot key={i} active={i === activeIndex} accent={accent} idle={colors.border} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: 6, justifyContent: "center" },
  dot: { height: 8, borderRadius: 999 },
});
