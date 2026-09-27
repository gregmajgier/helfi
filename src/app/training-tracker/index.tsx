import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Button, FlatList, SafeAreaView, Text, View } from "react-native";

import { deleteWorkout, listWorkouts } from "@/modules/training_tracker/api";
import type { Workout } from "@/modules/training_tracker/types";

function summarize(workout: Workout): string {
  if (workout.type === "strength" || workout.type === "calisthenics") {
    const setCount = workout.exercises?.reduce((sum, e) => sum + e.sets.length, 0) ?? 0;
    return `${workout.type}: ${workout.exercises?.length ?? 0} exercises, ${setCount} sets`;
  }
  const km = workout.distance_m ? (workout.distance_m / 1000).toFixed(1) : "?";
  return `${workout.type}: ${km} km`;
}

export default function TrainingTrackerRoute() {
  const router = useRouter();
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      setWorkouts(await listWorkouts());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load workouts");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      <Text style={{ fontSize: 20, fontWeight: "600" }}>Training History</Text>

      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}

      <FlatList
        data={workouts}
        keyExtractor={(item) => item.id}
        refreshing={isLoading}
        onRefresh={load}
        ListEmptyComponent={<Text>No workouts logged yet.</Text>}
        renderItem={({ item }) => (
          <View style={{ flexDirection: "row", justifyContent: "space-between", paddingVertical: 8 }}>
            <Text>{summarize(item)}</Text>
            <Button
              title="Delete"
              onPress={async () => {
                try {
                  await deleteWorkout(item.id);
                  setError(null);
                  load();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "failed to delete workout");
                }
              }}
            />
          </View>
        )}
      />

      <View style={{ flexDirection: "row", gap: 8 }}>
        <Button title="Log Strength" onPress={() => router.push("/training-tracker/log-strength" as Href)} />
        <Button title="Log Cardio" onPress={() => router.push("/training-tracker/log-cardio" as Href)} />
      </View>
      <Button
        title="Exercise Library"
        onPress={() => router.push("/training-tracker/exercise-library" as Href)}
      />
    </SafeAreaView>
  );
}
