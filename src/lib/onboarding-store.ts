import AsyncStorage from "@react-native-async-storage/async-storage";

export type FuelGoal = "lose" | "maintain" | "build" | "eat_healthier";

export type OnboardingAnswers = {
  moveGoalPerWeek?: number;
  fuelGoal?: FuelGoal;
  mindMoodScore?: number;
  focusCategories?: string[];
};

const PENDING_KEY = "helf.onboarding.pending_answers";
const COMPLETE_KEY = "helf.onboarding.complete";
const MOVE_GOAL_KEY = "helf.onboarding.move_goal_per_week";
const FUEL_GOAL_KEY = "helf.onboarding.fuel_goal";

export async function getPendingAnswers(): Promise<OnboardingAnswers> {
  const raw = await AsyncStorage.getItem(PENDING_KEY);
  return raw ? (JSON.parse(raw) as OnboardingAnswers) : {};
}

export async function setPendingAnswer<K extends keyof OnboardingAnswers>(
  key: K,
  value: OnboardingAnswers[K]
): Promise<void> {
  const current = await getPendingAnswers();
  await AsyncStorage.setItem(PENDING_KEY, JSON.stringify({ ...current, [key]: value }));
}

export async function clearPendingAnswers(): Promise<void> {
  await AsyncStorage.removeItem(PENDING_KEY);
}

export async function isOnboardingComplete(): Promise<boolean> {
  return (await AsyncStorage.getItem(COMPLETE_KEY)) === "true";
}

export async function setOnboardingComplete(): Promise<void> {
  await AsyncStorage.setItem(COMPLETE_KEY, "true");
}

export async function getMoveGoalPerWeek(): Promise<number | null> {
  const raw = await AsyncStorage.getItem(MOVE_GOAL_KEY);
  return raw ? Number(raw) : null;
}

export async function setMoveGoalPerWeek(value: number): Promise<void> {
  await AsyncStorage.setItem(MOVE_GOAL_KEY, String(value));
}

export async function getFuelGoal(): Promise<FuelGoal | null> {
  return (await AsyncStorage.getItem(FUEL_GOAL_KEY)) as FuelGoal | null;
}

export async function setFuelGoal(value: FuelGoal): Promise<void> {
  await AsyncStorage.setItem(FUEL_GOAL_KEY, value);
}
