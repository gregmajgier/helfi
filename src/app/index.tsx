import { Redirect, useRouter, type Href } from "expo-router";
import { Button, SafeAreaView, Text } from "react-native";

import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const router = useRouter();
  const { user, isLoading, logout } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!user) {
    return <Redirect href={"/login" as Href} />;
  }

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      <Text style={{ fontSize: 20, fontWeight: "600" }}>Health App</Text>
      <Button title="Meal Tracker" onPress={() => router.push("/meal-tracker" as Href)} />
      <Button title="Training Tracker" onPress={() => router.push("/training-tracker" as Href)} />
      <Button title="Log Out" onPress={logout} />
    </SafeAreaView>
  );
}
