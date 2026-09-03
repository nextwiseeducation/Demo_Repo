import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SampleDataBadge } from "@/features/admin/components/SampleDataBadge";
import { CHART_COLORS } from "@/types/analytics";
import type { RevenueSeries } from "@/types/analytics";

interface RevenueChartProps {
  series: RevenueSeries;
}

export function RevenueChart({ series }: RevenueChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Monthly revenue</CardTitle>
        {series.is_sample ? (
          <CardAction>
            <SampleDataBadge />
          </CardAction>
        ) : null}
      </CardHeader>
      <CardContent>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={series.points} margin={{ left: 8, right: 8, top: 8, bottom: 0 }}>
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `$${v}`} width={56} />
              <Tooltip formatter={(value) => [`$${value}`, "Revenue"]} />
              <Line type="monotone" dataKey="revenue" stroke={CHART_COLORS[0]} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
