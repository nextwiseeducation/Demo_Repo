import type { FacetCounts, QuizFilters, QuizSession } from "@/types/quiz";

import { apiClient } from "./client";
import type { SubmitAnswerResult } from "./questions";

/**
 * GET /api/quizzes/facet-counts/ — every live count the quiz-setup page's 5
 * cards need, scoped to the current student and whatever OTHER filters are
 * already selected. Accepts a partial filter set on purpose: the caller
 * debounces the full in-progress selection, not just the "final" one.
 *
 * Array filters are sent comma-joined (domains=1,2), NOT via axios's
 * default `{ params: { domains: [1, 2] } }` — that serializes as
 * `domains[]=1&domains[]=2` (bracket notation), which
 * request.query_params.getlist("domains") on the Django side would not
 * see at all (it's a different key, "domains[]"). Comma-joining matches
 * the fallback apps.quizzes.views._parse_facet_query_params already
 * expects, so no bracket-key handling is needed on either side.
 */
export function getFacetCounts(filters: Partial<QuizFilters>) {
  const params: Record<string, string> = {};
  if (filters.question_types?.length) params.question_types = filters.question_types.join(",");
  if (filters.status_filters?.length) params.status_filters = filters.status_filters.join(",");
  if (filters.domains?.length) params.domains = filters.domains.join(",");
  if (filters.nursing_systems?.length) params.nursing_systems = filters.nursing_systems.join(",");
  if (filters.nclex_client_needs_subcategories?.length) {
    params.nclex_client_needs_subcategories = filters.nclex_client_needs_subcategories.join(",");
  }

  return apiClient.get<FacetCounts>("/quizzes/facet-counts/", { params }).then((r) => r.data);
}

/** POST /api/quizzes/sessions/ — "Generate Quiz". Returns the created session, questions already ordered/included. */
export function createQuizSession(filters: QuizFilters) {
  return apiClient.post<QuizSession>("/quizzes/sessions/", filters).then((r) => r.data);
}

/**
 * POST /api/quizzes/sessions/<id>/answers/ — grades AND persists an answer
 * within a real session, unlike questions.ts' submitAnswer (stateless
 * preview). This is what the live quiz-taking flow uses.
 */
export function submitSessionAnswer(
  sessionId: string,
  payload: { questionId: string; selectedChoiceIds: string[]; timeTakenSeconds: number },
) {
  return apiClient
    .post<SubmitAnswerResult>(`/quizzes/sessions/${sessionId}/answers/`, {
      question_id: payload.questionId,
      selected_choice_ids: payload.selectedChoiceIds,
      time_taken_seconds: payload.timeTakenSeconds,
    })
    .then((r) => r.data);
}

/** POST /api/quizzes/bookmarks/toggle/ — UWorld's "Marked" flag. */
export function toggleBookmark(questionId: string) {
  return apiClient.post<{ marked: boolean }>("/quizzes/bookmarks/toggle/", { question_id: questionId }).then((r) => r.data);
}
