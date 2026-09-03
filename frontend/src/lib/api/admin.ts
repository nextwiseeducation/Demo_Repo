import type { Paginated } from "@/types/api";
import type { AdminAnalytics } from "@/types/analytics";
import type {
  AdminIssueReportDetail,
  AdminIssueReportRow,
  AdminQuestionDetail,
  AdminQuestionFilters,
  AdminQuestionRow,
  AdminQuizFeedbackDetail,
  AdminQuizFeedbackRow,
  AdminTaxonomy,
  FeedbackKind,
  FeedbackStatus,
  ImportLogEntry,
  ImportResultPayload,
  QuestionDraft,
  ReportStatus,
} from "@/types/admin";

import { apiClient } from "./client";

/** GET /api/admin/analytics/ — superuser-only platform metrics for the Business Analytics dashboard. */
export function getAnalytics() {
  return apiClient.get<AdminAnalytics>("/admin/analytics/").then((r) => r.data);
}

/** GET /api/admin/taxonomy/ — nested taxonomy tree for the question form's dropdowns and the filter bar. */
export function getTaxonomy() {
  return apiClient.get<AdminTaxonomy>("/admin/taxonomy/").then((r) => r.data);
}

/**
 * GET /api/admin/questions/ — the Content Team question table.
 *
 * Array filters are comma-joined, matching the backend's hand-rolled param
 * parsing (apps/admin_api/services/question_filters.py) — same convention
 * as lib/api/quizzes.ts's getFacetCounts, not axios's default bracket
 * serialization.
 */
export function listAdminQuestions(filters: AdminQuestionFilters, page: number) {
  const params: Record<string, string | number> = { page };
  if (filters.question_type?.length) params.question_type = filters.question_type.join(",");
  if (filters.nursing_system?.length) params.nursing_system = filters.nursing_system.join(",");
  if (filters.difficulty?.length) params.difficulty = filters.difficulty.join(",");
  if (filters.clinical_judgment_skill?.length) {
    params.clinical_judgment_skill = filters.clinical_judgment_skill.join(",");
  }
  if (filters.is_active !== undefined) params.is_active = String(filters.is_active);
  if (filters.search) params.search = filters.search;

  return apiClient.get<Paginated<AdminQuestionRow>>("/admin/questions/", { params }).then((r) => r.data);
}

/** GET /api/admin/questions/:id/ — full question detail, answer key included, for the edit form. */
export function getAdminQuestion(id: string) {
  return apiClient.get<AdminQuestionDetail>(`/admin/questions/${id}/`).then((r) => r.data);
}

/** DELETE /api/admin/questions/:id/ — single-question delete. */
export function deleteAdminQuestion(id: string) {
  return apiClient.delete<void>(`/admin/questions/${id}/`).then((r) => r.data);
}

/** POST /api/admin/questions/bulk-delete/ — deletes every question whose id is in `ids`. */
export function bulkDeleteAdminQuestions(ids: string[]) {
  return apiClient
    .post<{ deleted: number }>("/admin/questions/bulk-delete/", { ids })
    .then((r) => r.data);
}

/** POST /api/admin/questions/ — create a question (any of the 9 types, full NGN structure included). */
export function createAdminQuestion(draft: QuestionDraft) {
  return apiClient.post<AdminQuestionDetail>("/admin/questions/", draft).then((r) => r.data);
}

/** PUT /api/admin/questions/:id/ — full update. question_type is immutable once created. */
export function updateAdminQuestion(id: string, draft: QuestionDraft) {
  return apiClient.put<AdminQuestionDetail>(`/admin/questions/${id}/`, draft).then((r) => r.data);
}

export interface UploadImportOptions {
  update?: boolean;
  dryRun?: boolean;
  onUploadProgress?: (percent: number) => void;
}

/**
 * POST /api/admin/import/ — uploads an NGN Item Bank workbook and imports
 * it synchronously. onUploadProgress reports BYTES UPLOADED, not rows
 * imported — the import itself runs after the last byte lands, so the
 * caller should treat 100% upload progress as "now importing", not "done".
 */
export function uploadImport(file: File, options: UploadImportOptions = {}) {
  const formData = new FormData();
  formData.append("file", file);
  if (options.update) formData.append("update", "true");
  if (options.dryRun) formData.append("dry_run", "true");

  return apiClient
    .post<ImportResultPayload>("/admin/import/", formData, {
      onUploadProgress: (event) => {
        if (!options.onUploadProgress || !event.total) return;
        options.onUploadProgress(Math.round((event.loaded / event.total) * 100));
      },
    })
    .then((r) => r.data);
}

/** GET /api/admin/import-log/ — paginated history of past bulk imports. */
export function listImportLog(page: number) {
  return apiClient.get<Paginated<ImportLogEntry>>("/admin/import-log/", { params: { page } }).then((r) => r.data);
}

/**
 * GET /api/admin/feedback/?kind=survey|issue&status=...&page=...
 *
 * Returns a union type rather than overloading on `kind` — `kind` is
 * typically a variable (not a string literal) at call sites (see
 * useAdminFeedbackList), and TS overloads can't select between signatures
 * on a non-literal argument. Callers narrow the result themselves via
 * `kind === "survey"`, same as the components already do for the row union.
 */
export function listAdminFeedback(kind: FeedbackKind, status: string | undefined, page: number) {
  const params: Record<string, string | number> = { kind, page };
  if (status) params.status = status;
  return apiClient
    .get<Paginated<AdminQuizFeedbackRow | AdminIssueReportRow>>("/admin/feedback/", { params })
    .then((r) => r.data);
}

/** GET /api/admin/feedback/:kind/:id/ — full detail for the side panel. */
export function getAdminFeedback(kind: FeedbackKind, id: string) {
  return apiClient.get<AdminQuizFeedbackDetail | AdminIssueReportDetail>(`/admin/feedback/${kind}/${id}/`).then((r) => r.data);
}

/** PATCH /api/admin/feedback/:kind/:id/ — status update only. */
export function updateFeedbackStatus(kind: FeedbackKind, id: string, newStatus: FeedbackStatus | ReportStatus) {
  return apiClient
    .patch<AdminQuizFeedbackDetail | AdminIssueReportDetail>(`/admin/feedback/${kind}/${id}/`, { status: newStatus })
    .then((r) => r.data);
}

/** DELETE /api/admin/feedback/:kind/:id/ */
export function deleteFeedback(kind: FeedbackKind, id: string) {
  return apiClient.delete<void>(`/admin/feedback/${kind}/${id}/`).then((r) => r.data);
}
