import type { ReactNode } from "react";

import { ReportIssueDialog } from "@/features/quiz/components/ReportIssueDialog";
import { DIFFICULTY_LABELS, QUESTION_TYPE_LABELS, type Question } from "@/types/question";

export function QuestionCard({
  question,
  questionNumber,
  showReportButton = true,
  children,
}: {
  question: Question;
  /** Position within the current quiz (1-based) — shown on the issue report so students never have to remember it themselves. */
  questionNumber?: number;
  /** False for decorative/non-interactive usages (e.g. the landing page's hero mockup) — there's no real quiz to report an issue against there. */
  showReportButton?: boolean;
  children?: ReactNode;
}) {
  return (
    <div className="q-card">
      <div className="q-card-inner">
        <div className="badge-row">
          <span className="badge badge-outline">{question.nursing_system}</span>
          <span className="badge badge-outline">{question.topic}</span>
          <span className="badge badge-secondary">{DIFFICULTY_LABELS[question.difficulty]}</span>
          <span className="badge badge-tint">{QUESTION_TYPE_LABELS[question.question_type]}</span>
        </div>

        {question.clinical_scenario && <div className="scenario">{question.clinical_scenario}</div>}

        <p className="stem">{question.stem}</p>

        {children}

        {showReportButton && (
          <div className="report-row">
            <ReportIssueDialog questionStem={question.stem} questionNumber={questionNumber} />
          </div>
        )}
      </div>
    </div>
  );
}
