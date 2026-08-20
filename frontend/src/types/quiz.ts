import type { Difficulty, Question, QuestionType } from "./question";

/** Mirrors QuizSession.filter_config on the backend, so a real API swap later is a drop-in. */
export interface QuizFilterConfig {
  nursing_system: string | null;
  difficulty: Difficulty | null;
  question_types: QuestionType[];
  question_count: number;
}

/** Client-only mock of a QuizSession — nothing here is persisted to the backend. */
export interface MockQuizSession {
  filter_config: QuizFilterConfig;
  questions: Question[];
  current_question_index: number;
  is_complete: boolean;
}

export interface QuestionResponse {
  question_id: string;
  selected_choice_ids: string[];
  is_correct: boolean;
}
