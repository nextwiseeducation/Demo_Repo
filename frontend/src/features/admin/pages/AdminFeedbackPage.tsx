import { useState } from "react";

import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { PaginationBar } from "@/components/common/PaginationBar";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AdminPageHeader } from "@/features/admin/components/AdminPageHeader";
import { FeedbackDetailPanel } from "@/features/admin/components/FeedbackDetailPanel";
import { FeedbackTable } from "@/features/admin/components/FeedbackTable";
import { useAdminFeedbackList, useDeleteFeedback } from "@/features/admin/hooks/useAdminFeedback";
import { normalizeApiError } from "@/lib/api/errors";
import {
  FEEDBACK_STATUS_LABELS,
  REPORT_STATUS_LABELS,
  type FeedbackKind,
} from "@/types/admin";
import { MessageSquare } from "lucide-react";

const ALL_STATUS = "__all__";
const PAGE_SIZE = 25;

function FeedbackKindTab({ kind }: { kind: FeedbackKind }) {
  const [status, setStatus] = useState<string | undefined>(undefined);
  const [page, setPage] = useState(1);
  const [openId, setOpenId] = useState<string | null>(null);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  const { data, isPending, isError, error } = useAdminFeedbackList(kind, status, page);
  const deleteMutation = useDeleteFeedback();

  const labels = kind === "survey" ? FEEDBACK_STATUS_LABELS : REPORT_STATUS_LABELS;
  const allLabel = kind === "survey" ? "All statuses" : "All statuses";
  const statusLabels: Record<string, string> = { [ALL_STATUS]: allLabel, ...labels };

  function handleStatusChange(value: string | null) {
    setStatus(value === ALL_STATUS || !value ? undefined : value);
    setPage(1);
  }

  function confirmDelete() {
    if (!pendingDeleteId) return;
    deleteMutation.mutate(
      { kind, id: pendingDeleteId },
      {
        onSuccess: () => {
          setPendingDeleteId(null);
          if (openId === pendingDeleteId) setOpenId(null);
        },
      },
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Select value={status ?? ALL_STATUS} onValueChange={handleStatusChange}>
        <SelectTrigger className="w-48">
          <SelectValue>{(value: string) => statusLabels[value] ?? value}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_STATUS}>{allLabel}</SelectItem>
          {Object.entries(labels).map(([value, label]) => (
            <SelectItem key={value} value={value}>
              {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {isPending ? (
        <Skeleton className="h-96 w-full" />
      ) : isError ? (
        <ErrorState title="Couldn't load feedback" description={normalizeApiError(error).detail ?? undefined} />
      ) : data.results.length === 0 ? (
        <EmptyState icon={MessageSquare} title="Nothing here yet" />
      ) : (
        <>
          <FeedbackTable kind={kind} rows={data.results} onRowClick={setOpenId} onDeleteRow={setPendingDeleteId} />
          <PaginationBar page={page} pageSize={PAGE_SIZE} count={data.count} onPageChange={setPage} />
        </>
      )}

      <FeedbackDetailPanel kind={kind} id={openId} onOpenChange={(open) => !open && setOpenId(null)} onDelete={setPendingDeleteId} />

      <ConfirmDialog
        open={pendingDeleteId !== null}
        onOpenChange={(open) => !open && setPendingDeleteId(null)}
        title="Delete this record?"
        description="This cannot be undone."
        confirmLabel="Delete"
        isPending={deleteMutation.isPending}
        onConfirm={confirmDelete}
      />
    </div>
  );
}

export function AdminFeedbackPage() {
  return (
    <div className="flex flex-col gap-8">
      <AdminPageHeader title="Feedback" description="Triage student survey feedback and issue reports." />

      <Tabs defaultValue="survey">
        <TabsList>
          <TabsTrigger value="survey">Survey feedback</TabsTrigger>
          <TabsTrigger value="issue">Issue reports</TabsTrigger>
        </TabsList>
        <TabsContent value="survey" className="pt-4">
          <FeedbackKindTab kind="survey" />
        </TabsContent>
        <TabsContent value="issue" className="pt-4">
          <FeedbackKindTab kind="issue" />
        </TabsContent>
      </Tabs>
    </div>
  );
}
