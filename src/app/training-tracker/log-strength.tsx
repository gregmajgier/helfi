import { useRouter } from "expo-router";
import { useRef, useState } from "react";
import { Button, FlatList, SafeAreaView, Text, TextInput, View } from "react-native";

import { createWorkout, searchExercises } from "@/modules/training_tracker/api";
import type { Exercise, ExerciseSet, WorkoutType } from "@/modules/training_tracker/types";

const STRENGTH_TYPES: WorkoutType[] = ["strength", "calisthenics"];

type DraftExercise = {
  exercise: Exercise;
  sets: ExerciseSet[];
};

export default function LogStrengthScreen() {
  const router = useRouter();
  const [workoutType, setWorkoutType] = useState<WorkoutType>("strength");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Exercise[]>([]);
  const [draftExercises, setDraftExercises] = useState<DraftExercise[]>([]);
  const [error, setError] = useState<string | null>(null);
  const searchSeq = useRef(0);

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
    setDraftExercises((prev) => [...prev, { exercise, sets: [{ reps: 10 }] }]);
    setQuery("");
    setResults([]);
  };

  const addSet = (index: number) => {
    setDraftExercises((prev) =>
      prev.map((d, i) => (i === index ? { ...d, sets: [...d.sets, { reps: 10 }] } : d))
    );
  };

  const updateSet = (exerciseIndex: number, setIndex: number, reps: number, weightKg?: number) => {
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
      await createWorkout({
        type: workoutType,
        started_at: new Date().toISOString(),
        duration_s,
        exercises: draftExercises.map((d) => ({ exercise_id: d.exercise.id, sets: d.sets })),
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
        {STRENGTH_TYPES.map((t) => (
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
        placeholder="Search exercises"
        value={query}
        onChangeText={onSearch}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <FlatList
        data={results}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <Button title={item.name} onPress={() => addExercise(item)} />}
      />

      <FlatList
        data={draftExercises}
        keyExtractor={(_, index) => String(index)}
        renderItem={({ item, index }) => (
          <View style={{ paddingVertical: 8 }}>
            <Text style={{ fontWeight: "600" }}>{item.exercise.name}</Text>
            {item.sets.map((set, setIndex) => (
              <View key={setIndex} style={{ flexDirection: "row", gap: 8, alignItems: "center" }}>
                <TextInput
                  placeholder="reps"
                  keyboardType="numeric"
                  value={String(set.reps)}
                  onChangeText={(text) => updateSet(index, setIndex, Number(text) || 0, set.weight_kg)}
                  style={{ borderWidth: 1, padding: 8, borderRadius: 8, width: 60 }}
                />
                <TextInput
                  placeholder="kg"
                  keyboardType="numeric"
                  value={set.weight_kg !== undefined ? String(set.weight_kg) : ""}
                  onChangeText={(text) => updateSet(index, setIndex, set.reps, text ? Number(text) : undefined)}
                  style={{ borderWidth: 1, padding: 8, borderRadius: 8, width: 60 }}
                />
              </View>
            ))}
            <Button title="Add Set" onPress={() => addSet(index)} />
          </View>
        )}
      />

      <Button title="Save Workout" onPress={save} />
    </SafeAreaView>
  );
}
