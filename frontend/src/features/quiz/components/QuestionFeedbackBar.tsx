import type { ReactNode } from "react";

import { BarChart3, Calendar, CheckCircle2, Clock, XCircle } from "lucide-react";

interface QuestionFeedbackBarProps {
  isCorrect: boolean;
  /** 0-100, running accuracy across every question submitted so far this session (including this one). */
  accuracyPercent: number;
  /** Seconds spent on this specific question, from first render to submit — not the whole-quiz timer. */
  timeSpentSeconds: number;
  /** ISO 8601 datetime — when this question's content was last edited by the authoring team. */
  updatedAt: string;
}

/**
 * One-row info strip shown immediately after a student submits an answer.
 * Mirrors QuestionReviewItem's success/destructive color tokens so the
 * "correct/incorrect" language stays visually consistent between the live
 * quiz and the results review. Scoped to exactly the 4 stats the client
 * asked for — no exhibit button, no extra chrome.
 */
export function QuestionFeedbackBar({
  isCorrect,
  accuracyPercent,
  timeSpentSeconds,
  updatedAt,
}: QuestionFeedbackBarProps) {
  const lastUpdatedLabel = new Date(updatedAt).toLocaleDateString();

  return (
    <div
      className={`flex flex-wrap items-center gap-x-8 gap-y-3 rounded-lg border-l-4 bg-card px-4 py-3 ring-1 ring-foreground/10 ${
        isCorrect ? "border-l-success" : "border-l-destructive"
      }`}
    >
      <div className={`flex items-center gap-2 ${isCorrect ? "text-success" : "text-destructive"}`}>
        {isCorrect ? <CheckCircle2 className="h-5 w-5 shrink-0" /> : <XCircle className="h-5 w-5 shrink-0" />}
        <span className="text-sm font-semibold">{isCorrect ? "Correct" : "Incorrect"}</span>
      </div>

      <div className="flex flex-1 flex-wrap items-center gap-x-8 gap-y-3">
        <Stat icon={<BarChart3 className="h-4 w-4" />} label="Accuracy so far" value={`${accuracyPercent}%`} />
        <Stat icon={<Clock className="h-4 w-4" />} label="Time on question" value={`${timeSpentSeconds}s`} />
        <Stat icon={<Calendar className="h-4 w-4" />} label="Content updated" value={lastUpdatedLabel} />
      </div>
    </div>
  );
}

function Stat({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-muted-foreground">{icon}</span>
      <div className="flex flex-col leading-tight">
        <span className="text-sm font-medium text-foreground">{value}</span>
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
    </div>
  );
}
