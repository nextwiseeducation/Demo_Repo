import { Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";

interface BulkActionBarProps {
  selectedCount: number;
  onDelete: () => void;
}

/** Shown only when at least one row is selected. */
export function BulkActionBar({ selectedCount, onDelete }: BulkActionBarProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-muted/50 px-4 py-2">
      <span className="text-sm text-foreground">{selectedCount} selected</span>
      <Button variant="destructive" size="sm" onClick={onDelete}>
        <Trash2 className="h-4 w-4" />
        Delete selected
      </Button>
    </div>
  );
}
