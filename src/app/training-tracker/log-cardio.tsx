import { useRouter } from "expo-router";
import { useState } from "react";
import { Button, SafeAreaView, Text, TextInput, View } from "react-native";

import { createWorkout } from "@/modules/training_tracker/api";
import type { WorkoutType } from "@/modules/training_tracker/types";

const CARDIO_TYPES: WorkoutType[] = ["running", "cycling"];

export default function LogCardioScreen() {
  const router = useRouter();
  const [workoutType, setWorkoutType] = useState<WorkoutType>("running");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [distanceKm, setDistanceKm] = useState("");
  const [elevationM, setElevationM] = useState("");
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    const duration_s = Math.round(Number(durationMinutes) * 60);
    const distance_m = Number(distanceKm) * 1000;
    if (!Number.isFinite(duration_s) || duration_s <= 0 || !Number.isFinite(distance_m) || distance_m <= 0) {
      setError("enter a valid duration and distance");
      return;
    }
    try {
      await createWorkout({
        type: workoutType,
        started_at: new Date().toISOString(),
        duration_s,
        distance_m,
        avg_pace_s_per_km: Math.round(duration_s / (distance_m / 1000)),
        elevation_gain_m: elevationM ? Number(elevationM) : undefined,
      });
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to save workout");
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}

      <View style={{ flexDirection: "row", gap: 8 }}>
        {CARDIO_TYPES.map((t) => (
          <Button
            key={t}
            title={t}
            color={t === workoutType ? "#208AEF" : undefined}
            onPress={() => setWorkoutType(t)}
          />
        ))}
      </View>

      <TextInput
        placeholder="Duration (minutes)"
        keyboardType="numeric"
        value={durationMinutes}
        onChangeText={setDurationMinutes}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <TextInput
        placeholder="Distance (km)"
        keyboardType="numeric"
        value={distanceKm}
        onChangeText={setDistanceKm}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <TextInput
        placeholder="Elevation gain (m, optional)"
        keyboardType="numeric"
        value={elevationM}
        onChangeText={setElevationM}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />

      <Button title="Save Workout" onPress={save} />
    </SafeAreaView>
  );
}
