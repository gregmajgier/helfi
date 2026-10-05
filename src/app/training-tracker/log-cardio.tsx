import { useRouter } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";

import { Button, Chip, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createWorkout } from "@/modules/training_tracker/api";
import type { WorkoutType } from "@/modules/training_tracker/types";

const CARDIO_TYPES: WorkoutType[] = ["running", "cycling"];

export default function LogCardioScreen() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.move.light;
  const [workoutType, setWorkoutType] = useState<WorkoutType>("running");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [distanceKm, setDistanceKm] = useState("");
  const [elevationM, setElevationM] = useState("");
  const [error, setError] = useState<string | null>(null);

  const inputStyle = {
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    borderRadius: 12,
    fontFamily: font.regular,
    color: colors.textPrimary,
    backgroundColor: colors.surface,
  } as const;

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
    <ScreenContainer>
      {error ? <Text style={{ color: colors.danger, fontFamily: font.regular }}>{error}</Text> : null}

      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        {CARDIO_TYPES.map((t) => (
          <Chip key={t} label={t} selected={t === workoutType} onPress={() => setWorkoutType(t)} color={accent} />
        ))}
      </View>

      <TextInput
        placeholder="Duration (minutes)"
        placeholderTextColor={colors.textSecondary}
        keyboardType="numeric"
        value={durationMinutes}
        onChangeText={setDurationMinutes}
        style={inputStyle}
      />
      <TextInput
        placeholder="Distance (km)"
        placeholderTextColor={colors.textSecondary}
        keyboardType="numeric"
        value={distanceKm}
        onChangeText={setDistanceKm}
        style={inputStyle}
      />
      <TextInput
        placeholder="Elevation gain (m, optional)"
        placeholderTextColor={colors.textSecondary}
        keyboardType="numeric"
        value={elevationM}
        onChangeText={setElevationM}
        style={inputStyle}
      />

      <Button title="Save Workout" color={accent} onPress={save} />
    </ScreenContainer>
  );
}
