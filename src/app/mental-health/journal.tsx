import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Text, TextInput } from "react-native";

import { Button, ScreenContainer } from "@/components";
import { useTheme } from "@/lib/theme";
import { createJournalEntry, getTodaysPrompt } from "@/modules/mental_health/api";

export default function JournalRoute() {
  const router = useRouter();
  const { colors, pillars, font, spacing } = useTheme();
  const accent = pillars.mind.light;
  const [prompt, setPrompt] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getTodaysPrompt()
      .then((res) => setPrompt(res.prompt))
      .catch(() => setPrompt(null));
  }, []);

  const save = async () => {
    setError(null);
    if (!body.trim()) {
      setError("Write something first.");
      return;
    }
    setSaving(true);
    try {
      await createJournalEntry({ written_at: new Date().toISOString(), prompt: prompt ?? undefined, body });
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to save entry");
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScreenContainer>
      <Text style={{ fontFamily: font.bold, fontSize: 20, color: colors.textPrimary }}>Journal</Text>
      {prompt ? (
        <Text style={{ fontFamily: font.regular, fontSize: 14, color: colors.textSecondary }}>{prompt}</Text>
      ) : null}
      <TextInput
        placeholder="What's on your mind?"
        value={body}
        onChangeText={setBody}
        multiline
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 12,
          padding: spacing.md,
          minHeight: 160,
          fontFamily: font.regular,
          color: colors.textPrimary,
          textAlignVertical: "top",
        }}
      />
      {error ? <Text style={{ color: "#C0392B" }}>{error}</Text> : null}
      <Button title="Save entry" color={accent} onPress={save} disabled={saving} />
    </ScreenContainer>
  );
}
