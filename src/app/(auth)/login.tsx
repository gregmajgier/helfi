import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";

import { Button } from "@/components";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/lib/theme";

export default function LoginScreen() {
  const { login } = useAuth();
  const router = useRouter();
  const { colors, font, spacing } = useTheme();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setError(null);
    try {
      await login(email, password);
      router.dismissAll();
      router.replace("/" as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : "login failed");
    }
  };

  return (
    <View
      style={{ flex: 1, justifyContent: "center", padding: spacing.xl, gap: spacing.md, backgroundColor: colors.background }}
    >
      <TextInput
        placeholder="Email"
        placeholderTextColor={colors.textSecondary}
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
          backgroundColor: colors.surface,
        }}
      />
      <TextInput
        placeholder="Password"
        placeholderTextColor={colors.textSecondary}
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
          backgroundColor: colors.surface,
        }}
      />
      {error ? <Text style={{ color: colors.danger, fontFamily: font.regular }}>{error}</Text> : null}
      <Button title="Log in" onPress={onSubmit} />
      <Button title="Need an account? Register" variant="text" onPress={() => router.push("/register" as Href)} />
    </View>
  );
}
