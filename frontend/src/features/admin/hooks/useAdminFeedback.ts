import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import * as adminApi from "@/lib/api/admin";
import { normalizeApiError } from "@/lib/api/errors";
import type { FeedbackKind, FeedbackStatus, ReportStatus } from "@/types/admin";

export function useAdminFeedbackList(kind: FeedbackKind, status: string | undefined, page: number) {
  return useQuery({
    queryKey: ["admin", "feedback", kind, status, page],
    queryFn: () => adminApi.listAdminFeedback(kind, status, page),
    placeholderData: keepPreviousData,
  });
}

export function useAdminFeedbackDetail(kind: FeedbackKind, id: string | null) {
  return useQuery({
    queryKey: ["admin", "feedback-detail", kind, id],
    queryFn: () => adminApi.getAdminFeedback(kind, id as string),
    enabled: id !== null,
  });
}

export function useUpdateFeedbackStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ kind, id, status }: { kind: FeedbackKind; id: string; status: FeedbackStatus | ReportStatus }) =>
      adminApi.updateFeedbackStatus(kind, id, status),
    onSuccess: (_, { kind, id }) => {
      toast.success("Status updated.");
      queryClient.invalidateQueries({ queryKey: ["admin", "feedback", kind] });
      queryClient.invalidateQueries({ queryKey: ["admin", "feedback-detail", kind, id] });
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).detail ?? "Couldn't update the status.");
    },
  });
}

export function useDeleteFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ kind, id }: { kind: FeedbackKind; id: string }) => adminApi.deleteFeedback(kind, id),
    onSuccess: (_, { kind }) => {
      toast.success("Deleted.");
      queryClient.invalidateQueries({ queryKey: ["admin", "feedback", kind] });
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).detail ?? "Couldn't delete this record.");
    },
  });
}
