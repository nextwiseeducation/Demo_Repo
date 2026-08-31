import { Check, X } from "lucide-react";

import { cn } from "@/lib/utils";
import type { MatrixCellResult, MatrixColumn, MatrixRow } from "@/types/question";

export function MatrixQuestion({
  rows,
  columns,
  selections,
  submitted,
  cellResults,
  onSelect,
}: {
  rows: MatrixRow[];
  columns: MatrixColumn[];
  selections: { row_id: number; column_id: number }[];
  submitted: boolean;
  cellResults?: MatrixCellResult[];
  onSelect: (rowId: number, columnId: number) => void;
}) {
  const selectedByRow = new Map(selections.map((s) => [s.row_id, s.column_id]));
  const resultFor = (rowId: number, columnId: number) =>
    cellResults?.find((c) => c.row_id === rowId && c.column_id === columnId);

  const sortedRows = [...rows].sort((a, b) => a.display_order - b.display_order);
  const sortedColumns = [...columns].sort((a, b) => a.display_order - b.display_order);

  return (
    <div className="matrix">
      <p className="sata-label">Select one option per row</p>
      <div className="matrix-scroll">
        <table className="matrix-table">
          <thead>
            <tr>
              <th className="matrix-row-head" />
              {sortedColumns.map((column) => (
                <th key={column.id} className="matrix-col-head">
                  {column.text}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((row) => {
              const selectedColumnId = selectedByRow.get(row.id);
              return (
                <tr key={row.id}>
                  <th className="matrix-row-head" scope="row">
                    {row.text}
                  </th>
                  {sortedColumns.map((column) => {
                    const isSelected = selectedColumnId === column.id;
                    const result = resultFor(row.id, column.id);
                    const isCorrectCell = submitted && result?.is_correct;
                    const isWrongPick = submitted && isSelected && result && !result.is_correct;
                    return (
                      <td key={column.id} className="matrix-cell">
                        <button
                          type="button"
                          className={cn(
                            "matrix-radio",
                            isSelected && !submitted && "selected",
                            isCorrectCell && "correct",
                            isWrongPick && "incorrect",
                          )}
                          disabled={submitted}
                          aria-pressed={isSelected}
                          aria-label={`${row.text}: ${column.text}`}
                          onClick={() => onSelect(row.id, column.id)}
                        >
                          {isCorrectCell ? (
                            <Check className="h-3 w-3" />
                          ) : isWrongPick ? (
                            <X className="h-3 w-3" />
                          ) : (
                            isSelected && <span className="matrix-dot" />
                          )}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {submitted && (
        <div className="matrix-rationales">
          {sortedRows.map((row) => {
            const correctCell = cellResults?.find((c) => c.row_id === row.id && c.is_correct);
            if (!correctCell?.rationale) return null;
            return (
              <p key={row.id} className="choice-rationale matrix-row-rationale">
                <span className="matrix-row-rationale-label">{row.text}: </span>
                {correctCell.rationale}
              </p>
            );
          })}
        </div>
      )}
    </div>
  );
}
