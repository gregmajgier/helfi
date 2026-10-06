export type MoodEntry = {
  id: string;
  user_id: string;
  logged_at: string;
  mood_score: number;
  /** Fuller check-in fields, 1-5. Null on quick check-ins and on entries from older app versions. */
  energy?: number | null;
  stress?: number | null;
  sleep_quality?: number | null;
  emotions?: string[];
  tags: string[];
  note?: string | null;
  created_at: string;
  updated_at: string;
};

export type MoodEntryInput = {
  logged_at: string;
  mood_score: number;
  energy?: number;
  stress?: number;
  sleep_quality?: number;
  emotions?: string[];
  tags?: string[];
  note?: string;
};

export type JournalEntry = {
  id: string;
  user_id: string;
  written_at: string;
  prompt?: string;
  body: string;
  created_at: string;
  updated_at: string;
};

export type JournalEntryInput = {
  written_at: string;
  prompt?: string;
  body: string;
};
