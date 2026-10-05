import { useColorScheme } from "react-native";

export type PillarKey = "move" | "fuel" | "mind" | "focus";

export type Pillar = {
  key: PillarKey;
  label: string;
  light: string;
  dark: string;
};

export const PILLARS: Record<PillarKey, Pillar> = {
  move: { key: "move", label: "Move", light: "#FF5A36", dark: "#FF7A5C" },
  fuel: { key: "fuel", label: "Fuel", light: "#22B866", dark: "#46D58A" },
  mind: { key: "mind", label: "Mind", light: "#7A5CFF", dark: "#9C85FF" },
  focus: { key: "focus", label: "Focus", light: "#1E9BFF", dark: "#52B4FF" },
};

export const PILLAR_ORDER: PillarKey[] = ["move", "fuel", "mind", "focus"];

type NeutralPalette = {
  background: string;
  surface: string;
  textPrimary: string;
  textSecondary: string;
  border: string;
  danger: string;
};

export type ThemeMode = "light" | "dark";

export const NEUTRALS: Record<ThemeMode, NeutralPalette> = {
  light: {
    background: "#F6F6FB",
    surface: "#FFFFFF",
    textPrimary: "#14151F",
    textSecondary: "#5A5E72",
    border: "#E2E3EE",
    danger: "#D6293E",
  },
  dark: {
    background: "#0E0F16",
    surface: "#181A24",
    textPrimary: "#F5F5FA",
    textSecondary: "#9A9EB2",
    border: "#262936",
    danger: "#FF6B7D",
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

export const RADIUS = { sm: 12, md: 18, lg: 24, pill: 999 } as const;

export const MOTION = {
  spring: { damping: 16, stiffness: 220 },
  pressScale: 0.96,
  stagger: 60,
  enterDuration: 420,
} as const;

export function tint(hex: string, alpha = 0.14): string {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
}

function luminance(hex: string): number {
  const n = parseInt(hex.slice(1), 16);
  const ch = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2];
}

export function contrastRatio(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

export function onAccent(accent: string): string {
  return contrastRatio(accent, "#FFFFFF") >= contrastRatio(accent, "#0B1220") ? "#FFFFFF" : "#0B1220";
}

export function cardShadow(mode: ThemeMode) {
  return {
    shadowColor: mode === "dark" ? "#000000" : "#14151F",
    shadowOpacity: mode === "dark" ? 0.4 : 0.08,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 6 },
    elevation: 3,
  };
}

export function accentShadow(color: string) {
  return {
    shadowColor: color,
    shadowOpacity: 0.35,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 8 },
    elevation: 4,
  };
}

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
    radius: RADIUS,
    font: FONT_FAMILY,
  };
}
