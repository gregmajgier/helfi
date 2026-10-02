import { StyleSheet, View } from "react-native";

import { useTheme } from "@/lib/theme";

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
        <View
          key={i}
          style={[
            styles.dot,
            { backgroundColor: i === activeIndex ? accent : colors.border, width: i === activeIndex ? 20 : 8 },
          ]}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: 6, justifyContent: "center" },
  dot: { height: 8, borderRadius: 4 },
});
