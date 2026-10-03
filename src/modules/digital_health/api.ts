import { apiFetch } from "@/lib/api-client";

import type { ScreenTimeRule, ScreenTimeRuleInput, ScreenTimeRuleUpdateInput } from "./types";

export function listScreenTimeRules(): Promise<ScreenTimeRule[]> {
  return apiFetch<ScreenTimeRule[]>("/screentime/rules");
}

export function createScreenTimeRule(rule: ScreenTimeRuleInput): Promise<ScreenTimeRule> {
  return apiFetch<ScreenTimeRule>("/screentime/rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rule),
  });
}

export function updateScreenTimeRule(
  id: string,
  updates: ScreenTimeRuleUpdateInput
): Promise<ScreenTimeRule> {
  return apiFetch<ScreenTimeRule>(`/screentime/rules/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
}

export function deleteScreenTimeRule(id: string): Promise<void> {
  return apiFetch<void>(`/screentime/rules/${id}`, { method: "DELETE" });
}
