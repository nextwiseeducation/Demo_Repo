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

/**
 * Every type the schema supports now has a renderer (see
 * features/quiz/components). NGN_CASE isn't itself a renderer — it's a
 * wrapper: an NGN_CASE question's `ngn_type` says which of the other types
 * it actually renders as (see Question.ngn_type below), so it's deliberately
 * left out of this list and handled by unwrapping to ngn_type instead.
 */
export const SUPPORTED_QUESTION_TYPES: QuestionType[] = [
  "MCQ",
  "SATA",
  "MATRIX",
  "BOWTIE",
  "EMR",
  "DRAG_DROP",
  "CLOZE",
  "HOTSPOT",
];

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

// --- NGN nested shapes -------------------------------------------------
// All ids below are plain numbers, not UUIDs — the backend's NGN stub
// models use ordinary auto-increment PKs (see MatrixRow/BowTieOption/etc.'s
// own "no UUIDPKMixin" comments), unlike Question/AnswerChoice.
//
// Same "hidden until submit" pattern as AnswerChoice.is_correct/rationale
// throughout: every *is_correct/rationale field below is undefined until
// SUBMIT_RESULT merges the revealed answer key in (quizSessionReducer.ts).

export interface MatrixRow {
  id: number;
  text: string;
  display_order: number;
}

export interface MatrixColumn {
  id: number;
  text: string;
  display_order: number;
}

/** Revealed post-submit only — one entry per (row, column) pair that has an answer-key verdict. */
export interface MatrixCellResult {
  row_id: number;
  column_id: number;
  is_correct: boolean;
  rationale: string;
}

export type BowTieSection = "ASSESSMENT" | "CONDITION" | "ACTION";

export const BOWTIE_SECTION_LABELS: Record<BowTieSection, string> = {
  ASSESSMENT: "Assessment",
  CONDITION: "Condition",
  ACTION: "Action",
};

export interface BowTieOption {
  id: number;
  section: BowTieSection;
  option_text: string;
  display_order: number;
  is_correct?: boolean;
  rationale?: string;
}

export interface ClozeOption {
  id: number;
  option_text: string;
  is_correct?: boolean;
  rationale?: string;
}

export interface ClozeBlank {
  id: number;
  blank_key: string;
  display_order: number;
  options: ClozeOption[];
}

export interface DragDropCategory {
  id: number;
  name: string;
  display_order: number;
}

export interface DragDropItem {
  id: number;
  text: string;
  display_order: number;
  correct_category_id?: number | null;
  correct_order?: number | null;
  rationale?: string;
}

export interface HotSpotTarget {
  id: number;
  target_text: string;
  display_order: number;
  is_correct?: boolean;
  rationale?: string;
}

export interface CaseStudy {
  id: number;
  title: string;
  shared_scenario: string;
}

export interface Question {
  id: string;
  question_type: QuestionType;
  /** Only meaningful when question_type is "NGN_CASE" — which real type (MCQ, MATRIX, BOWTIE, ...) this case-study item actually renders as. */
  ngn_type: QuestionType | null;
  stem: string;
  clinical_scenario: string | null;
  /** Accompanying lab table/diagram/EKG strip, when the question has one — a full URL or null. */
  image: string | null;
  case_study: CaseStudy | null;
  case_study_sequence: number | null;
  difficulty: Difficulty;
  /** UWorld's "Subjects" facet — null until the content team backfills it (see backend Question.domain's own comment). */
  domain: string | null;
  domain_id: number | null;
  nursing_system: string;
  nursing_system_id: number;
  topic: string;
  nclex_client_needs_category: string;
  nclex_client_needs_subcategory: string;
  nclex_client_needs_subcategory_id: number;
  clinical_judgment_skill: string;
  answer_choices: AnswerChoice[];
  /** Non-empty only for question_type/ngn_type "MATRIX". */
  matrix_rows: MatrixRow[];
  matrix_columns: MatrixColumn[];
  /** Populated in place by SUBMIT_RESULT — empty until this question is submitted. */
  matrix_cells?: MatrixCellResult[];
  /** Non-empty only for question_type/ngn_type "BOWTIE". */
  bowtie_options: BowTieOption[];
  /** Non-empty only for question_type/ngn_type "CLOZE". */
  cloze_blanks: ClozeBlank[];
  /** Non-empty only for question_type/ngn_type "DRAG_DROP". */
  dragdrop_items: DragDropItem[];
  dragdrop_categories: DragDropCategory[];
  /** Non-empty only for question_type/ngn_type "HOTSPOT". */
  hotspot_targets: HotSpotTarget[];
  /** Short "big idea" the student should walk away with. Optional — most questions won't have one yet. */
  key_takeaway?: string | null;
  /** ISO 8601 datetime string — auto-maintained by TimeStampedMixin on every save. */
  updated_at: string;
}

/** The type actually driving rendering/grading — unwraps NGN_CASE to its ngn_type, same rule as the backend's effective_question_type. */
export function effectiveQuestionType(question: Question): QuestionType {
  if (question.question_type === "NGN_CASE" && question.ngn_type) return question.ngn_type;
  return question.question_type;
}
