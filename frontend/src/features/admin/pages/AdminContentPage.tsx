import { useState } from "react";

import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { PaginationBar } from "@/components/common/PaginationBar";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AdminPageHeader } from "@/features/admin/components/AdminPageHeader";
import { BulkActionBar } from "@/features/admin/components/BulkActionBar";
import { ImportHistoryTable } from "@/features/admin/components/ImportHistoryTable";
import { ImportUploadPanel } from "@/features/admin/components/ImportUploadPanel";
import { QuestionFilterBar } from "@/features/admin/components/QuestionFilterBar";
import { QuestionFormDialog } from "@/features/admin/components/QuestionFormDialog";
import { QuestionTable } from "@/features/admin/components/QuestionTable";
import {
  useAdminQuestions,
  useBulkDeleteAdminQuestions,
  useDeleteAdminQuestion,
} from "@/features/admin/hooks/useAdminQuestions";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { normalizeApiError } from "@/lib/api/errors";
import { ADMIN_QUESTIONS_PAGE_SIZE, type AdminQuestionFilters } from "@/types/admin";
import { FileText, Plus } from "lucide-react";

function QuestionsTab() {
  const [filters, setFilters] = useState<AdminQuestionFilters>({});
  const [searchInput, setSearchInput] = useState("");
  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const debouncedSearch = useDebouncedValue(searchInput, 300);

  const effectiveFilters: AdminQuestionFilters = { ...filters, search: debouncedSearch || undefined };
  const { data, isPending, isError, error } = useAdminQuestions(effectiveFilters, page);
  const deleteQuestion = useDeleteAdminQuestion();
  const bulkDelete = useBulkDeleteAdminQuestions();

  function handleFiltersChange(next: AdminQuestionFilters) {
    setFilters(next);
    setPage(1);
  }

  function handleSearchInputChange(value: string) {
    setSearchInput(value);
    setPage(1);
  }

  function toggleRow(id: string, checked: boolean) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function toggleAll(checked: boolean) {
    setSelectedIds(checked ? new Set(data?.results.map((r) => r.id) ?? []) : new Set());
  }

  function handleAddQuestion() {
    setEditingId(null);
    setFormOpen(true);
  }

  function handleEditRow(id: string) {
    setEditingId(id);
    setFormOpen(true);
  }

  function confirmDeleteRow() {
    if (!pendingDeleteId) return;
    deleteQuestion.mutate(pendingDeleteId, { onSuccess: () => setPendingDeleteId(null) });
  }

  function confirmBulkDelete() {
    bulkDelete.mutate(Array.from(selectedIds), {
      onSuccess: () => {
        setSelectedIds(new Set());
        setBulkDeleteOpen(false);
      },
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-2">
        <QuestionFilterBar
          filters={filters}
          searchInput={searchInput}
          onSearchInputChange={handleSearchInputChange}
          onFiltersChange={handleFiltersChange}
        />
        <Button onClick={handleAddQuestion}>
          <Plus className="h-4 w-4" />
          Add question
        </Button>
      </div>

      <BulkActionBar selectedCount={selectedIds.size} onDelete={() => setBulkDeleteOpen(true)} />

      {isPending ? (
        <Skeleton className="h-96 w-full" />
      ) : isError ? (
        <ErrorState title="Couldn't load questions" description={normalizeApiError(error).detail ?? undefined} />
      ) : data.results.length === 0 ? (
        <EmptyState icon={FileText} title="No questions match these filters" />
      ) : (
        <>
          <QuestionTable
            rows={data.results}
            selectedIds={selectedIds}
            onToggleRow={toggleRow}
            onToggleAll={toggleAll}
            onEditRow={handleEditRow}
            onDeleteRow={setPendingDeleteId}
          />
          <PaginationBar page={page} pageSize={ADMIN_QUESTIONS_PAGE_SIZE} count={data.count} onPageChange={setPage} />
        </>
      )}

      <ConfirmDialog
        open={pendingDeleteId !== null}
        onOpenChange={(open) => !open && setPendingDeleteId(null)}
        title="Delete this question?"
        description="This permanently removes the question and its answer key. Any student response history tied to it is removed too. This cannot be undone."
        confirmLabel="Delete"
        isPending={deleteQuestion.isPending}
        onConfirm={confirmDeleteRow}
      />

      <ConfirmDialog
        open={bulkDeleteOpen}
        onOpenChange={setBulkDeleteOpen}
        title={`Delete ${selectedIds.size} question${selectedIds.size === 1 ? "" : "s"}?`}
        description="This permanently removes these questions and their answer keys. Any student response history tied to them is removed too. This cannot be undone."
        confirmLabel="Delete"
        isPending={bulkDelete.isPending}
        onConfirm={confirmBulkDelete}
      />

      <QuestionFormDialog open={formOpen} onOpenChange={setFormOpen} questionId={editingId} />
    </div>
  );
}

export function AdminContentPage() {
  return (
    <div className="flex flex-col gap-8">
      <AdminPageHeader title="Content Team" description="Manage the question bank and bulk imports." />

      <Tabs defaultValue="questions">
        <TabsList>
          <TabsTrigger value="questions">Questions</TabsTrigger>
          <TabsTrigger value="import">Import</TabsTrigger>
          <TabsTrigger value="import-history">Import History</TabsTrigger>
        </TabsList>
        <TabsContent value="questions" className="pt-4">
          <QuestionsTab />
        </TabsContent>
        <TabsContent value="import" className="pt-4">
          <ImportUploadPanel />
        </TabsContent>
        <TabsContent value="import-history" className="pt-4">
          <ImportHistoryTable />
        </TabsContent>
      </Tabs>
    </div>
  );
}
