export interface SystemAttemptRow {
  id: number;
  name: string;
  attempts: number;
}

export interface WeakSystemRow {
  id: number;
  name: string;
  attempts: number;
  correct: number;
  correct_rate: number;
}

export interface RevenuePoint {
  month: string;
  revenue: number;
}

export interface RevenueSeries {
  points: RevenuePoint[];
  is_sample: boolean;
}

export interface SubscriptionMixPoint {
  tier: string;
  percentage: number;
}

export interface SubscriptionMix {
  points: SubscriptionMixPoint[];
  is_sample: boolean;
}

/** Mirrors AdminAnalyticsSerializer (backend: apps/admin_api/serializers/analytics.py). */
export interface AdminAnalytics {
  total_students: number;
  total_revenue: string;
  mom_student_growth: number | null;
  total_questions_answered: number;
  top_systems_by_attempts: SystemAttemptRow[];
  avg_quiz_score: number | null;
  completion_rate: number;
  weakest_systems: WeakSystemRow[];
  revenue_series: RevenueSeries;
  subscription_mix: SubscriptionMix;
}

export const ANALYTICS_TILE_LABELS = {
  totalStudents: "Total students",
  totalRevenue: "Total revenue",
  momGrowth: "Growth vs. last month",
  questionsAnswered: "Questions answered",
  avgQuizScore: "Average quiz score",
  completionRate: "Quiz completion rate",
} as const;

export const SAMPLE_DATA_BADGE_LABEL = "Sample data — live revenue will appear once subscriptions are active";

/**
 * Brand-neutral categorical palette for the two sample charts and the
 * top-systems bar chart. Kept small and local to this page rather than a
 * shared design-system export, since no other page in the app charts
 * anything yet.
 */
export const CHART_COLORS = ["#4338ca", "#d97706", "#16a34a", "#0ea5e9", "#dc2626"];
