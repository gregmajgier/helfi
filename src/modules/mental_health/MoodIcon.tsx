import { Smiley, SmileyMeh, SmileyNervous, SmileySad, SmileySticker } from "phosphor-react-native";

import { MOOD_COLORS } from "./content";

const FACES = [SmileySad, SmileyNervous, SmileyMeh, Smiley, SmileySticker] as const;

/** One icon family for mood across the app. `score` is 1 (rough) to 5 (great); fractions round. */
export function MoodIcon({ score, size = 28, color }: { score: number; size?: number; color?: string }) {
  const index = Math.min(5, Math.max(1, Math.round(score))) - 1;
  const Face = FACES[index];
  const fill = color ?? MOOD_COLORS[index];
  return <Face size={size} weight="duotone" color={fill} duotoneColor={fill} duotoneOpacity={0.35} />;
}
