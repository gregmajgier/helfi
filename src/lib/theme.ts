import { useColorScheme } from "react-native";

export type PillarKey = "move" | "fuel" | "mind" | "focus";

export type Pillar = {
  key: PillarKey;
  label: string;
  icon: string;
  light: string;
  dark: string;
};

export const PILLARS: Record<PillarKey, Pillar> = {
  move: { key: "move", label: "Move", icon: "🏃", light: "#E8623D", dark: "#FF8162" },
  fuel: { key: "fuel", label: "Fuel", icon: "🍎", light: "#7C9A5C", dark: "#9CBB7A" },
  mind: { key: "mind", label: "Mind", icon: "🧘", light: "#8B7FD1", dark: "#A79BEB" },
  focus: { key: "focus", label: "Focus", icon: "⏳", light: "#3E9A96", dark: "#5CC2BD" },
};

export const PILLAR_ORDER: PillarKey[] = ["move", "fuel", "mind", "focus"];

type NeutralPalette = {
  background: string;
  surface: string;
  textPrimary: string;
  textSecondary: string;
  border: string;
};

export type ThemeMode = "light" | "dark";

export const NEUTRALS: Record<ThemeMode, NeutralPalette> = {
  light: {
    background: "#FBF9F6",
    surface: "#FFFFFF",
    textPrimary: "#22262B",
    textSecondary: "#6B7177",
    border: "#E6E2DC",
  },
  dark: {
    background: "#16181C",
    surface: "#1F2227",
    textPrimary: "#F4F2EE",
    textSecondary: "#9BA1A8",
    border: "#2B2F35",
  },
};

export const SPACING = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 } as const;

export const FONT_FAMILY = {
  regular: "PlusJakartaSans_400Regular",
  medium: "PlusJakartaSans_500Medium",
  semibold: "PlusJakartaSans_600SemiBold",
  bold: "PlusJakartaSans_700Bold",
  extrabold: "PlusJakartaSans_800ExtraBold",
} as const;

export function pillarColor(pillar: PillarKey, mode: ThemeMode): string {
  return PILLARS[pillar][mode];
}

export function useTheme() {
  const scheme = useColorScheme();
  const mode: ThemeMode = scheme === "dark" ? "dark" : "light";
  return {
    mode,
    colors: NEUTRALS[mode],
    pillars: PILLARS,
    pillarOrder: PILLAR_ORDER,
    spacing: SPACING,
    font: FONT_FAMILY,
  };
}
