import { StyleSheet, Text, View } from "react-native";
import Animated from "react-native-reanimated";

import { useEnter } from "@/lib/motion";
import { accentShadow, tint, useTheme, type PillarKey } from "@/lib/theme";
import type { PillarCardData } from "@/modules/dashboard/types";

import { AnimatedPressable } from "./AnimatedPressable";
import { PillarIcon } from "./PillarIcon";

export function PillarCard({
  pillar,
  data,
  onPress,
  index = 0,
}: {
  pillar: PillarKey;
  data: PillarCardData | undefined;
  onPress: () => void;
  index?: number;
}) {
  const { colors, mode, pillars, font, spacing, radius } = useTheme();
  const info = pillars[pillar];
  const accent = info[mode];
  const entering = useEnter(index);

  return (
    <Animated.View entering={entering}>
      <AnimatedPressable
        onPress={onPress}
        style={[
          styles.base,
          { backgroundColor: tint(accent, mode === "dark" ? 0.18 : 0.14), borderRadius: radius.lg, padding: spacing.lg },
          accentShadow(accent),
        ]}
      >
        <View style={styles.header}>
          <View style={[styles.iconBadge, { backgroundColor: tint(accent, 0.28) }]}>
            <PillarIcon pillar={pillar} size={22} />
          </View>
          <Text style={{ flex: 1, fontFamily: font.extrabold, fontSize: 18, color: colors.textPrimary }}>{info.label}</Text>
          <Text style={{ fontFamily: font.bold, fontSize: 20, color: colors.textSecondary }}>{"›"}</Text>
        </View>

        {data ? (
          <>
            <View style={styles.headlineRow}>
              <Text style={{ fontFamily: font.extrabold, fontSize: 32, color: colors.textPrimary }}>{data.headline}</Text>
              <Text style={{ flexShrink: 1, fontFamily: font.medium, fontSize: 13, color: colors.textSecondary }}>{data.caption}</Text>
            </View>

            {data.progress !== null && (
              <View style={[styles.track, { backgroundColor: tint(accent, 0.22) }]}>
                <View style={{ width: `${Math.round(data.progress * 100)}%`, height: "100%", borderRadius: 999, backgroundColor: accent }} />
              </View>
            )}

            {data.details.length > 0 && (
              <View style={styles.details}>
                {data.details.map((d) => (
                  <View key={d.label} style={{ flex: 1 }}>
                    <Text style={{ fontFamily: font.bold, fontSize: 15, color: colors.textPrimary }}>{d.value}</Text>
                    <Text style={{ fontFamily: font.medium, fontSize: 11, color: colors.textSecondary }}>{d.label}</Text>
                  </View>
                ))}
              </View>
            )}
          </>
        ) : (
          <Text style={{ fontFamily: font.medium, fontSize: 13, color: colors.textSecondary }}>Loading...</Text>
        )}
      </AnimatedPressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  base: { gap: 12 },
  header: { flexDirection: "row", alignItems: "center", gap: 10 },
  iconBadge: { width: 36, height: 36, borderRadius: 999, alignItems: "center", justifyContent: "center" },
  headlineRow: { flexDirection: "row", alignItems: "baseline", gap: 8 },
  track: { height: 8, borderRadius: 999, overflow: "hidden" },
  details: { flexDirection: "row", gap: 12 },
});
