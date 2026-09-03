import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { OptionRowActions } from "@/features/admin/components/builders/OptionRowActions";
import { RationaleField } from "@/features/admin/components/builders/RationaleField";
import { nextDraftKey, type MatrixColumnDraft, type MatrixRowDraft } from "@/types/admin";
import { useState } from "react";

interface MatrixBuilderProps {
  columns: MatrixColumnDraft[];
  rows: MatrixRowDraft[];
  onColumnsChange: (columns: MatrixColumnDraft[]) => void;
  onRowsChange: (rows: MatrixRowDraft[]) => void;
}

const MIN_COLUMNS = 2;

/** Cells nest under rows (one radio group per row) — the shape the "exactly one correct column per row" rule and this grid both want. */
export function MatrixBuilder({ columns, rows, onColumnsChange, onRowsChange }: MatrixBuilderProps) {
  const [expandedCell, setExpandedCell] = useState<string | null>(null);

  function addColumn() {
    const key = nextDraftKey();
    onColumnsChange([...columns, { key, text: "", display_order: columns.length }]);
    onRowsChange(
      rows.map((row) => ({
        ...row,
        cells: [...row.cells, { column_key: key, is_correct: false, rationale: "" }],
      })),
    );
  }

  function updateColumn(index: number, text: string) {
    onColumnsChange(columns.map((c, i) => (i === index ? { ...c, text } : c)));
  }

  function removeColumn(index: number) {
    const removedKey = columns[index].key;
    onColumnsChange(columns.filter((_, i) => i !== index).map((c, i) => ({ ...c, display_order: i })));
    onRowsChange(rows.map((row) => ({ ...row, cells: row.cells.filter((c) => c.column_key !== removedKey) })));
  }

  function addRow() {
    onRowsChange([
      ...rows,
      {
        key: nextDraftKey(),
        text: "",
        display_order: rows.length,
        cells: columns.map((c) => ({ column_key: c.key, is_correct: false, rationale: "" })),
      },
    ]);
  }

  function updateRowText(index: number, text: string) {
    onRowsChange(rows.map((r, i) => (i === index ? { ...r, text } : r)));
  }

  function removeRow(index: number) {
    onRowsChange(rows.filter((_, i) => i !== index).map((r, i) => ({ ...r, display_order: i })));
  }

  function setCorrectCell(rowIndex: number, columnKey: string) {
    onRowsChange(
      rows.map((row, i) =>
        i === rowIndex
          ? { ...row, cells: row.cells.map((cell) => ({ ...cell, is_correct: cell.column_key === columnKey })) }
          : row,
      ),
    );
  }

  function updateCellRationale(rowIndex: number, columnKey: string, rationale: string) {
    onRowsChange(
      rows.map((row, i) =>
        i === rowIndex
          ? { ...row, cells: row.cells.map((cell) => (cell.column_key === columnKey ? { ...cell, rationale } : cell)) }
          : row,
      ),
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-foreground">Matrix / Grid</span>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={addColumn}>
            <Plus className="h-4 w-4" />
            Add column
          </Button>
          <Button variant="outline" size="sm" onClick={addRow} disabled={columns.length === 0}>
            <Plus className="h-4 w-4" />
            Add row
          </Button>
        </div>
      </div>

      {columns.length < MIN_COLUMNS ? (
        <p className="text-xs text-destructive">At least {MIN_COLUMNS} columns are required.</p>
      ) : null}

      {columns.length > 0 ? (
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Row</TableHead>
                {columns.map((col, colIndex) => (
                  <TableHead key={col.key}>
                    <div className="flex items-center gap-1">
                      <Input
                        value={col.text}
                        onChange={(e) => updateColumn(colIndex, e.target.value)}
                        placeholder={`Column ${colIndex + 1}`}
                        className="h-7 text-xs"
                      />
                      <OptionRowActions onDelete={() => removeColumn(colIndex)} />
                    </div>
                  </TableHead>
                ))}
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row, rowIndex) => (
                <TableRow key={row.key}>
                  <TableCell>
                    <Input
                      value={row.text}
                      onChange={(e) => updateRowText(rowIndex, e.target.value)}
                      placeholder={`Row ${rowIndex + 1}`}
                      className="h-7 min-w-40 text-xs"
                    />
                  </TableCell>
                  {columns.map((col) => {
                    const cell = row.cells.find((c) => c.column_key === col.key);
                    const cellKey = `${row.key}:${col.key}`;
                    return (
                      <TableCell key={col.key}>
                        <div className="flex flex-col gap-1">
                          <button
                            type="button"
                            onClick={() => setCorrectCell(rowIndex, col.key)}
                            className={`h-7 w-full rounded border text-xs ${
                              cell?.is_correct
                                ? "border-primary bg-primary text-primary-foreground"
                                : "border-border bg-background text-muted-foreground"
                            }`}
                          >
                            {cell?.is_correct ? "Correct" : "—"}
                          </button>
                          <button
                            type="button"
                            className="text-left text-[10px] text-muted-foreground underline"
                            onClick={() => setExpandedCell(expandedCell === cellKey ? null : cellKey)}
                          >
                            Rationale
                          </button>
                          {expandedCell === cellKey ? (
                            <RationaleField
                              value={cell?.rationale ?? ""}
                              onChange={(v) => updateCellRationale(rowIndex, col.key, v)}
                              label=""
                            />
                          ) : null}
                        </div>
                      </TableCell>
                    );
                  })}
                  <TableCell>
                    <OptionRowActions onDelete={() => removeRow(rowIndex)} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : null}
    </div>
  );
}
