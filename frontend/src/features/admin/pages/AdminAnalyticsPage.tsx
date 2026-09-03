import { ErrorState } from "@/components/common/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { AdminPageHeader } from "@/features/admin/components/AdminPageHeader";
import { RevenueChart } from "@/features/admin/components/RevenueChart";
import { StatTile } from "@/features/admin/components/StatTile";
import { SubscriptionMixChart } from "@/features/admin/components/SubscriptionMixChart";
import { SystemAttemptsChart } from "@/features/admin/components/SystemAttemptsChart";
import { WeakSystemsTable } from "@/features/admin/components/WeakSystemsTable";
import { useAdminAnalytics } from "@/features/admin/hooks/useAdminAnalytics";
import { normalizeApiError } from "@/lib/api/errors";
import { ANALYTICS_TILE_LABELS } from "@/types/analytics";

export function AdminAnalyticsPage() {
  const { data, isPending, isError, error } = useAdminAnalytics();

  return (
    <div className="flex flex-col gap-8">
      <AdminPageHeader
        title="Business Analytics"
        description="Platform-wide enrollment, revenue and performance metrics."
      />

      {isPending ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState title="Couldn't load analytics" description={normalizeApiError(error).detail ?? undefined} />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatTile label={ANALYTICS_TILE_LABELS.totalStudents} value={data.total_students} />
            <StatTile
              label={ANALYTICS_TILE_LABELS.totalRevenue}
              value={`$${Number(data.total_revenue).toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
            />
            <StatTile
              label={ANALYTICS_TILE_LABELS.momGrowth}
              value={data.mom_student_growth === null ? null : data.mom_student_growth}
              suffix={data.mom_student_growth === null ? undefined : "%"}
            />
            <StatTile label={ANALYTICS_TILE_LABELS.questionsAnswered} value={data.total_questions_answered} />
            <StatTile
              label={ANALYTICS_TILE_LABELS.avgQuizScore}
              value={data.avg_quiz_score}
              suffix={data.avg_quiz_score === null ? undefined : "%"}
            />
            <StatTile label={ANALYTICS_TILE_LABELS.completionRate} value={data.completion_rate} suffix="%" />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <RevenueChart series={data.revenue_series} />
            <SubscriptionMixChart mix={data.subscription_mix} />
          </div>

          <SystemAttemptsChart rows={data.top_systems_by_attempts} />
          <WeakSystemsTable rows={data.weakest_systems} />
        </>
      )}
    </div>
  );
}
