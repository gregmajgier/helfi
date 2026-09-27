import { useState } from "react";
import { Button, FlatList, SafeAreaView, Text, TextInput } from "react-native";

import { createExercise, searchExercises } from "@/modules/training_tracker/api";
import type { Exercise } from "@/modules/training_tracker/types";

export default function ExerciseLibraryScreen() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Exercise[]>([]);
  const [newName, setNewName] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onSearch = async (text: string) => {
    setQuery(text);
    try {
      setResults(text.length >= 2 ? await searchExercises(text) : []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "search failed");
    }
  };

  const addCustomExercise = async () => {
    if (!newName.trim() || !newCategory.trim()) return;
    try {
      await createExercise({ name: newName.trim(), category: newCategory.trim(), is_bodyweight: false });
      setNewName("");
      setNewCategory("");
      await onSearch(query);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to add exercise");
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}

      <TextInput
        placeholder="Search exercises"
        value={query}
        onChangeText={onSearch}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <FlatList
        data={results}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Text style={{ paddingVertical: 8 }}>
            {item.name} · {item.category}
            {item.is_bodyweight ? " · bodyweight" : ""}
          </Text>
        )}
      />

      <Text style={{ fontWeight: "600" }}>Add a custom exercise</Text>
      <TextInput
        placeholder="Name"
        value={newName}
        onChangeText={setNewName}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <TextInput
        placeholder="Category (e.g. chest, back, legs)"
        value={newCategory}
        onChangeText={setNewCategory}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <Button title="Add Exercise" onPress={addCustomExercise} />
    </SafeAreaView>
  );
}
