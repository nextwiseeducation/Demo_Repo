import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import * as adminApi from "@/lib/api/admin";
import { normalizeApiError } from "@/lib/api/errors";
import type { AdminQuestionFilters, QuestionDraft } from "@/types/admin";

/** keepPreviousData: stops the table collapsing to a spinner on every filter/page change (same pattern as QuizSetupPage's facet query). */
export function useAdminQuestions(filters: AdminQuestionFilters, page: number) {
  return useQuery({
    queryKey: ["admin", "questions", filters, page],
    queryFn: () => adminApi.listAdminQuestions(filters, page),
    placeholderData: keepPreviousData,
  });
}

export function useAdminQuestion(id: string | null) {
  return useQuery({
    queryKey: ["admin", "question", id],
    queryFn: () => adminApi.getAdminQuestion(id as string),
    enabled: id !== null,
  });
}

export function useDeleteAdminQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: adminApi.deleteAdminQuestion,
    onSuccess: () => {
      toast.success("Question deleted.");
      queryClient.invalidateQueries({ queryKey: ["admin", "questions"] });
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).detail ?? "Couldn't delete the question.");
    },
  });
}

export function useBulkDeleteAdminQuestions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: adminApi.bulkDeleteAdminQuestions,
    onSuccess: (result) => {
      toast.success(`Deleted ${result.deleted} question${result.deleted === 1 ? "" : "s"}.`);
      queryClient.invalidateQueries({ queryKey: ["admin", "questions"] });
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).detail ?? "Couldn't delete the selected questions.");
    },
  });
}

export function useCreateAdminQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: adminApi.createAdminQuestion,
    onSuccess: () => {
      toast.success("Question created.");
      queryClient.invalidateQueries({ queryKey: ["admin", "questions"] });
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).detail ?? "Couldn't create the question.");
    },
  });
}

export function useUpdateAdminQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, draft }: { id: string; draft: QuestionDraft }) => adminApi.updateAdminQuestion(id, draft),
    onSuccess: (_, { id }) => {
      toast.success("Question updated.");
      queryClient.invalidateQueries({ queryKey: ["admin", "questions"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "question", id] });
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).detail ?? "Couldn't update the question.");
    },
  });
}
