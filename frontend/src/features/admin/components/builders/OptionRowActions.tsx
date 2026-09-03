import { ChevronDown, ChevronUp, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";

interface OptionRowActionsProps {
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  onDelete: () => void;
  canMoveUp?: boolean;
  canMoveDown?: boolean;
}

/** Shared move-up/move-down/delete controls for a row in any of the builder lists. */
export function OptionRowActions({ onMoveUp, onMoveDown, onDelete, canMoveUp = true, canMoveDown = true }: OptionRowActionsProps) {
  return (
    <div className="flex items-center gap-0.5">
      {onMoveUp ? (
        <Button variant="ghost" size="icon-xs" onClick={onMoveUp} disabled={!canMoveUp} aria-label="Move up">
          <ChevronUp className="h-3.5 w-3.5" />
        </Button>
      ) : null}
      {onMoveDown ? (
        <Button variant="ghost" size="icon-xs" onClick={onMoveDown} disabled={!canMoveDown} aria-label="Move down">
          <ChevronDown className="h-3.5 w-3.5" />
        </Button>
      ) : null}
      <Button variant="ghost" size="icon-xs" onClick={onDelete} aria-label="Remove">
        <Trash2 className="h-3.5 w-3.5 text-destructive" />
      </Button>
    </div>
  );
}

/** Swaps display_order-bearing items at index i and i+delta, keeping display_order in sync with array position. */
export function reorder<T extends { display_order: number }>(items: T[], index: number, delta: number): T[] {
  const target = index + delta;
  if (target < 0 || target >= items.length) return items;
  const next = [...items];
  [next[index], next[target]] = [next[target], next[index]];
  return next.map((item, i) => ({ ...item, display_order: i }));
}
