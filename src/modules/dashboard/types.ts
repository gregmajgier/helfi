import type { PillarKey } from "@/lib/theme";

export type ViewMode = "day" | "week";

export type PillarProgress = { pillar: PillarKey; percent: number; tracked: boolean };

export type DashboardSummary = {
  rings: PillarProgress[];
  stats: {
    caloriePercent: number | null;
    trainingHours: number;
    rating: number | null;
  };
  cards: Record<PillarKey, string>;
};
