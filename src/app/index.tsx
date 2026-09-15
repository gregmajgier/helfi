import { Redirect, type Href } from "expo-router";

export default function Home() {
  return <Redirect href={"/calorie-ai-tools" as Href} />;
}