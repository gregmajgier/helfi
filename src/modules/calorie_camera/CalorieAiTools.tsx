import { useRouter, type Href } from "expo-router";
import { Button, View } from "react-native";

export default function CalorieAiTools() {
    const router = useRouter();

    return <View>
       <Button
         title="Take a Photo"
         onPress={() => router.push("/calorie-ai-tools/camera" as Href)}
       />
       <Button title="View History" onPress={() => {}} />
       <Button title="Settings" onPress={() => {}} />
    </View>;
}