import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, FlatList, Text, View } from "react-native";

import { Button, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
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
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.move.light;
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
    <ScreenContainer>
      <Text style={{ fontFamily: font.extrabold, fontSize: 24, color: colors.textPrimary }}>Move</Text>

      {error ? <Text style={{ color: colors.danger, fontFamily: font.regular }}>{error}</Text> : null}

      <FlatList
        data={workouts}
        keyExtractor={(item) => item.id}
        refreshing={isLoading}
        onRefresh={load}
        style={{ flex: 1 }}
        ListEmptyComponent={
          <Text style={{ color: colors.textSecondary, fontFamily: font.regular }}>No workouts logged yet.</Text>
        }
        renderItem={({ item }) => (
          <View
            style={{
              flexDirection: "row",
              justifyContent: "space-between",
              alignItems: "center",
              paddingVertical: spacing.sm,
              borderBottomWidth: 1,
              borderBottomColor: colors.border,
            }}
          >
            <View>
              <Text style={{ fontFamily: font.semibold, color: colors.textPrimary, textTransform: "capitalize" }}>
                {summarize(item)}
              </Text>
              <Text style={{ fontFamily: font.regular, color: colors.textSecondary, fontSize: 13 }}>
                {new Date(item.started_at).toLocaleDateString()} · {Math.round(item.duration_s / 60)} min
              </Text>
            </View>
            <Button
              title="Delete"
              variant="text"
              color={colors.danger}
              onPress={() => {
                Alert.alert("Delete workout?", "This can't be undone.", [
                  { text: "Cancel", style: "cancel" },
                  {
                    text: "Delete",
                    style: "destructive",
                    onPress: async () => {
                      try {
                        await deleteWorkout(item.id);
                        setError(null);
                        load();
                      } catch (err) {
                        setError(err instanceof Error ? err.message : "failed to delete workout");
                      }
                    },
                  },
                ]);
              }}
            />
          </View>
        )}
      />

      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        <View style={{ flex: 1 }}>
          <Button title="Log Strength" color={accent} onPress={() => router.push("/training-tracker/log-strength" as Href)} />
        </View>
        <View style={{ flex: 1 }}>
          <Button title="Log Cardio" color={accent} onPress={() => router.push("/training-tracker/log-cardio" as Href)} />
        </View>
      </View>
      <Button
        title="Exercise Library"
        variant="secondary"
        color={accent}
        onPress={() => router.push("/training-tracker/exercise-library" as Href)}
      />
    </ScreenContainer>
  );
}
