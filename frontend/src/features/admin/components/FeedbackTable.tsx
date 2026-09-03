import { Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FeedbackStatusSelect } from "@/features/admin/components/FeedbackStatusSelect";
import type { AdminIssueReportRow, AdminQuizFeedbackRow, FeedbackKind } from "@/types/admin";

interface FeedbackTableProps {
  kind: FeedbackKind;
  rows: (AdminQuizFeedbackRow | AdminIssueReportRow)[];
  onRowClick: (id: string) => void;
  onDeleteRow: (id: string) => void;
}

export function FeedbackTable({ kind, rows, onRowClick, onDeleteRow }: FeedbackTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Student</TableHead>
          <TableHead>{kind === "survey" ? "Feedback" : "Issue"}</TableHead>
          <TableHead>Submitted</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.id} className="cursor-pointer" onClick={() => onRowClick(row.id)}>
            <TableCell className="font-medium text-foreground">{row.student_name || row.student_email}</TableCell>
            <TableCell className="max-w-md truncate whitespace-normal">
              {kind === "survey" ? (row as AdminQuizFeedbackRow).feedback_text : (row as AdminIssueReportRow).description_preview}
            </TableCell>
            <TableCell>{new Date(row.created_at).toLocaleDateString()}</TableCell>
            <TableCell onClick={(e) => e.stopPropagation()}>
              <FeedbackStatusSelect kind={kind} id={row.id} status={row.status} />
            </TableCell>
            <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="icon-sm" onClick={() => onDeleteRow(row.id)} aria-label="Delete">
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
