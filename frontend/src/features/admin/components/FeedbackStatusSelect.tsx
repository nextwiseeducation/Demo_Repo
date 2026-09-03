import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useUpdateFeedbackStatus } from "@/features/admin/hooks/useAdminFeedback";
import {
  FEEDBACK_STATUS_BADGE_CLASS,
  FEEDBACK_STATUS_LABELS,
  REPORT_STATUS_BADGE_CLASS,
  REPORT_STATUS_LABELS,
  type FeedbackKind,
  type FeedbackStatus,
  type ReportStatus,
} from "@/types/admin";

interface FeedbackStatusSelectProps {
  kind: FeedbackKind;
  id: string;
  status: FeedbackStatus | ReportStatus;
}

/** Colour-coded status badge doubling as the change control — selecting a new value PATCHes immediately, badge updates without a reload. */
export function FeedbackStatusSelect({ kind, id, status }: FeedbackStatusSelectProps) {
  const updateStatus = useUpdateFeedbackStatus();
  // Cast to Record<string, ...>: `status`'s static type is the union
  // FeedbackStatus | ReportStatus, but at runtime it's always paired with
  // the matching `kind`-selected map, so this is a safe widening for
  // indexing purposes.
  const labels = (kind === "survey" ? FEEDBACK_STATUS_LABELS : REPORT_STATUS_LABELS) as Record<string, string>;
  const badgeClasses = (kind === "survey" ? FEEDBACK_STATUS_BADGE_CLASS : REPORT_STATUS_BADGE_CLASS) as Record<
    string,
    string
  >;
  const options = Object.entries(labels) as [FeedbackStatus | ReportStatus, string][];

  return (
    <Select
      value={status}
      onValueChange={(value) => {
        if (!value) return;
        updateStatus.mutate({ kind, id, status: value as FeedbackStatus | ReportStatus });
      }}
    >
      <SelectTrigger className="h-auto w-fit border-none bg-transparent p-0 shadow-none hover:bg-transparent">
        <SelectValue>
          {() => (
            <Badge variant="outline" className={`cursor-pointer ${badgeClasses[status]}`}>
              {labels[status]}
            </Badge>
          )}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {options.map(([value, label]) => (
          <SelectItem key={value} value={value}>
            {label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
