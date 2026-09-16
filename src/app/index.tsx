import { Redirect, type Href } from "expo-router";

import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  return <Redirect href={(user ? "/meal-tracker" : "/login") as Href} />;
}
