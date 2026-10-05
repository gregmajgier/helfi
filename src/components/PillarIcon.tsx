import { Barbell, Brain, ForkKnife, Timer } from "phosphor-react-native";

import { useTheme, type PillarKey } from "@/lib/theme";

const ICONS = { move: Barbell, fuel: ForkKnife, mind: Brain, focus: Timer } as const;

export function PillarIcon({ pillar, size = 24 }: { pillar: PillarKey; size?: number }) {
  const { pillars, mode } = useTheme();
  const accent = pillars[pillar][mode];
  const Icon = ICONS[pillar];
  return <Icon size={size} weight="duotone" color={accent} duotoneColor={accent} duotoneOpacity={0.35} />;
}
