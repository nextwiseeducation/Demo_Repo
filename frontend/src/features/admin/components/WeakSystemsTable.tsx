import { EmptyState } from "@/components/common/EmptyState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { WeakSystemRow } from "@/types/analytics";
import { TrendingDown } from "lucide-react";

interface WeakSystemsTableProps {
  rows: WeakSystemRow[];
}

/**
 * May legitimately render fewer than 5 rows (or none) early on — the
 * backend only ranks systems with enough attempts to be statistically
 * meaningful (see MIN_ATTEMPTS_FOR_WEAK_SYSTEM), so a small platform can
 * have no qualifying system yet.
 */
export function WeakSystemsTable({ rows }: WeakSystemsTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Weakest nursing systems</CardTitle>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <EmptyState icon={TrendingDown} title="Not enough attempts yet to rank weak areas" />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nursing system</TableHead>
                <TableHead className="text-right">Attempts</TableHead>
                <TableHead className="text-right">Correct rate</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.id}>
                  <TableCell className="font-medium text-foreground">{row.name}</TableCell>
                  <TableCell className="text-right">{row.attempts}</TableCell>
                  <TableCell className="text-right">{row.correct_rate.toFixed(1)}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
