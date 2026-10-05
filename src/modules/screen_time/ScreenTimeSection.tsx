import { useCallback, useEffect, useState } from "react";
import { AppState, Text, View } from "react-native";

import { AnimatedPressable, Button, Card } from "@/components";
import { formatMinutes } from "@/modules/dashboard/summary";
import { useTheme } from "@/lib/theme";

import { ExcludedAppsPicker } from "./ExcludedAppsPicker";
import {
  BUDGET_STEP_MINUTES,
  MAX_FOCUS_BUDGET_MINUTES,
  MIN_FOCUS_BUDGET_MINUTES,
  defaultExcludedApps,
  getExcludedApps,
  getFocusBudget,
  setExcludedApps,
  setFocusBudget,
} from "./settings";
import { syncScreenTime } from "./sync";
import type { InstalledApp, PermissionState } from "./types";
import { provider } from "./usage";

const PERMISSION_COPY: Record<PermissionState, string> = {
  granted: "Usage access is on.",
  denied: "Usage access is off. Turn it on to track your screen time.",
  unavailable: "Not available here.",
};

export function ScreenTimeSection() {
  const { colors, font, spacing, pillars, mode } = useTheme();
  const accent = pillars.focus[mode];
  const [permission, setPermission] = useState<PermissionState | null>(null);
  const [budget, setBudget] = useState<number | null>(null);
  const [excluded, setExcluded] = useState<string[] | null>(null);
  const [apps, setApps] = useState<InstalledApp[]>([]);
  const [pickerOpen, setPickerOpen] = useState(false);

  const refreshPermission = useCallback(async () => {
    const state = await provider.getPermissionState().catch(() => "unavailable" as const);
    setPermission(state);
    // Granting happens in system settings, so catch up as soon as the user comes back.
    if (state === "granted") void syncScreenTime({ force: true });
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time load of persisted settings
    refreshPermission();
    getFocusBudget().then(setBudget);
    getExcludedApps().then(setExcluded);
    const sub = AppState.addEventListener("change", (s) => {
      if (s === "active") refreshPermission();
    });
    return () => sub.remove();
  }, [refreshPermission]);

  const changeBudget = async (delta: number) => {
    const next = await setFocusBudget((budget ?? 0) + delta);
    setBudget(next);
  };

  const openPicker = async () => {
    const installed = await provider.listInstalledApps().catch(() => []);
    setApps(installed.slice().sort((a, b) => a.label.localeCompare(b.label)));
    if (excluded === null) setExcluded(defaultExcludedApps(installed));
    setPickerOpen(true);
  };

  const saveExcluded = async (ids: string[]) => {
    await setExcludedApps(ids);
    setExcluded(ids);
    setPickerOpen(false);
    void syncScreenTime({ force: true });
  };

  const body = { fontFamily: font.regular, fontSize: 13, color: colors.textSecondary } as const;
  const heading = { fontFamily: font.semibold, fontSize: 14, color: colors.textPrimary } as const;

  return (
    <Card accent={accent} style={{ gap: spacing.md }}>
      <Text style={{ fontFamily: font.extrabold, fontSize: 18, color: colors.textPrimary }}>Screen-time tracking</Text>
      <Text style={body}>
        helf adds up how long you spend in apps each day and shows it on your Focus ring. Only the daily minute totals
        are uploaded. App names and per-app times never leave your phone.
      </Text>

      <View style={{ gap: spacing.sm }}>
        <Text style={heading}>Permission</Text>
        <Text style={body}>{permission === null ? "Checking..." : PERMISSION_COPY[permission]}</Text>
        {permission === "denied" ? (
          <Button
            title="Allow usage access"
            color={accent}
            onPress={async () => {
              await provider.requestPermission();
            }}
          />
        ) : null}
      </View>

      {permission === "granted" ? (
        <>
          <View style={{ gap: spacing.sm }}>
            <Text style={heading}>Daily budget for non-productive apps</Text>
            <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.lg }}>
              <AnimatedPressable
                disabled={budget === null || budget <= MIN_FOCUS_BUDGET_MINUTES}
                onPress={() => changeBudget(-BUDGET_STEP_MINUTES)}
              >
                <Text style={{ fontSize: 32, color: accent }}>−</Text>
              </AnimatedPressable>
              <Text style={{ fontFamily: font.extrabold, fontSize: 28, color: colors.textPrimary, minWidth: 96, textAlign: "center" }}>
                {budget === null ? "-" : formatMinutes(budget)}
              </Text>
              <AnimatedPressable
                disabled={budget === null || budget >= MAX_FOCUS_BUDGET_MINUTES}
                onPress={() => changeBudget(BUDGET_STEP_MINUTES)}
              >
                <Text style={{ fontSize: 32, color: accent }}>+</Text>
              </AnimatedPressable>
            </View>
          </View>

          {provider.pickerMode === "list" ? (
            <View style={{ gap: spacing.sm }}>
              <Text style={heading}>Productive apps</Text>
              <Text style={body}>Apps you choose here do not count against your budget.</Text>
              <Button
                title={excluded === null ? "Choose productive apps" : `Productive apps (${excluded.length})`}
                variant="secondary"
                color={accent}
                onPress={openPicker}
              />
            </View>
          ) : null}
        </>
      ) : null}

      <Text style={body}>{provider.accuracyNote}</Text>

      <ExcludedAppsPicker
        // Remount per open so the selection starts from what is saved.
        key={pickerOpen ? "open" : "closed"}
        visible={pickerOpen}
        apps={apps}
        initiallyExcluded={excluded ?? []}
        onDone={saveExcluded}
        onCancel={() => setPickerOpen(false)}
      />
    </Card>
  );
}
