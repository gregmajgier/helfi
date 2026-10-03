import { Stack } from "expo-router";

export default function MentalHealthLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Mind" }} />
      <Stack.Screen name="journal" options={{ title: "Journal" }} />
      <Stack.Screen name="history" options={{ title: "History" }} />
    </Stack>
  );
}
