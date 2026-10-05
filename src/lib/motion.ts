import { useEffect, useState } from "react";
import { AccessibilityInfo } from "react-native";
import { FadeInUp } from "react-native-reanimated";

import { MOTION } from "@/lib/theme";

export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduced).catch(() => {});
    const sub = AccessibilityInfo.addEventListener("reduceMotionChanged", setReduced);
    return () => sub.remove();
  }, []);
  return reduced;
}

export function useEnter(index = 0) {
  const reduced = useReducedMotion();
  if (reduced) return undefined;
  return FadeInUp.delay(index * MOTION.stagger)
    .duration(MOTION.enterDuration)
    .springify()
    .damping(MOTION.spring.damping);
}
