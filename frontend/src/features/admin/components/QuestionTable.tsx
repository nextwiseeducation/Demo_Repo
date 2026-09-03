import { Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DIFFICULTY_LABELS, QUESTION_TABLE_COLUMN_LABELS, type AdminQuestionRow } from "@/types/admin";
import { QUESTION_TYPE_LABELS } from "@/types/question";

interface QuestionTableProps {
  rows: AdminQuestionRow[];
  selectedIds: Set<string>;
  onToggleRow: (id: string, checked: boolean) => void;
  onToggleAll: (checked: boolean) => void;
  onEditRow: (id: string) => void;
  onDeleteRow: (id: string) => void;
}

export function QuestionTable({
  rows,
  selectedIds,
  onToggleRow,
  onToggleAll,
  onEditRow,
  onDeleteRow,
}: QuestionTableProps) {
  const allSelected = rows.length > 0 && rows.every((row) => selectedIds.has(row.id));

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-8">
            <Checkbox
              checked={allSelected}
              onCheckedChange={(checked) => onToggleAll(checked === true)}
              aria-label="Select all questions on this page"
            />
          </TableHead>
          <TableHead>{QUESTION_TABLE_COLUMN_LABELS.stem}</TableHead>
          <TableHead>{QUESTION_TABLE_COLUMN_LABELS.questionType}</TableHead>
          <TableHead>{QUESTION_TABLE_COLUMN_LABELS.nursingSystem}</TableHead>
          <TableHead>{QUESTION_TABLE_COLUMN_LABELS.difficulty}</TableHead>
          <TableHead>{QUESTION_TABLE_COLUMN_LABELS.isActive}</TableHead>
          <TableHead>{QUESTION_TABLE_COLUMN_LABELS.createdAt}</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.id} data-state={selectedIds.has(row.id) ? "selected" : undefined}>
            <TableCell>
              <Checkbox
                checked={selectedIds.has(row.id)}
                onCheckedChange={(checked) => onToggleRow(row.id, checked === true)}
                aria-label={`Select question ${row.id}`}
              />
            </TableCell>
            <TableCell className="max-w-md truncate whitespace-normal text-foreground">
              {row.stem_preview}
            </TableCell>
            <TableCell>{QUESTION_TYPE_LABELS[row.question_type]}</TableCell>
            <TableCell>{row.nursing_system}</TableCell>
            <TableCell>{DIFFICULTY_LABELS[row.difficulty]}</TableCell>
            <TableCell>
              <Badge variant={row.is_active ? "secondary" : "outline"}>
                {row.is_active ? "Active" : "Inactive"}
              </Badge>
            </TableCell>
            <TableCell>{new Date(row.created_at).toLocaleDateString()}</TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-1">
                <Button variant="ghost" size="sm" onClick={() => onEditRow(row.id)}>
                  Edit
                </Button>
                <Button variant="ghost" size="icon-sm" onClick={() => onDeleteRow(row.id)} aria-label="Delete question">
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
