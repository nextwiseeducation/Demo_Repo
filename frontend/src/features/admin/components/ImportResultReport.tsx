import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ImportResultPayload } from "@/types/admin";

interface ImportResultReportProps {
  result: ImportResultPayload;
}

export function ImportResultReport({ result }: ImportResultReportProps) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border p-4">
      <div className="flex items-center gap-2">
        {result.rows_failed === 0 ? (
          <CheckCircle2 className="h-5 w-5 text-[color:var(--success)]" />
        ) : (
          <AlertTriangle className="h-5 w-5 text-accent" />
        )}
        <span className="font-medium text-foreground">
          {result.dry_run ? "Dry run complete — nothing was written." : "Import complete."}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Created" value={result.created} />
        <Stat label="Updated" value={result.updated} />
        <Stat label="Skipped (already exist)" value={result.skipped_existing} />
        <Stat label="Rows failed" value={result.rows_failed} tone={result.rows_failed > 0 ? "destructive" : undefined} />
        <Stat label="Case studies created" value={result.case_studies_created} />
        <Stat label="Case studies updated" value={result.case_studies_updated} />
      </div>

      {result.created_taxonomy.length > 0 ? (
        <div>
          <p className="text-xs font-medium text-accent">
            Created {result.created_taxonomy.length} new taxonomy row(s) — check for typos:
          </p>
          <ul className="mt-1 list-inside list-disc text-xs text-muted-foreground">
            {result.created_taxonomy.map((entry) => (
              <li key={entry}>{entry}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {result.errors.length > 0 ? (
        <div>
          <p className="mb-1 text-xs font-medium text-destructive">{result.errors.length} row(s) failed validation:</p>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Row</TableHead>
                <TableHead>Reason</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {result.errors.map((error, i) => (
                <TableRow key={i}>
                  <TableCell className="font-medium text-foreground">{error.label}</TableCell>
                  <TableCell className="whitespace-normal text-muted-foreground">{error.message}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : null}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone?: "destructive" }) {
  return (
    <div className="flex flex-col gap-0.5 rounded-md border border-border px-3 py-2">
      <span className="text-[11px] text-muted-foreground">{label}</span>
      {tone === "destructive" && value > 0 ? (
        <Badge variant="destructive" className="w-fit">
          {value}
        </Badge>
      ) : (
        <span className="text-sm font-semibold text-foreground">{value}</span>
      )}
    </div>
  );
}
