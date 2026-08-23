import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
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
    <Card className="border-border/80 shadow-sm">
      <CardHeader className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="outline">{question.nursing_system}</Badge>
          <Badge variant="outline">{question.topic}</Badge>
          <Badge variant="secondary">{DIFFICULTY_LABELS[question.difficulty]}</Badge>
          <Badge className="ml-auto bg-primary/10 text-primary hover:bg-primary/10">
            {QUESTION_TYPE_LABELS[question.question_type]}
          </Badge>
        </div>

        {question.clinical_scenario && (
          <div className="rounded-lg border-l-2 border-accent bg-accent/10 px-4 py-3 text-sm text-foreground/90">
            {question.clinical_scenario}
          </div>
        )}

        <p className="text-base leading-relaxed font-medium text-foreground">{question.stem}</p>

        {showReportButton && (
          <div className="flex w-full justify-end">
            <ReportIssueDialog questionStem={question.stem} questionNumber={questionNumber} />
          </div>
        )}
      </CardHeader>
      {children && <CardContent className="flex flex-col gap-2">{children}</CardContent>}
    </Card>
  );
}
