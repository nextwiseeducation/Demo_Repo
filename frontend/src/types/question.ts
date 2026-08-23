export type QuestionType =
  | "MCQ"
  | "SATA"
  | "MATRIX"
  | "BOWTIE"
  | "EMR"
  | "DRAG_DROP"
  | "CLOZE"
  | "HOTSPOT"
  | "NGN_CASE";

/** Only these two render as real, interactive mock questions right now. */
export const SUPPORTED_QUESTION_TYPES: QuestionType[] = ["MCQ", "SATA"];

export const QUESTION_TYPE_LABELS: Record<QuestionType, string> = {
  MCQ: "Multiple Choice",
  SATA: "Select All That Apply",
  MATRIX: "Matrix / Grid",
  BOWTIE: "Bow-Tie",
  EMR: "Extended Multiple Response",
  DRAG_DROP: "Drag and Drop",
  CLOZE: "Drop-down Cloze",
  HOTSPOT: "Enhanced Hot Spot",
  NGN_CASE: "NGN Case Study",
};

export type Difficulty = "EASY" | "MEDIUM" | "HARD";

export const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  EASY: "Easy",
  MEDIUM: "Medium",
  HARD: "Hard",
};

export interface AnswerChoice {
  id: string;
  choice_text: string;
  is_correct: boolean;
  display_order: number;
  /** Shown inline directly under this option once the student submits — the primary explanation mechanism for MCQ/SATA, not a single combined blob. */
  rationale?: string;
}

export interface Question {
  id: string;
  question_type: QuestionType;
  stem: string;
  clinical_scenario: string | null;
  difficulty: Difficulty;
  nursing_system: string;
  topic: string;
  nclex_client_needs_category: string;
  clinical_judgment_skill: string;
  /** Question-level fallback rationale — superseded by AnswerChoice.rationale for MCQ/SATA/EMR, only still meaningful for non-choice-based question types. */
  rationale_correct: string | null;
  rationale_incorrect: string | null;
  answer_choices: AnswerChoice[];
}
