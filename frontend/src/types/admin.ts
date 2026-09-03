import type { QuestionType } from "@/types/question";

export const STEM_PREVIEW_CHARS = 80;
export const ADMIN_QUESTIONS_PAGE_SIZE = 20;
export const ADMIN_FEEDBACK_PAGE_SIZE = 25;

/** Mirrors AdminQuestionListSerializer (backend: apps/admin_api/serializers/questions.py). */
export interface AdminQuestionRow {
  id: string;
  stem_preview: string;
  question_type: QuestionType;
  nursing_system: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  is_active: boolean;
  created_at: string;
}

export interface AdminQuestionFilters {
  question_type?: QuestionType[];
  nursing_system?: number[];
  difficulty?: ("EASY" | "MEDIUM" | "HARD")[];
  is_active?: boolean;
  clinical_judgment_skill?: string[];
  search?: string;
}

export const DIFFICULTY_LABELS: Record<"EASY" | "MEDIUM" | "HARD", string> = {
  EASY: "Easy",
  MEDIUM: "Medium",
  HARD: "Hard",
};

export const CLINICAL_JUDGMENT_SKILL_LABELS: Record<string, string> = {
  RECOGNIZE_CUES: "Recognize Cues",
  ANALYZE_CUES: "Analyze Cues",
  PRIORITIZE_HYPOTHESES: "Prioritize Hypotheses",
  GENERATE_SOLUTIONS: "Generate Solutions",
  TAKE_ACTION: "Take Action",
  EVALUATE_OUTCOMES: "Evaluate Outcomes",
};

export const QUESTION_TABLE_COLUMN_LABELS = {
  id: "Question ID",
  stem: "Stem",
  questionType: "Type",
  nursingSystem: "Nursing System",
  difficulty: "Difficulty",
  isActive: "Active",
  createdAt: "Created",
} as const;

/** Taxonomy tree returned by GET /api/admin/taxonomy/ (backend: apps/admin_api/views/taxonomy.py). */
export interface TaxonomySubtopicOption {
  id: number;
  name: string;
}

export interface TaxonomyTopicOption {
  id: number;
  name: string;
  subtopics: TaxonomySubtopicOption[];
}

export interface TaxonomyNursingSystemOption {
  id: number;
  name: string;
  topics: TaxonomyTopicOption[];
}

export interface TaxonomyDomainOption {
  id: number;
  name: string;
}

export interface TaxonomyClientNeedsSubcategoryOption {
  id: number;
  name: string;
}

export interface TaxonomyClientNeedsCategoryOption {
  id: number;
  name: string;
  exam_type: "RN" | "PN";
  subcategories: TaxonomyClientNeedsSubcategoryOption[];
}

export interface TaxonomyTagOption {
  id: number;
  name: string;
}

export interface TaxonomyCaseStudyOption {
  id: number;
  external_id: string | null;
  title: string;
}

export interface AdminTaxonomy {
  nursing_systems: TaxonomyNursingSystemOption[];
  domains: TaxonomyDomainOption[];
  client_needs_categories: TaxonomyClientNeedsCategoryOption[];
  tags: TaxonomyTagOption[];
  case_studies: TaxonomyCaseStudyOption[];
}

// --- Question detail (GET /api/admin/questions/:id/) ---------------------
// Mirrors AdminQuestionDetailSerializer (backend:
// apps/admin_api/serializers/questions.py). Read-only for now (Phase 4);
// the writable draft shapes these evolve into land with Phase 5's
// QuestionAdminSerializer.

export interface AdminAnswerChoice {
  id: string;
  choice_text: string;
  is_correct: boolean;
  display_order: number;
  rationale: string;
}

export interface AdminMatrixCell {
  column_id: number;
  is_correct: boolean;
  rationale: string;
}

export interface AdminMatrixColumn {
  id: number;
  text: string;
  display_order: number;
}

export interface AdminMatrixRow {
  id: number;
  text: string;
  display_order: number;
  cells: AdminMatrixCell[];
}

export interface AdminBowTieOption {
  id: number;
  section: "ASSESSMENT" | "CONDITION" | "ACTION";
  option_text: string;
  is_correct: boolean;
  display_order: number;
  rationale: string;
}

export interface AdminClozeOption {
  id: number;
  option_text: string;
  is_correct: boolean;
  rationale: string;
}

export interface AdminClozeBlank {
  id: number;
  blank_key: string;
  display_order: number;
  options: AdminClozeOption[];
}

export interface AdminDragDropCategory {
  id: number;
  name: string;
  display_order: number;
}

export interface AdminDragDropItem {
  id: number;
  text: string;
  display_order: number;
  correct_category: number | null;
  correct_order: number | null;
  rationale: string;
}

export interface AdminHotSpotTarget {
  id: number;
  target_text: string;
  is_correct: boolean;
  display_order: number;
  rationale: string;
}

export interface AdminCaseStudy {
  id: number;
  external_id: string | null;
  title: string;
  shared_scenario: string;
}

export interface AdminQuestionDetail {
  id: string;
  external_id: string | null;
  question_type: QuestionType;
  ngn_type: QuestionType | null;
  stem: string;
  clinical_scenario: string | null;
  image: string | null;
  case_study: AdminCaseStudy | null;
  case_study_sequence: number | null;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  domain: string | null;
  domain_id: number | null;
  nursing_system: string;
  nursing_system_id: number;
  topic: string;
  topic_id: number;
  subtopic_id: number | null;
  nclex_client_needs_category_id: number;
  nclex_client_needs_subcategory_id: number;
  clinical_judgment_skill: string;
  clinical_judgment_skill_secondary: string | null;
  cognitive_level: string;
  tag_ids: number[];
  rationale_correct: string | null;
  rationale_incorrect: string | null;
  reference: string | null;
  key_takeaway: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  answer_choices: AdminAnswerChoice[];
  matrix_columns: AdminMatrixColumn[];
  matrix_rows: AdminMatrixRow[];
  bowtie_options: AdminBowTieOption[];
  cloze_blanks: AdminClozeBlank[];
  dragdrop_categories: AdminDragDropCategory[];
  dragdrop_items: AdminDragDropItem[];
  hotspot_targets: AdminHotSpotTarget[];
}

// --- Question write drafts (POST/PUT /api/admin/questions/[:id/]) --------
// Mirror the payload shape QuestionAdminSerializer accepts (backend:
// apps/admin_api/serializers/questions.py). Deliberately a SEPARATE set of
// types from the read shapes above: drafts carry a client-only `key` on
// matrix columns/rows and drag-drop categories (to let a new row reference
// a new sibling before either has a real id — see the serializer's own
// docstring on forward references), which the read shapes never have.

export interface AnswerChoiceDraft {
  id?: string;
  choice_text: string;
  is_correct: boolean;
  display_order: number;
  rationale: string;
}

export interface MatrixColumnDraft {
  key: string;
  text: string;
  display_order: number;
}

export interface MatrixCellDraft {
  column_key: string;
  is_correct: boolean;
  rationale: string;
}

export interface MatrixRowDraft {
  key: string;
  text: string;
  display_order: number;
  cells: MatrixCellDraft[];
}

export interface BowTieOptionDraft {
  section: "ASSESSMENT" | "CONDITION" | "ACTION";
  option_text: string;
  is_correct: boolean;
  display_order: number;
  rationale: string;
}

export interface ClozeOptionDraft {
  option_text: string;
  is_correct: boolean;
  rationale: string;
}

export interface ClozeBlankDraft {
  blank_key: string;
  display_order: number;
  options: ClozeOptionDraft[];
}

export interface DragDropCategoryDraft {
  key: string;
  name: string;
  display_order: number;
}

export interface DragDropItemDraft {
  text: string;
  display_order: number;
  correct_category_key: string | null;
  correct_order: number | null;
  rationale: string;
}

export interface HotSpotTargetDraft {
  target_text: string;
  is_correct: boolean;
  display_order: number;
  rationale: string;
}

export interface CaseStudyDraft {
  id?: number;
  external_id?: string | null;
  title?: string;
  shared_scenario?: string;
}

export interface QuestionDraft {
  external_id?: string | null;
  question_type: QuestionType;
  ngn_type?: QuestionType | null;
  stem: string;
  clinical_scenario?: string | null;
  case_study?: CaseStudyDraft | null;
  case_study_sequence?: number | null;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  domain_id?: number | null;
  nursing_system_id: number;
  topic_id: number;
  subtopic_id?: number | null;
  nclex_client_needs_category_id: number;
  nclex_client_needs_subcategory_id: number;
  clinical_judgment_skill: string;
  clinical_judgment_skill_secondary?: string | null;
  cognitive_level: string;
  tag_ids?: number[];
  rationale_correct?: string | null;
  rationale_incorrect?: string | null;
  reference?: string | null;
  key_takeaway?: string | null;
  is_active?: boolean;
  answer_choices?: AnswerChoiceDraft[];
  matrix_columns?: MatrixColumnDraft[];
  matrix_rows?: MatrixRowDraft[];
  bowtie_options?: BowTieOptionDraft[];
  cloze_blanks?: ClozeBlankDraft[];
  dragdrop_categories?: DragDropCategoryDraft[];
  dragdrop_items?: DragDropItemDraft[];
  hotspot_targets?: HotSpotTargetDraft[];
}

export const COGNITIVE_LEVEL_LABELS: Record<string, string> = {
  REMEMBER: "Remember",
  UNDERSTAND: "Understand",
  APPLY: "Apply",
  ANALYZE: "Analyze",
  EVALUATE: "Evaluate",
  CREATE: "Create",
};

export const BOWTIE_SECTIONS: BowTieOptionDraft["section"][] = ["ASSESSMENT", "CONDITION", "ACTION"];

export const BOWTIE_SECTION_LABELS: Record<BowTieOptionDraft["section"], string> = {
  ASSESSMENT: "Assessment",
  CONDITION: "Condition",
  ACTION: "Action",
};

/** Question types with a metadata-only builder ("edit structure in Django admin" placeholder) until their builder lands. */
export const STRUCTURE_KEYS_BY_TYPE: Record<string, (keyof QuestionDraft)[]> = {
  MCQ: ["answer_choices"],
  SATA: ["answer_choices"],
  EMR: ["answer_choices"],
  MATRIX: ["matrix_columns", "matrix_rows"],
  BOWTIE: ["bowtie_options"],
  CLOZE: ["cloze_blanks"],
  DRAG_DROP: ["dragdrop_categories", "dragdrop_items"],
  HOTSPOT: ["hotspot_targets"],
};

let draftKeyCounter = 0;
/** A fresh client-only key for a new matrix column/row or drag-drop category — never sent as-is, only referenced by column_key/correct_category_key within the same request. */
export function nextDraftKey(): string {
  draftKeyCounter += 1;
  return `draft-${draftKeyCounter}-${Date.now()}`;
}

// --- Bulk import (POST /api/admin/import/, GET /api/admin/import-log/) ---

export interface ImportRowErrorEntry {
  label: string;
  message: string;
}

/** Mirrors ImportResultSerializer (backend: apps/admin_api/serializers/imports.py). */
export interface ImportResultPayload {
  created: number;
  updated: number;
  skipped_existing: number;
  case_studies_created: number;
  case_studies_updated: number;
  questions_imported: number;
  rows_failed: number;
  created_taxonomy: string[];
  errors: ImportRowErrorEntry[];
  dry_run: boolean;
}

/** Mirrors ImportLogSerializer. */
export interface ImportLogEntry {
  id: string;
  uploaded_at: string;
  uploaded_by_email: string | null;
  source_filename: string;
  questions_imported: number;
  rows_failed: number;
  errors: ImportRowErrorEntry[];
}

// --- Feedback dashboard (GET/PATCH/DELETE /api/admin/feedback/...) -------

export type FeedbackKind = "survey" | "issue";

export type FeedbackStatus = "IN_CONSIDERATION" | "IMPLEMENTED" | "REJECTED";

export const FEEDBACK_STATUS_LABELS: Record<FeedbackStatus, string> = {
  IN_CONSIDERATION: "In consideration",
  IMPLEMENTED: "Implemented",
  REJECTED: "Rejected",
};

/**
 * Badge colour per status — amber/green/red, matching the spec literally
 * (Badge's own "secondary" variant is the theme's indigo, not green, so
 * these are explicit classNames built on the same --accent/--success/
 * --destructive tokens the rest of the app already uses, rather than a
 * Badge `variant` name).
 */
export const FEEDBACK_STATUS_BADGE_CLASS: Record<FeedbackStatus, string> = {
  IN_CONSIDERATION: "border-accent/40 bg-accent/10 text-accent",
  IMPLEMENTED: "border-[color:var(--success)]/40 bg-[color:var(--success)]/10 text-[color:var(--success)]",
  REJECTED: "border-destructive/40 bg-destructive/10 text-destructive",
};

export type ReportStatus = "OPEN" | "RESOLVED" | "DISMISSED";

export const REPORT_STATUS_LABELS: Record<ReportStatus, string> = {
  OPEN: "Open",
  RESOLVED: "Resolved",
  DISMISSED: "Dismissed",
};

/** OPEN reads as "not yet triaged" (amber), RESOLVED as the positive outcome (green), DISMISSED as declined (red) — same three-colour scheme as FEEDBACK_STATUS_BADGE_CLASS. */
export const REPORT_STATUS_BADGE_CLASS: Record<ReportStatus, string> = {
  OPEN: "border-accent/40 bg-accent/10 text-accent",
  RESOLVED: "border-[color:var(--success)]/40 bg-[color:var(--success)]/10 text-[color:var(--success)]",
  DISMISSED: "border-destructive/40 bg-destructive/10 text-destructive",
};

/** Mirrors AdminQuizFeedbackListSerializer. */
export interface AdminQuizFeedbackRow {
  id: string;
  student_name: string;
  student_email: string;
  feedback_text: string;
  status: FeedbackStatus;
  created_at: string;
}

/** Mirrors AdminQuizFeedbackDetailSerializer. */
export interface AdminQuizFeedbackDetail {
  id: string;
  student_name: string;
  student_email: string;
  overall_rating: number;
  question_quality_rating: number;
  difficulty_rating: string;
  realism_rating: string;
  rationale_helpfulness_rating: number;
  had_question_issue: boolean;
  issue_question_number: number | null;
  issue_description: string;
  liked_most: string;
  improvement_suggestion: string;
  recommend_likelihood: string;
  status: FeedbackStatus;
  status_updated_at: string | null;
  created_at: string;
}

/** Mirrors AdminQuestionIssueReportListSerializer. */
export interface AdminIssueReportRow {
  id: string;
  student_name: string;
  student_email: string;
  issue_type: string;
  description_preview: string;
  status: ReportStatus;
  created_at: string;
}

/** Mirrors AdminQuestionIssueReportDetailSerializer. */
export interface AdminIssueReportDetail {
  id: string;
  student_name: string;
  student_email: string;
  question: string | null;
  question_stem_snapshot: string;
  question_number_in_quiz: number | null;
  issue_type: string;
  description: string;
  status: ReportStatus;
  created_at: string;
}
