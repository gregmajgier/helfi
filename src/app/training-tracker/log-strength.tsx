import { useRouter } from "expo-router";
import { useRef, useState } from "react";
import { FlatList, Text, TextInput, View } from "react-native";

import { Button, Card, Chip, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createWorkout, searchExercises } from "@/modules/training_tracker/api";
import type { Exercise, WorkoutExercise, WorkoutType } from "@/modules/training_tracker/types";

const STRENGTH_TYPES: WorkoutType[] = ["strength", "calisthenics"];

type DraftSet = {
  reps: string;
  weight_kg: string;
};

type DraftExercise = {
  exercise: Exercise;
  sets: DraftSet[];
};

export default function LogStrengthScreen() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.move.light;
  const [workoutType, setWorkoutType] = useState<WorkoutType>("strength");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Exercise[]>([]);
  const [draftExercises, setDraftExercises] = useState<DraftExercise[]>([]);
  const [error, setError] = useState<string | null>(null);
  const searchSeq = useRef(0);

  const inputStyle = {
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    borderRadius: 12,
    fontFamily: font.regular,
    color: colors.textPrimary,
    backgroundColor: colors.surface,
  } as const;

  const onSearch = async (text: string) => {
    setQuery(text);
    const seq = ++searchSeq.current;
    try {
      const found = text.length >= 2 ? await searchExercises(text) : [];
      if (seq === searchSeq.current) {
        setResults(found);
        setError(null);
      }
    } catch (err) {
      if (seq === searchSeq.current) {
        setError(err instanceof Error ? err.message : "search failed");
      }
    }
  };

  const addExercise = (exercise: Exercise) => {
    setDraftExercises((prev) => [...prev, { exercise, sets: [{ reps: "10", weight_kg: "" }] }]);
    setQuery("");
    setResults([]);
  };

  const addSet = (index: number) => {
    setDraftExercises((prev) =>
      prev.map((d, i) => (i === index ? { ...d, sets: [...d.sets, { reps: "10", weight_kg: "" }] } : d))
    );
  };

  const updateSet = (exerciseIndex: number, setIndex: number, reps: string, weightKg: string) => {
    setDraftExercises((prev) =>
      prev.map((d, i) =>
        i === exerciseIndex
          ? { ...d, sets: d.sets.map((s, si) => (si === setIndex ? { reps, weight_kg: weightKg } : s)) }
          : d
      )
    );
  };

  const save = async () => {
    const duration_s = Math.round(Number(durationMinutes) * 60);
    if (!Number.isFinite(duration_s) || duration_s <= 0 || draftExercises.length === 0) {
      setError("enter a duration and at least one exercise");
      return;
    }
    try {
      const exercises: WorkoutExercise[] = draftExercises.map((d) => ({
        exercise_id: d.exercise.id,
        sets: d.sets.map((s) => ({
          reps: Number(s.reps) || 0,
          weight_kg: s.weight_kg ? Number(s.weight_kg) : undefined,
        })),
      }));
      await createWorkout({
        type: workoutType,
        started_at: new Date().toISOString(),
        duration_s,
        exercises,
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
        {STRENGTH_TYPES.map((t) => (
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
        placeholder="Search exercises"
        placeholderTextColor={colors.textSecondary}
        value={query}
        onChangeText={onSearch}
        style={inputStyle}
      />
      {results.length > 0 ? (
        <FlatList
          data={results}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ gap: spacing.xs }}
          renderItem={({ item }) => (
            <Button title={item.name} variant="text" color={accent} onPress={() => addExercise(item)} />
          )}
        />
      ) : null}

      <FlatList
        data={draftExercises}
        keyExtractor={(_, index) => String(index)}
        style={{ flex: 1 }}
        contentContainerStyle={{ gap: spacing.sm }}
        renderItem={({ item, index }) => (
          <Card>
            <Text style={{ fontFamily: font.semibold, color: colors.textPrimary }}>{item.exercise.name}</Text>
            {item.sets.map((set, setIndex) => (
              <View key={setIndex} style={{ flexDirection: "row", gap: spacing.sm, alignItems: "center" }}>
                <TextInput
                  placeholder="reps"
                  placeholderTextColor={colors.textSecondary}
                  keyboardType="numeric"
                  value={set.reps}
                  onChangeText={(text) => updateSet(index, setIndex, text, set.weight_kg)}
                  style={[inputStyle, { width: 70, padding: spacing.sm }]}
                />
                <TextInput
                  placeholder="kg"
                  placeholderTextColor={colors.textSecondary}
                  keyboardType="numeric"
                  value={set.weight_kg}
                  onChangeText={(text) => updateSet(index, setIndex, set.reps, text)}
                  style={[inputStyle, { width: 70, padding: spacing.sm }]}
                />
              </View>
            ))}
            <Button title="Add Set" variant="text" color={accent} onPress={() => addSet(index)} />
          </Card>
        )}
      />

      <Button title="Save Workout" color={accent} onPress={save} />
    </ScreenContainer>
  );
}
