export type MoodEntry = {
  id: string;
  user_id: string;
  logged_at: string;
  mood_score: number;
  tags: string[];
  note?: string;
  created_at: string;
  updated_at: string;
};

export type MoodEntryInput = {
  logged_at: string;
  mood_score: number;
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
