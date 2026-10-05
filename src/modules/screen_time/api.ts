import { apiFetch } from "@/lib/api-client";

import type { DailyUsage } from "./types";

export type UsageRecord = DailyUsage & { updated_at: string };

export function putDailyUsage(usage: DailyUsage): Promise<UsageRecord> {
  return apiFetch<UsageRecord>(`/screentime/usage/${usage.date}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ total_minutes: usage.total_minutes, dumb_minutes: usage.dumb_minutes }),
  });
}

export function listDailyUsage(start: string, end: string): Promise<UsageRecord[]> {
  return apiFetch<UsageRecord[]>(`/screentime/usage?start=${start}&end=${end}`);
}
