import { Stack } from "expo-router";

export default function MealTrackerLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Fuel" }} />
      <Stack.Screen name="add-entry" options={{ title: "Add Entry" }} />
      <Stack.Screen name="custom-food" options={{ title: "Custom Food" }} />
      <Stack.Screen name="barcode-scanner" options={{ title: "Scan Barcode" }} />
      <Stack.Screen name="camera" options={{ title: "Calorie Camera" }} />
      <Stack.Screen name="confirm-estimate" options={{ title: "Confirm Estimate" }} />
    </Stack>
  );
}
