import { Stack } from "expo-router";

export default function DigitalHealthLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Focus" }} />
      <Stack.Screen name="rule-builder" options={{ title: "New Rule" }} />
    </Stack>
  );
}
