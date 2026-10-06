export type MoodOption = { score: number; label: string; hint: string };

export const MOOD_OPTIONS: MoodOption[] = [
  { score: 1, label: "Rough", hint: "Hard going right now" },
  { score: 2, label: "Low", hint: "Down or flat" },
  { score: 3, label: "Okay", hint: "Neither good nor bad" },
  { score: 4, label: "Good", hint: "Mostly positive" },
  { score: 5, label: "Great", hint: "Feeling really good" },
];

/** Rough to great. Used by the heatmap and distribution so a colour always means the same mood. */
export const MOOD_COLORS = ["#FF6B6B", "#FFA94D", "#FFD43B", "#74C69D", "#22B866"];

export const MOOD_LABEL: Record<number, string> = Object.fromEntries(MOOD_OPTIONS.map((o) => [o.score, o.label]));

/** Feelings grouped so the picker stays scannable. Stored as the lowercase label. */
export const EMOTION_GROUPS: { title: string; emotions: string[] }[] = [
  { title: "Pleasant", emotions: ["happy", "calm", "grateful", "excited", "proud", "hopeful", "loved"] },
  { title: "Unpleasant", emotions: ["anxious", "sad", "angry", "lonely", "overwhelmed", "guilty", "irritable"] },
  { title: "Low energy", emotions: ["tired", "bored", "numb", "unmotivated"] },
];

export const FACTORS: string[] = [
  "work",
  "family",
  "friends",
  "relationship",
  "exercise",
  "good food",
  "poor sleep",
  "health",
  "money",
  "weather",
  "outdoors",
  "screen time",
  "alone time",
  "creative",
];

export type ScaleKey = "energy" | "stress" | "sleep_quality";

export type Scale = {
  key: ScaleKey;
  title: string;
  question: string;
  labels: [string, string, string, string, string];
};

export const SCALES: Scale[] = [
  { key: "energy", title: "Energy", question: "How is your energy?", labels: ["Drained", "Low", "Steady", "Good", "Energised"] },
  { key: "stress", title: "Stress", question: "How stressed do you feel?", labels: ["Calm", "Mild", "Some", "High", "Very high"] },
  { key: "sleep_quality", title: "Sleep", question: "How did you sleep last night?", labels: ["Awful", "Poor", "Okay", "Good", "Great"] },
];
