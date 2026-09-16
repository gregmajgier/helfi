import { Stack } from "expo-router";

export default function MealTrackerLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Meal Tracker" }} />
      <Stack.Screen name="camera" options={{ title: "Calorie Camera" }} />
    </Stack>
  );
}
