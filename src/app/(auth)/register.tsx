import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Button, Text, TextInput, View } from "react-native";

import { useAuth } from "@/lib/auth-context";

export default function RegisterScreen() {
  const { register } = useAuth();
  const router = useRouter();
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
      router.replace("/meal-tracker" as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : "registration failed");
    }
  };

  return (
    <View style={{ flex: 1, justifyContent: "center", padding: 24, gap: 12 }}>
      <TextInput
        placeholder="Email"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <TextInput
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}
      <Button title="Register" onPress={onSubmit} />
      <Button title="Already have an account? Log in" onPress={() => router.push("/login" as Href)} />
    </View>
  );
}
