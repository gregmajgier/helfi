import type { ReactNode } from "react";
import { Pressable, type AccessibilityRole, type AccessibilityState, type StyleProp, type ViewStyle } from "react-native";
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from "react-native-reanimated";

import { useReducedMotion } from "@/lib/motion";
import { MOTION } from "@/lib/theme";

const APressable = Animated.createAnimatedComponent(Pressable);

export function AnimatedPressable({
  children,
  onPress,
  onLongPress,
  disabled,
  style,
  accessibilityRole,
  accessibilityLabel,
  accessibilityHint,
  accessibilityState,
}: {
  children: ReactNode;
  onPress?: () => void;
  onLongPress?: () => void;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
  accessibilityRole?: AccessibilityRole;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  accessibilityState?: AccessibilityState;
}) {
  const reduced = useReducedMotion();
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);
  const animated = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  return (
    <APressable
      onPress={onPress}
      onLongPress={onLongPress}
      accessibilityRole={accessibilityRole}
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      accessibilityState={accessibilityState}
      disabled={disabled}
      onPressIn={() => {
        if (reduced) opacity.set(0.7);
        else scale.set(withSpring(MOTION.pressScale, MOTION.spring));
      }}
      onPressOut={() => {
        opacity.set(1);
        scale.set(withSpring(1, MOTION.spring));
      }}
      style={[style, animated, disabled ? { opacity: 0.5 } : null]}
    >
      {children}
    </APressable>
  );
}
