import { Redirect, type Href } from "expo-router";

export default function Home() {
  return <Redirect href={"/meal-tracker" as Href} />;
}