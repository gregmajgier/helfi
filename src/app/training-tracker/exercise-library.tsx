import { useRef, useState } from "react";
import { FlatList, Text, TextInput, View } from "react-native";

import { Button, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createExercise, searchExercises } from "@/modules/training_tracker/api";
import type { Exercise } from "@/modules/training_tracker/types";

export default function ExerciseLibraryScreen() {
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.move.light;
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Exercise[]>([]);
  const [newName, setNewName] = useState("");
  const [newCategory, setNewCategory] = useState("");
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

  const inputStyle = {
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    borderRadius: 12,
    fontFamily: font.regular,
    color: colors.textPrimary,
    backgroundColor: colors.surface,
  } as const;

  return (
    <ScreenContainer>
      {error ? <Text style={{ color: colors.danger, fontFamily: font.regular }}>{error}</Text> : null}

      <TextInput
        placeholder="Search exercises"
        placeholderTextColor={colors.textSecondary}
        value={query}
        onChangeText={onSearch}
        style={inputStyle}
      />
      <FlatList
        data={results}
        keyExtractor={(item) => item.id}
        style={{ flex: 1 }}
        renderItem={({ item }) => (
          <View style={{ paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border }}>
            <Text style={{ fontFamily: font.medium, color: colors.textPrimary, textTransform: "capitalize" }}>
              {item.name} · {item.category}
              {item.is_bodyweight ? " · bodyweight" : ""}
            </Text>
          </View>
        )}
      />

      <Text style={{ fontFamily: font.semibold, fontSize: 14, color: colors.textSecondary }}>
        Add a custom exercise
      </Text>
      <TextInput placeholder="Name" placeholderTextColor={colors.textSecondary} value={newName} onChangeText={setNewName} style={inputStyle} />
      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        <TextInput
          placeholder="Category (e.g. chest, back, legs)"
          placeholderTextColor={colors.textSecondary}
          value={newCategory}
          onChangeText={setNewCategory}
          style={[inputStyle, { flex: 1 }]}
        />
      </View>
      <Button title="Add Exercise" color={accent} onPress={addCustomExercise} />
    </ScreenContainer>
  );
}
