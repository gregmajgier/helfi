import CalorieAiTools from "@/modules/meal_tracker/CalorieAiTools";
import { SafeAreaView } from "react-native";

export default function MealTrackerRoute() {
  return (
    <SafeAreaView style={{ flex: 1 }}>
      <CalorieAiTools />
    </SafeAreaView>
  );
}
