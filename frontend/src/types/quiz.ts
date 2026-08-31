import type { Question } from "./question";

export type QuestionFormat = "TRADITIONAL" | "NGN";
export type QuestionModeStatus = "UNUSED" | "INCORRECT" | "MARKED" | "OMITTED" | "CORRECT";

export const QUESTION_MODE_STATUS_LABELS: Record<QuestionModeStatus, string> = {
  UNUSED: "Unused",
  INCORRECT: "Incorrect",
  MARKED: "Marked",
  OMITTED: "Omitted",
  CORRECT: "Correct",
};

/** The full filter selection driving both live counts (getFacetCounts) and quiz creation (createQuizSession). */
export interface QuizFilters {
  question_types: QuestionFormat[];
  question_mode: "STANDARD" | "CUSTOM";
  status_filters: QuestionModeStatus[];
  domains: number[];
  nursing_systems: number[];
  nclex_client_needs_subcategories: number[];
  is_tutor_mode: boolean;
  is_timed: boolean;
  time_limit_minutes: number | null;
  question_count: number;
}

export interface FacetCounts {
  question_types: Record<QuestionFormat, { unused: number; total: number }>;
  question_mode: Record<QuestionModeStatus, { count: number; ngn_count: number }>;
  domains: { id: number; name: string; count: number }[];
  nursing_systems: { id: number; name: string; count: number }[];
  nclex_client_needs_subcategories: { id: number; name: string; count: number }[];
}

/** The real, server-created quiz attempt — replaces the old client-only MockQuizSession. */
export interface QuizSession {
  id: string;
  current_question_index: number;
  is_complete: boolean;
  started_at: string;
  filter_config: QuizFilters;
  questions: Question[];
}

export interface QuestionResponse {
  question_id: string;
  selected_choice_ids: string[];
  is_correct: boolean;
}
