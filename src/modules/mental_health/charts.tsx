import { useState } from "react";
import { Text, View } from "react-native";
import Svg, { Circle, Line, Path } from "react-native-svg";

import { tint, useTheme } from "@/lib/theme";

import { MOOD_COLORS } from "./content";
import { WEEKDAY_LABELS, type TrendPoint } from "./stats";

function parseKey(key: string): Date {
  const [y, m, d] = key.split("-").map(Number);
  return new Date(y, m - 1, d);
}

/** Splits a series into runs of consecutive present values so gaps stay gaps. */
function runs(points: { x: number; y: number | null }[]): { x: number; y: number }[][] {
  const out: { x: number; y: number }[][] = [];
  let cur: { x: number; y: number }[] = [];
  for (const p of points) {
    if (p.y === null) {
      if (cur.length) out.push(cur);
      cur = [];
    } else {
      cur.push({ x: p.x, y: p.y });
    }
  }
  if (cur.length) out.push(cur);
  return out;
}

/** Line chart on a fixed 1-5 axis, with dots and gaps where nothing was logged. */
export function TrendChart({
  points,
  color,
  height = 150,
  min = 1,
  max = 5,
}: {
  points: TrendPoint[];
  color: string;
  height?: number;
  min?: number;
  max?: number;
}) {
  const { colors, font } = useTheme();
  const [width, setWidth] = useState(0);
  const padX = 12;
  const padY = 12;
  const n = points.length;
  const x = (i: number) => padX + (n <= 1 ? 0 : (i * (width - padX * 2)) / (n - 1));
  const y = (v: number) => padY + ((max - v) / (max - min)) * (height - padY * 2);
  const series = points.map((p, i) => ({ x: x(i), y: p.value === null ? null : y(p.value) }));
  const segments = runs(series);
  const first = parseKey(points[0]?.date ?? "2000-01-01");
  const label = (d: Date) => `${d.getDate()}/${d.getMonth() + 1}`;

  return (
    <View onLayout={(e) => setWidth(e.nativeEvent.layout.width)}>
      {width > 0 ? (
        <Svg width={width} height={height}>
          {[1, 3, 5].map((v) => (
            <Line key={v} x1={padX} x2={width - padX} y1={y(v)} y2={y(v)} stroke={colors.border} strokeWidth={1} strokeDasharray="4 4" />
          ))}
          {segments.map((seg, i) =>
            seg.length > 1 ? (
              <Path
                key={i}
                d={seg.map((p, j) => `${j === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ")}
                stroke={color}
                strokeWidth={3}
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
              />
            ) : null
          )}
          {segments.flat().map((p, i) => (
            <Circle key={i} cx={p.x} cy={p.y} r={4} fill={color} stroke={colors.surface} strokeWidth={2} />
          ))}
        </Svg>
      ) : (
        <View style={{ height }} />
      )}
      <View style={{ flexDirection: "row", justifyContent: "space-between", paddingHorizontal: padX }}>
        <Text style={{ fontFamily: font.medium, fontSize: 11, color: colors.textSecondary }}>{label(first)}</Text>
        <Text style={{ fontFamily: font.medium, fontSize: 11, color: colors.textSecondary }}>Today</Text>
      </View>
    </View>
  );
}

/** Small line for a secondary metric. */
export function Sparkline({ points, color, height = 36, min = 1, max = 5 }: { points: TrendPoint[]; color: string; height?: number; min?: number; max?: number }) {
  const [width, setWidth] = useState(0);
  const pad = 4;
  const n = points.length;
  const x = (i: number) => pad + (n <= 1 ? 0 : (i * (width - pad * 2)) / (n - 1));
  const y = (v: number) => pad + ((max - v) / (max - min)) * (height - pad * 2);
  const segments = runs(points.map((p, i) => ({ x: x(i), y: p.value === null ? null : y(p.value) })));
  return (
    <View style={{ flex: 1, height }} onLayout={(e) => setWidth(e.nativeEvent.layout.width)}>
      {width > 0 ? (
        <Svg width={width} height={height}>
          {segments.map((seg, i) =>
            seg.length > 1 ? (
              <Path key={i} d={seg.map((p, j) => `${j === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ")} stroke={color} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" fill="none" />
            ) : (
              <Circle key={i} cx={seg[0].x} cy={seg[0].y} r={3} fill={color} />
            )
          )}
        </Svg>
      ) : null}
    </View>
  );
}

export function moodColor(value: number): string {
  return MOOD_COLORS[Math.min(5, Math.max(1, Math.round(value))) - 1];
}

/** Calendar heatmap: one cell per day, Monday-first columns, empty cells padding the first week. */
export function Heatmap({ points }: { points: TrendPoint[] }) {
  const { colors, font, radius } = useTheme();
  const firstWeekday = points.length ? (parseKey(points[0].date).getDay() + 6) % 7 : 0;
  const cells: (TrendPoint | null)[] = [...Array<null>(firstWeekday).fill(null), ...points];
  while (cells.length % 7 !== 0) cells.push(null);
  const rows = Array.from({ length: cells.length / 7 }, (_, r) => cells.slice(r * 7, r * 7 + 7));
  const todayKey = points[points.length - 1]?.date;

  return (
    <View style={{ gap: 6 }}>
      <View style={{ flexDirection: "row", gap: 6 }}>
        {WEEKDAY_LABELS.map((d) => (
          <Text key={d} style={{ flex: 1, textAlign: "center", fontFamily: font.medium, fontSize: 10, color: colors.textSecondary }}>
            {d.slice(0, 2)}
          </Text>
        ))}
      </View>
      {rows.map((row, r) => (
        <View key={r} style={{ flexDirection: "row", gap: 6 }}>
          {row.map((cell, c) => (
            <View
              key={c}
              accessibilityLabel={cell ? `${cell.date}: ${cell.value === null ? "no check-in" : `mood ${cell.value.toFixed(1)}`}` : undefined}
              style={{
                flex: 1,
                aspectRatio: 1,
                borderRadius: radius.sm / 2,
                backgroundColor: cell === null ? "transparent" : cell.value === null ? tint(colors.textSecondary, 0.12) : moodColor(cell.value),
                borderWidth: cell && cell.date === todayKey ? 2 : 0,
                borderColor: colors.textPrimary,
              }}
            />
          ))}
        </View>
      ))}
    </View>
  );
}

/** Seven vertical bars, one per weekday, on a 1-5 scale. */
export function WeekdayBars({ points, color, height = 110 }: { points: TrendPoint[]; color: string; height?: number }) {
  const { colors, font, radius } = useTheme();
  const best = points.reduce<number | null>((b, p) => (p.value !== null && (b === null || p.value > b) ? p.value : b), null);
  return (
    <View style={{ flexDirection: "row", gap: 8, alignItems: "flex-end", height: height + 34 }}>
      {points.map((p) => {
        const h = p.value === null ? 6 : Math.max(8, (p.value / 5) * height);
        const isBest = p.value !== null && p.value === best;
        return (
          <View key={p.date} style={{ flex: 1, alignItems: "center", gap: 4 }}>
            <Text style={{ fontFamily: font.semibold, fontSize: 11, color: colors.textSecondary }}>
              {p.value === null ? "-" : p.value.toFixed(1)}
            </Text>
            <View
              style={{
                width: "100%",
                height: h,
                borderRadius: radius.sm / 2,
                backgroundColor: p.value === null ? tint(colors.textSecondary, 0.14) : isBest ? color : tint(color, 0.45),
              }}
            />
            <Text style={{ fontFamily: font.medium, fontSize: 11, color: colors.textSecondary }}>{p.date}</Text>
          </View>
        );
      })}
    </View>
  );
}

/** One segmented bar showing how check-ins split across moods 1 to 5, rough on the left. */
export function StackedBar({ counts, height = 14 }: { counts: number[]; height?: number }) {
  const { colors } = useTheme();
  const total = counts.reduce((a, b) => a + b, 0);
  if (total === 0) return <View style={{ height, borderRadius: height / 2, backgroundColor: tint(colors.textSecondary, 0.14) }} />;
  return (
    <View style={{ flexDirection: "row", height, borderRadius: height / 2, overflow: "hidden", gap: 2 }}>
      {counts.map((c, i) => (c > 0 ? <View key={i} style={{ flex: c, backgroundColor: MOOD_COLORS[i] }} /> : null))}
    </View>
  );
}

/** Ranked row: label, a bar scaled to `fraction` (0 to 1) with no background track, and the count. */
export function RankRow({ label, count, fraction, color }: { label: string; count: number; fraction: number; color: string }) {
  const { colors, font } = useTheme();
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
      <Text style={{ width: 96, fontFamily: font.medium, fontSize: 14, color: colors.textPrimary }} numberOfLines={1}>
        {label}
      </Text>
      <View style={{ flex: 1 }}>
        <View style={{ width: `${Math.round(Math.max(0.06, Math.min(1, fraction)) * 100)}%`, height: 8, borderRadius: 4, backgroundColor: color }} />
      </View>
      <Text style={{ fontFamily: font.bold, fontSize: 13, color: colors.textSecondary }}>{count}</Text>
    </View>
  );
}
