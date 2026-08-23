import type { QuestionIssueReportPayload, QuizFeedbackPayload } from "@/types/feedback";

import { apiClient } from "./client";

export function submitQuizFeedback(payload: QuizFeedbackPayload) {
  return apiClient.post("/feedback/quiz/", payload).then((r) => r.data);
}

export function submitQuestionIssueReport(payload: QuestionIssueReportPayload) {
  return apiClient.post("/feedback/question-issue/", payload).then((r) => r.data);
}
