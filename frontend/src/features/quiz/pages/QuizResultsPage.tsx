import { CheckCircle2, Info, MessageSquareText, XCircle } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { QuizFeedbackModal } from "@/features/quiz/components/QuizFeedbackModal";
import { RationalePanel } from "@/features/quiz/components/RationalePanel";
import { ReportIssueDialog } from "@/features/quiz/components/ReportIssueDialog";
import { ROUTES } from "@/lib/constants";
import type { Question } from "@/types/question";
import type { QuestionResponse } from "@/types/quiz";

interface LocationState {
  questions: Question[];
  responses: QuestionResponse[];
}

export function QuizResultsPage() {
  const location = useLocation();
  const state = location.state as LocationState | null;
  // Opens automatically as soon as the results page is reached — this IS
  // the "end of quiz" moment the survey is meant to appear at.
  const [feedbackOpen, setFeedbackOpen] = useState(true);

  if (!state?.responses?.length) {
    return <Navigate to={ROUTES.quizSetup} replace />;
  }

  const { questions, responses } = state;
  const correctCount = responses.filter((r) => r.is_correct).length;
  const percent = Math.round((correctCount / responses.length) * 100);

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <QuizFeedbackModal open={feedbackOpen} onOpenChange={setFeedbackOpen} questionCount={responses.length} />

      <div className="rounded-xl border border-accent/30 bg-accent/10 px-4 py-3 text-sm text-foreground/90">
        <div className="flex items-start gap-2">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
          <p>This is a practice summary from sample questions — it isn't saved to your account.</p>
        </div>
      </div>

      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-8 text-center">
          <p className="font-display text-4xl font-semibold text-foreground">
            {correctCount}/{responses.length}
          </p>
          <p className="text-sm text-muted-foreground">{percent}% correct</p>
          {!feedbackOpen && (
            <Button variant="outline" size="sm" className="gap-1.5" onClick={() => setFeedbackOpen(true)}>
              <MessageSquareText className="h-3.5 w-3.5" />
              Give feedback
            </Button>
          )}
        </CardContent>
      </Card>

      <div className="flex flex-col gap-2">
        <h2 className="font-display text-lg font-medium text-foreground">Review</h2>
        <Accordion className="flex flex-col gap-2">
          {questions.map((question, index) => {
            const response = responses[index];
            return (
              <AccordionItem key={question.id} value={question.id} className="rounded-xl border border-border bg-card px-4">
                <AccordionTrigger className="gap-3 py-3 text-left hover:no-underline">
                  <div className="flex flex-1 items-center gap-3">
                    {response.is_correct ? (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-success" />
                    ) : (
                      <XCircle className="h-4 w-4 shrink-0 text-destructive" />
                    )}
                    <span className="line-clamp-1 text-sm font-medium text-foreground">{question.stem}</span>
                    <Badge variant="outline" className="ml-auto shrink-0">
                      Q{index + 1}
                    </Badge>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="flex flex-col gap-3 pb-4">
                  <ul className="flex flex-col gap-1.5 text-sm">
                    {question.answer_choices.map((choice) => {
                      const wasSelected = response.selected_choice_ids.includes(choice.id);
                      return (
                        <li
                          key={choice.id}
                          className={
                            choice.is_correct
                              ? "font-medium text-success"
                              : wasSelected
                                ? "font-medium text-destructive"
                                : "text-muted-foreground"
                          }
                        >
                          {choice.choice_text}
                          {wasSelected && !choice.is_correct && " (your answer)"}
                        </li>
                      );
                    })}
                  </ul>
                  <RationalePanel question={question} />
                  <div className="flex w-full justify-end">
                    <ReportIssueDialog questionStem={question.stem} questionNumber={index + 1} />
                  </div>
                </AccordionContent>
              </AccordionItem>
            );
          })}
        </Accordion>
      </div>

      <div className="flex gap-2">
        <Button variant="outline" render={<Link to={ROUTES.quizSetup}>Start another practice quiz</Link>} className="flex-1" />
        <Button render={<Link to={ROUTES.dashboard}>Back to dashboard</Link>} className="flex-1" />
      </div>
    </div>
  );
}
