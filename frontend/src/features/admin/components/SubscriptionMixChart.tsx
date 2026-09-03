import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SampleDataBadge } from "@/features/admin/components/SampleDataBadge";
import { CHART_COLORS } from "@/types/analytics";
import type { SubscriptionMix } from "@/types/analytics";

interface SubscriptionMixChartProps {
  mix: SubscriptionMix;
}

export function SubscriptionMixChart({ mix }: SubscriptionMixChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Subscription tier breakdown</CardTitle>
        {mix.is_sample ? (
          <CardAction>
            <SampleDataBadge />
          </CardAction>
        ) : null}
      </CardHeader>
      <CardContent>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={mix.points}
                dataKey="percentage"
                nameKey="tier"
                innerRadius="55%"
                outerRadius="80%"
                paddingAngle={2}
              >
                {mix.points.map((point, index) => (
                  <Cell key={point.tier} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value}%`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
