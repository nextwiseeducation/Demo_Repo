import { Badge } from "@/components/ui/badge";
import { SAMPLE_DATA_BADGE_LABEL } from "@/types/analytics";

/**
 * Driven off the `is_sample` flag the analytics API returns per chart, not
 * a frontend constant — the badge disappears on its own the moment the
 * backend starts returning real Stripe-backed data, with no frontend
 * change required. See the "STRIPE SWAP POINT" comments in
 * apps/admin_api/services/analytics.py.
 */
export function SampleDataBadge() {
  return (
    <Badge
      variant="outline"
      className="h-auto max-w-[160px] border-accent/40 bg-accent/10 py-1 text-right text-[10px] leading-tight whitespace-normal text-foreground"
    >
      {SAMPLE_DATA_BADGE_LABEL}
    </Badge>
  );
}
