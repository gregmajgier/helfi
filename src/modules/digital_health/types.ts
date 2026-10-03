export type ScreenTimeRule = {
  id: string;
  user_id: string;
  name: string;
  apps_or_categories: string[];
  daily_limit_minutes?: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type ScreenTimeRuleInput = {
  name: string;
  apps_or_categories: string[];
  daily_limit_minutes?: number;
  enabled?: boolean;
};

export type ScreenTimeRuleUpdateInput = {
  name?: string;
  apps_or_categories?: string[];
  daily_limit_minutes?: number;
  enabled?: boolean;
};
