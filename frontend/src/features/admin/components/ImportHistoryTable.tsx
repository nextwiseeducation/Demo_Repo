import { useState } from "react";

import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { PaginationBar } from "@/components/common/PaginationBar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useImportLog } from "@/features/admin/hooks/useAdminImport";
import { normalizeApiError } from "@/lib/api/errors";
import { History } from "lucide-react";

const PAGE_SIZE = 20;

export function ImportHistoryTable() {
  const [page, setPage] = useState(1);
  const { data, isPending, isError, error } = useImportLog(page);

  if (isPending) return <Skeleton className="h-64 w-full" />;
  if (isError) return <ErrorState title="Couldn't load import history" description={normalizeApiError(error).detail ?? undefined} />;
  if (data.results.length === 0) return <EmptyState icon={History} title="No imports yet" />;

  return (
    <div className="flex flex-col gap-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Uploaded by</TableHead>
            <TableHead>File</TableHead>
            <TableHead className="text-right">Imported</TableHead>
            <TableHead className="text-right">Failed</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.results.map((entry) => (
            <TableRow key={entry.id}>
              <TableCell>{new Date(entry.uploaded_at).toLocaleString()}</TableCell>
              <TableCell>{entry.uploaded_by_email ?? "Command line"}</TableCell>
              <TableCell>{entry.source_filename || "—"}</TableCell>
              <TableCell className="text-right">{entry.questions_imported}</TableCell>
              <TableCell className="text-right">
                {entry.rows_failed > 0 ? (
                  <Badge variant="destructive">{entry.rows_failed}</Badge>
                ) : (
                  entry.rows_failed
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <PaginationBar page={page} pageSize={PAGE_SIZE} count={data.count} onPageChange={setPage} />
    </div>
  );
}
