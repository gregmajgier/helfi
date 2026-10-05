import { Text } from "react-native";
import Animated from "react-native-reanimated";

import { useEnter } from "@/lib/motion";
import { cardShadow, useTheme } from "@/lib/theme";

export function StatTile({ value, label, index = 0 }: { value: string; label: string; index?: number }) {
  const { colors, font, radius, mode } = useTheme();
  const entering = useEnter(index);
  return (
    <Animated.View
      entering={entering}
      style={[
        { flex: 1, backgroundColor: colors.surface, borderRadius: radius.md, paddingVertical: 12, paddingHorizontal: 8, alignItems: "center", gap: 2 },
        cardShadow(mode),
      ]}
    >
      <Text style={{ fontFamily: font.extrabold, fontSize: 18, color: colors.textPrimary }}>{value}</Text>
      <Text style={{ fontFamily: font.medium, fontSize: 11, color: colors.textSecondary, textAlign: "center" }}>{label}</Text>
    </Animated.View>
  );
}
