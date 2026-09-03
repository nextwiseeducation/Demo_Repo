import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/common/EmptyState";
import { CHART_COLORS } from "@/types/analytics";
import type { SystemAttemptRow } from "@/types/analytics";
import { BarChart3 } from "lucide-react";

interface SystemAttemptsChartProps {
  rows: SystemAttemptRow[];
}

/** Real data — no sample badge. Horizontal bars so long nursing-system names stay readable. */
export function SystemAttemptsChart({ rows }: SystemAttemptsChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Most attempted nursing systems</CardTitle>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <EmptyState icon={BarChart3} title="No question attempts yet" />
        ) : (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rows} layout="vertical" margin={{ left: 24, right: 16, top: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value) => [value, "Attempts"]} />
                <Bar dataKey="attempts" fill={CHART_COLORS[0]} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
