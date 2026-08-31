import type { Paginated } from "@/types/api";
import type { Question } from "@/types/question";

import { apiClient } from "./client";

/**
 * Hard ceiling on how many pages listQuestions() will fetch.
 *
 * Purely a runaway guard: if the API ever returned a malformed envelope
 * whose `next` never cleared, the loop below would spin forever and hang
 * the setup page. At the backend's 50-per-page default this still allows
 * 10,000 questions, comfortably beyond the 4,000+ the bank is specced for.
 */
const MAX_PAGES = 200;

/**
 * GET /api/questions/ — every active question, answer key omitted (each
 * choice's is_correct/rationale stays undefined until submitAnswer()
 * reveals it for that specific question).
 *
 * The endpoint is paginated, but this returns a flat Question[] because the
 * quiz setup page filters the whole bank client-side to build its dropdowns
 * and match counts — it genuinely needs every question, not one page.
 *
 * Pages by explicit `?page=N` rather than by following the envelope's
 * `next` URL: `next` is absolute, and behind Vite's dev proxy it is built
 * from a host the browser isn't talking to. Requesting the relative path
 * keeps apiClient's baseURL (and its auth interceptor) in play for every
 * page.
 *
 * KNOWN LIMITATION: this issues one request per 50 questions, so it scales
 * linearly with the bank — fine at today's size, slow once the 4,000+
 * question batch lands. The real fix is server-side filtering on this
 * endpoint (CLAUDE.md, Milestone 3), which removes the need to pull the
 * whole bank down at all. Revisit here when that arrives.
 */
export async function listQuestions(): Promise<Question[]> {
  const questions: Question[] = [];

  for (let page = 1; page <= MAX_PAGES; page += 1) {
    const { data } = await apiClient.get<Paginated<Question> | Question[]>("/questions/", {
      params: { page },
    });

    // Tolerates BOTH the paginated envelope and a bare array. The frontend
    // and backend are separate Render services built from one repo, so a
    // single push redeploys them in parallel and one is briefly live
    // against the other's previous version. Without this, whichever landed
    // first would break the quiz setup page for that window: an old backend
    // ignores ?page and returns a bare array (making data.results
    // undefined), while a new backend returns an envelope an old client
    // cannot read. Accepting either shape makes deploy order irrelevant.
    //
    // Safe to delete once the paginated backend is live everywhere.
    if (Array.isArray(data)) return data;

    questions.push(...data.results);
    if (!data.next) break;
  }

  return questions;
}

export interface SubmitAnswerResult {
  is_correct: boolean;
  choices: { id: string; is_correct: boolean; rationale: string }[];
}

/**
 * POST /api/questions/<id>/submit/ — grades one question and returns the
 * answer key for it.
 *
 * `selectedChoiceIds` must be non-empty: the backend rejects an empty
 * selection with a 400 precisely so that skipping a question can't be used
 * to fetch its answers without attempting it. The submit button is disabled
 * while nothing is selected (QuizSessionPage), so this holds by
 * construction.
 */
export function submitAnswer(questionId: string, selectedChoiceIds: string[]) {
  return apiClient
    .post<SubmitAnswerResult>(`/questions/${questionId}/submit/`, { selected_choice_ids: selectedChoiceIds })
    .then((r) => r.data);
}
