import type { ReactNode } from "react";

import { ReportIssueDialog } from "@/features/quiz/components/ReportIssueDialog";
import { DIFFICULTY_LABELS, QUESTION_TYPE_LABELS, type Question } from "@/types/question";

export function QuestionCard({
  question,
  questionNumber,
  showReportButton = true,
  hideStem = false,
  hideScenario = false,
  children,
}: {
  question: Question;
  /** Position within the current quiz (1-based) — shown on the issue report so students never have to remember it themselves. */
  questionNumber?: number;
  /** False for decorative/non-interactive usages (e.g. the landing page's hero mockup) — there's no real quiz to report an issue against there. */
  showReportButton?: boolean;
  /** True for Drop-down Cloze and Enhanced Hot Spot — both render their own version of the stem (with inline dropdowns / clickable spans) inside `children`, so the plain, non-interactive copy below would otherwise duplicate it. */
  hideStem?: boolean;
  /** True only for Enhanced Hot Spot — HotSpotQuestion renders its own clickable scenario (a target's text can fall inside it, not just the stem), so the plain copy below would duplicate it. Cloze doesn't touch the scenario, so it keeps this shown. */
  hideScenario?: boolean;
  children?: ReactNode;
}) {
  const scenario = question.case_study?.shared_scenario ?? question.clinical_scenario;
  return (
    <div className="q-card">
      <div className="q-card-inner">
        {question.case_study && (
          <div className="case-study-tag">
            {question.case_study.title}
            {question.case_study_sequence != null && <span> · Item {question.case_study_sequence}</span>}
          </div>
        )}

        <div className="badge-row">
          <span className="badge badge-outline">{question.nursing_system}</span>
          <span className="badge badge-outline">{question.topic}</span>
          <span className="badge badge-secondary">{DIFFICULTY_LABELS[question.difficulty]}</span>
          <span className="badge badge-tint">{QUESTION_TYPE_LABELS[question.question_type]}</span>
        </div>

        {!hideScenario && scenario && <div className="scenario">{scenario}</div>}
        {!hideStem && (
          <>
            {question.image && (
              <img src={question.image} alt="" className="question-image" />
            )}
            <p className="stem">{question.stem}</p>
          </>
        )}

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
