import { StyleSheet, Text, View } from "react-native";
import Animated from "react-native-reanimated";

import { useEnter } from "@/lib/motion";
import { accentShadow, tint, useTheme, type PillarKey } from "@/lib/theme";

import { AnimatedPressable } from "./AnimatedPressable";
import { PillarIcon } from "./PillarIcon";

export function PillarTile({
  pillar,
  status,
  onPress,
  index = 0,
}: {
  pillar: PillarKey;
  status: string;
  onPress: () => void;
  index?: number;
}) {
  const { colors, mode, pillars, font, spacing, radius } = useTheme();
  const info = pillars[pillar];
  const accent = info[mode];
  const entering = useEnter(index);

  return (
    <Animated.View entering={entering} style={styles.cell}>
      <AnimatedPressable
        onPress={onPress}
        style={[
          styles.base,
          { backgroundColor: tint(accent, mode === "dark" ? 0.18 : 0.14), borderRadius: radius.lg, padding: spacing.lg },
          accentShadow(accent),
        ]}
      >
        <View style={[styles.iconBadge, { backgroundColor: tint(accent, 0.28) }]}>
          <PillarIcon pillar={pillar} size={26} />
        </View>
        <Text style={{ fontFamily: font.extrabold, fontSize: 20, color: colors.textPrimary }}>{info.label}</Text>
        <Text style={{ fontFamily: font.medium, fontSize: 13, color: colors.textSecondary }}>{status}</Text>
      </AnimatedPressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  cell: { flexBasis: "47%", flexGrow: 1 },
  base: { gap: 6 },
  iconBadge: { width: 44, height: 44, borderRadius: 999, alignItems: "center", justifyContent: "center" },
});
