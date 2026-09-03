import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";

interface PaginationBarProps {
  page: number;
  pageSize: number;
  count: number;
  onPageChange: (page: number) => void;
}

/** App logic ("page 3 of 41"), not a design-system atom — hence common/, not ui/. */
export function PaginationBar({ page, pageSize, count, onPageChange }: PaginationBarProps) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize));

  return (
    <div className="flex items-center justify-between gap-4 text-sm text-muted-foreground">
      <span>
        {count === 0 ? "No results" : `Page ${page} of ${totalPages} · ${count} total`}
      </span>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft className="h-4 w-4" />
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
