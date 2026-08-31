import { Link } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/constants";

interface QuizResultsSummaryProps {
  correctCount: number;
  totalCount: number;
  /** Undefined for a link built before totalTimeSeconds was forwarded — the row is simply omitted. */
  totalTimeSeconds?: number;
  /** Computed by QuizResultsPage from the actual questions in this quiz — see its own comment for how. */
  topicLabel: string;
  incorrectCount: number;
  onReviewIncorrect: () => void;
}

/** "125" -> "2:05" */
function formatDuration(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

/**
 * Prominent, above-the-fold summary + next-step actions — this is the
 * "immediately know what to do next" block the redesign exists for, so it
 * sits at the top of the results page rather than at the bottom as a
 * relabeled action bar.
 */
export function QuizResultsSummary({
  correctCount,
  totalCount,
  totalTimeSeconds,
  topicLabel,
  incorrectCount,
  onReviewIncorrect,
}: QuizResultsSummaryProps) {
  const percent = totalCount > 0 ? Math.round((correctCount / totalCount) * 100) : 0;

  return (
    <Card>
      <CardContent className="flex flex-col gap-6 py-6">
        <div className="flex flex-col items-center gap-1 text-center">
          <p className="font-display text-4xl font-semibold text-foreground">
            {correctCount}/{totalCount}
          </p>
          <p className="text-sm text-muted-foreground">{percent}% correct</p>
        </div>

        <dl className="grid grid-cols-2 gap-4 border-y border-border py-4 sm:grid-cols-4">
          <SummaryStat label="Correct" value={String(correctCount)} valueClassName="text-success" />
          <SummaryStat label="Incorrect" value={String(incorrectCount)} valueClassName="text-destructive" />
          <SummaryStat label="Accuracy" value={`${percent}%`} />
          {totalTimeSeconds !== undefined ? (
            <SummaryStat label="Time" value={formatDuration(totalTimeSeconds)} />
          ) : (
            <SummaryStat label="Topic" value={topicLabel} />
          )}
        </dl>

        {totalTimeSeconds !== undefined && (
          <p className="-mt-3 text-center text-xs text-muted-foreground">Topic: {topicLabel}</p>
        )}

        <div className="flex flex-col gap-2 sm:flex-row">
          <Button
            className="flex-1"
            disabled={incorrectCount === 0}
            onClick={onReviewIncorrect}
          >
            Review Incorrect Answers
          </Button>
          <Button variant="outline" className="flex-1" render={<Link to={ROUTES.quizSetup}>Practice Again</Link>} />
          <Button variant="outline" className="flex-1" render={<Link to={ROUTES.dashboard}>Back to Dashboard</Link>} />
        </div>
      </CardContent>
    </Card>
  );
}

function SummaryStat({
  label,
  value,
  valueClassName = "text-foreground",
}: {
  label: string;
  value: string;
  valueClassName?: string;
}) {
  return (
    <div className="flex flex-col items-center gap-0.5 text-center">
      <dt className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{label}</dt>
      <dd className={`font-display text-lg font-semibold ${valueClassName}`}>{value}</dd>
    </div>
  );
}
