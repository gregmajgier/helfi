import * as ImagePicker from "expo-image-picker";
import { useRouter, type Href } from "expo-router";
import { useEffect } from "react";
import { SafeAreaView, Text } from "react-native";

export default function CameraScreen() {
  const router = useRouter();

  useEffect(() => {
    (async () => {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        router.back();
        return;
      }

      const result = await ImagePicker.launchCameraAsync({ quality: 0.7 });
      if (result.canceled) {
        router.back();
        return;
      }

      router.replace({
        pathname: "/meal-tracker/confirm-estimate",
        params: { photoUri: result.assets[0].uri },
      } as Href);
    })();
  }, [router]);

  return (
    <SafeAreaView style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <Text>Opening camera…</Text>
    </SafeAreaView>
  );
}
