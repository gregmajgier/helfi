import { apiFetch } from "@/lib/api-client";

import type {
  Exercise,
  ExerciseInput,
  Workout,
  WorkoutInput,
  WorkoutType,
  WorkoutUpdateInput,
} from "./types";

export function listWorkouts(type?: WorkoutType): Promise<Workout[]> {
  const query = type ? `?type=${encodeURIComponent(type)}` : "";
  return apiFetch<Workout[]>(`/workouts${query}`);
}

export function createWorkout(workout: WorkoutInput): Promise<Workout> {
  return apiFetch<Workout>("/workouts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(workout),
  });
}

export function updateWorkout(id: string, updates: WorkoutUpdateInput): Promise<Workout> {
  return apiFetch<Workout>(`/workouts/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
}

export function deleteWorkout(id: string): Promise<void> {
  return apiFetch<void>(`/workouts/${id}`, { method: "DELETE" });
}

export function searchExercises(query: string): Promise<Exercise[]> {
  return apiFetch<Exercise[]>(`/workouts/exercises?q=${encodeURIComponent(query)}`);
}

export function createExercise(exercise: ExerciseInput): Promise<Exercise> {
  return apiFetch<Exercise>("/workouts/exercises", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(exercise),
  });
}
