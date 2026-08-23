/** Mirrors apps.feedback.models on the backend (backend/apps/feedback/models.py). */

export type DifficultyRating =
  | "MUCH_TOO_EASY"
  | "SOMEWHAT_EASY"
  | "JUST_RIGHT"
  | "SOMEWHAT_DIFFICULT"
  | "MUCH_TOO_DIFFICULT";

export const DIFFICULTY_RATING_LABELS: Record<DifficultyRating, string> = {
  MUCH_TOO_EASY: "Much too easy",
  SOMEWHAT_EASY: "Somewhat easy",
  JUST_RIGHT: "Just right",
  SOMEWHAT_DIFFICULT: "Somewhat difficult",
  MUCH_TOO_DIFFICULT: "Much too difficult",
};

export type RealismRating =
  | "NOT_REALISTIC"
  | "SLIGHTLY_REALISTIC"
  | "MODERATELY_REALISTIC"
  | "VERY_REALISTIC"
  | "EXTREMELY_REALISTIC";

export const REALISM_RATING_LABELS: Record<RealismRating, string> = {
  NOT_REALISTIC: "Not realistic",
  SLIGHTLY_REALISTIC: "Slightly realistic",
  MODERATELY_REALISTIC: "Moderately realistic",
  VERY_REALISTIC: "Very realistic",
  EXTREMELY_REALISTIC: "Extremely realistic",
};

export type RecommendLikelihood = "DEFINITELY_NOT" | "PROBABLY_NOT" | "MAYBE" | "PROBABLY_YES" | "DEFINITELY_YES";

export const RECOMMEND_LIKELIHOOD_LABELS: Record<RecommendLikelihood, string> = {
  DEFINITELY_NOT: "Definitely not",
  PROBABLY_NOT: "Probably not",
  MAYBE: "Maybe",
  PROBABLY_YES: "Probably yes",
  DEFINITELY_YES: "Definitely yes",
};

export interface QuizFeedbackPayload {
  quiz_session?: string;
  overall_rating: number;
  question_quality_rating: number;
  difficulty_rating: DifficultyRating;
  realism_rating: RealismRating;
  rationale_helpfulness_rating: number;
  had_question_issue: boolean;
  issue_question_number?: number;
  issue_description?: string;
  liked_most?: string;
  improvement_suggestion?: string;
  recommend_likelihood: RecommendLikelihood;
}

export type QuestionIssueType =
  | "ANSWER_INCORRECT"
  | "UNCLEAR"
  | "RATIONALE_NEEDS_IMPROVEMENT"
  | "CLINICAL_INFO_INCORRECT"
  | "TYPO_GRAMMAR"
  | "REFERENCE_ISSUE"
  | "OTHER";

export const QUESTION_ISSUE_TYPE_LABELS: Record<QuestionIssueType, string> = {
  ANSWER_INCORRECT: "Answer may be incorrect",
  UNCLEAR: "Question is unclear",
  RATIONALE_NEEDS_IMPROVEMENT: "Rationale needs improvement",
  CLINICAL_INFO_INCORRECT: "Clinical information seems incorrect",
  TYPO_GRAMMAR: "Typo/grammar",
  REFERENCE_ISSUE: "Reference issue",
  OTHER: "Other",
};

export interface QuestionIssueReportPayload {
  // Omitted entirely for today's mock quiz questions (no real Question row
  // to reference yet) — question_stem_snapshot is what keeps the report
  // meaningful until Milestone 3 serves real questions with real ids.
  question?: string;
  question_stem_snapshot?: string;
  quiz_session?: string;
  question_number_in_quiz?: number;
  issue_type: QuestionIssueType;
  description?: string;
}
