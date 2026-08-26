import type { Question } from "@/types/question";

import { apiClient } from "./client";

/** GET /api/questions/ — answer key omitted; every choice's is_correct/rationale is undefined until submitAnswer() reveals it for that specific question. */
export function listQuestions() {
  return apiClient.get<Question[]>("/questions/").then((r) => r.data);
}

export interface SubmitAnswerResult {
  is_correct: boolean;
  choices: { id: string; is_correct: boolean; rationale: string }[];
}

export function submitAnswer(questionId: string, selectedChoiceIds: string[]) {
  return apiClient
    .post<SubmitAnswerResult>(`/questions/${questionId}/submit/`, { selected_choice_ids: selectedChoiceIds })
    .then((r) => r.data);
}
