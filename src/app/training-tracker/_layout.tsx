import { Stack } from "expo-router";

export default function TrainingTrackerLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Move" }} />
      <Stack.Screen name="log-strength" options={{ title: "Log Strength" }} />
      <Stack.Screen name="log-cardio" options={{ title: "Log Cardio" }} />
      <Stack.Screen name="exercise-library" options={{ title: "Exercise Library" }} />
    </Stack>
  );
}
