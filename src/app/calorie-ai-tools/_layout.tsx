import { Stack } from "expo-router";

export default function CalorieAiToolsLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Calorie AI Tools" }} />
      <Stack.Screen name="camera" options={{ title: "Calorie Camera" }} />
    </Stack>
  );
}
