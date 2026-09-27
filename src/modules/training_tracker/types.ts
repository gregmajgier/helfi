export type WorkoutType = "strength" | "calisthenics" | "running" | "cycling";
export type WorkoutSource = "manual";

export type ExerciseSet = {
  reps: number;
  weight_kg?: number;
  bodyweight?: boolean;
};

export type WorkoutExercise = {
  exercise_id: string;
  sets: ExerciseSet[];
};

export type Workout = {
  id: string;
  user_id: string;
  type: WorkoutType;
  source: WorkoutSource;
  started_at: string;
  duration_s: number;
  exercises?: WorkoutExercise[];
  distance_m?: number;
  avg_pace_s_per_km?: number;
  elevation_gain_m?: number;
  created_at: string;
  updated_at: string;
};

export type WorkoutInput = {
  type: WorkoutType;
  started_at: string;
  duration_s: number;
  exercises?: WorkoutExercise[];
  distance_m?: number;
  avg_pace_s_per_km?: number;
  elevation_gain_m?: number;
};

export type WorkoutUpdateInput = {
  duration_s?: number;
  avg_pace_s_per_km?: number;
  elevation_gain_m?: number;
};

export type Exercise = {
  id: string;
  name: string;
  category: string;
  is_bodyweight: boolean;
  created_by_user_id?: string | null;
};

export type ExerciseInput = {
  name: string;
  category: string;
  is_bodyweight: boolean;
};
