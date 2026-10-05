import { useEffect } from "react";
import { View } from "react-native";
import Animated, { useAnimatedProps, useSharedValue, withTiming } from "react-native-reanimated";
import Svg, { Circle } from "react-native-svg";

import { useReducedMotion } from "@/lib/motion";
import { tint, useTheme } from "@/lib/theme";
import type { PillarProgress } from "@/modules/dashboard/types";

const ACircle = Animated.createAnimatedComponent(Circle);
const STROKE = 14;
const GAP = 6;

function Ring({ radius, size, color, percent, animate }: { radius: number; size: number; color: string; percent: number; animate: boolean }) {
  const circumference = 2 * Math.PI * radius;
  const progress = useSharedValue(animate ? 0 : percent);
  useEffect(() => {
    progress.value = animate ? withTiming(percent, { duration: 900 }) : percent;
  }, [percent, animate, progress]);
  const props = useAnimatedProps(() => ({ strokeDashoffset: circumference * (1 - progress.value) }));
  const c = size / 2;
  return (
    <>
      <Circle cx={c} cy={c} r={radius} stroke={tint(color, 0.2)} strokeWidth={STROKE} fill="none" />
      <ACircle
        cx={c}
        cy={c}
        r={radius}
        stroke={color}
        strokeWidth={STROKE}
        strokeLinecap="round"
        fill="none"
        strokeDasharray={`${circumference} ${circumference}`}
        animatedProps={props}
        rotation={-90}
        origin={`${c}, ${c}`}
      />
    </>
  );
}

export function RingCluster({ rings, size = 220, children }: { rings: PillarProgress[]; size?: number; children?: React.ReactNode }) {
  const { pillars, mode } = useTheme();
  const reduced = useReducedMotion();
  return (
    <View style={{ width: size, height: size, alignSelf: "center", alignItems: "center", justifyContent: "center" }}>
      <Svg width={size} height={size} style={{ position: "absolute" }}>
        {rings.map((r, i) => (
          <Ring
            key={r.pillar}
            radius={size / 2 - STROKE / 2 - i * (STROKE + GAP)}
            size={size}
            color={pillars[r.pillar][mode]}
            percent={r.tracked ? r.percent : 0}
            animate={!reduced}
          />
        ))}
      </Svg>
      {children}
    </View>
  );
}
