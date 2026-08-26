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
  /**
   * Both undefined until the student submits this question — GET
   * /api/questions/ deliberately omits the answer key (see
   * PublicAnswerChoiceSerializer on the backend), so a student can't read
   * the correct answer from the network tab before answering. Populated in
   * place by the SUBMIT_RESULT reducer action once
   * questionsApi.submitAnswer() resolves for this question.
   */
  is_correct?: boolean;
  rationale?: string;
  display_order: number;
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
  answer_choices: AnswerChoice[];
}
