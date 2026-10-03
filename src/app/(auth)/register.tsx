import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";

import { Button } from "@/components";
import { useAuth } from "@/lib/auth-context";
import {
  clearPendingAnswers,
  getPendingAnswers,
  setFuelGoal,
  setMoveGoalPerWeek,
  setOnboardingComplete,
} from "@/lib/onboarding-store";
import { useTheme } from "@/lib/theme";
import { createScreenTimeRule } from "@/modules/digital_health/api";
import { createMoodEntry } from "@/modules/mental_health/api";

async function flushOnboardingAnswers() {
  const answers = await getPendingAnswers();

  if (answers.mindMoodScore) {
    try {
      await createMoodEntry({
        logged_at: new Date().toISOString(),
        mood_score: answers.mindMoodScore,
        tags: [],
      });
    } catch {
      // best-effort — a seed mood entry is a nice-to-have, never worth blocking the hub over
    }
  }

  if (answers.focusCategories && answers.focusCategories.length > 0) {
    try {
      await createScreenTimeRule({
        name: "My first rule",
        apps_or_categories: answers.focusCategories,
        enabled: false,
      });
    } catch {
      // best-effort, same reasoning as above
    }
  }

  if (answers.moveGoalPerWeek) {
    await setMoveGoalPerWeek(answers.moveGoalPerWeek);
  }
  if (answers.fuelGoal) {
    await setFuelGoal(answers.fuelGoal);
  }

  await clearPendingAnswers();
  await setOnboardingComplete();
}

export default function RegisterScreen() {
  const { register } = useAuth();
  const router = useRouter();
  const { colors, font, spacing } = useTheme();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    try {
      await register(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "registration failed");
      return;
    }

    try {
      await flushOnboardingAnswers();
    } catch {
      // best-effort — registration already succeeded; never block reaching the hub over this
    }
    router.dismissAll();
    router.replace("/" as Href);
  };

  return (
    <View
      style={{ flex: 1, justifyContent: "center", padding: spacing.xl, gap: spacing.md, backgroundColor: colors.background }}
    >
      <TextInput
        placeholder="Email"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          padding: spacing.md,
          borderRadius: 12,
          fontFamily: font.regular,
          color: colors.textPrimary,
        }}
      />
      <TextInput
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          padding: spacing.md,
          borderRadius: 12,
          fontFamily: font.regular,
          color: colors.textPrimary,
        }}
      />
      {error ? <Text style={{ color: "#C0392B" }}>{error}</Text> : null}
      <Button title="Register" onPress={onSubmit} />
      <Button title="Already have an account? Log in" variant="text" onPress={() => router.push("/login" as Href)} />
    </View>
  );
}
