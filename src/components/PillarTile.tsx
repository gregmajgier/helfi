import { Pressable, StyleSheet, Text, View } from "react-native";

import { useTheme, type PillarKey } from "@/lib/theme";

export function PillarTile({
  pillar,
  status,
  onPress,
}: {
  pillar: PillarKey;
  status: string;
  onPress: () => void;
}) {
  const { colors, mode, pillars, font, spacing } = useTheme();
  const info = pillars[pillar];
  const accent = info[mode];

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        {
          backgroundColor: colors.surface,
          borderColor: accent,
          padding: spacing.lg,
          opacity: pressed ? 0.85 : 1,
        },
      ]}
    >
      <View style={[styles.iconBadge, { backgroundColor: accent }]}>
        <Text style={styles.icon}>{info.icon}</Text>
      </View>
      <Text style={{ fontFamily: font.bold, fontSize: 18, color: colors.textPrimary }}>{info.label}</Text>
      <Text style={{ fontFamily: font.regular, fontSize: 13, color: colors.textSecondary }}>{status}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: { borderRadius: 20, borderWidth: 2, gap: 6, flexBasis: "47%", flexGrow: 1 },
  iconBadge: { width: 40, height: 40, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  icon: { fontSize: 20 },
});
