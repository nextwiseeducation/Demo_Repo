import { Info } from "lucide-react";
import { useMemo, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { Accordion } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { QuestionReviewItem } from "@/features/quiz/components/QuestionReviewItem";
import { QuizFeedbackModal } from "@/features/quiz/components/QuizFeedbackModal";
import { QuizResultsSummary } from "@/features/quiz/components/QuizResultsSummary";
import { ROUTES } from "@/lib/constants";
import type { Question } from "@/types/question";
import type { QuestionResponse, QuizFilterConfig } from "@/types/quiz";

interface LocationState {
  questions: Question[];
  responses: QuestionResponse[];
  /** Absent for a link built before this was forwarded (e.g. an old bookmark) — everything below degrades gracefully. */
  filterConfig?: QuizFilterConfig;
  /** Absent for a link built before this was forwarded — the summary just omits the time stat. */
  totalTimeSeconds?: number;
}

type ReviewFilter = "all" | "incorrect";

export function QuizResultsPage() {
  const location = useLocation();
  const state = location.state as LocationState | null;
  // Opens automatically as soon as the results page is reached — this IS
  // the "end of quiz" moment the survey is meant to appear at.
  const [feedbackOpen, setFeedbackOpen] = useState(true);
  const [reviewFilter, setReviewFilter] = useState<ReviewFilter>("all");
  // Controlled accordion so "Review Incorrect Answers" can auto-expand every
  // incorrect item at once (default accordion behavior only opens one item
  // at a time).
  const [openItems, setOpenItems] = useState<string[]>([]);

  if (!state?.responses?.length) {
    return <Navigate to={ROUTES.quizSetup} replace />;
  }

  const { questions, responses, filterConfig, totalTimeSeconds } = state;
  const correctCount = responses.filter((r) => r.is_correct).length;
  const incorrectCount = responses.length - correctCount;

  const incorrectQuestionIds = useMemo(
    () => questions.filter((_, index) => !responses[index].is_correct).map((q) => q.id),
    [questions, responses],
  );

  function handleReviewIncorrect() {
    setReviewFilter("incorrect");
    setOpenItems(incorrectQuestionIds);
  }

  function handleShowAll() {
    setReviewFilter("all");
  }

  const visibleIndexes = questions
    .map((_, index) => index)
    .filter((index) => reviewFilter === "all" || !responses[index].is_correct);

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <QuizFeedbackModal open={feedbackOpen} onOpenChange={setFeedbackOpen} questionCount={responses.length} />

      <div className="rounded-xl border border-accent/30 bg-accent/10 px-4 py-3 text-sm text-foreground/90">
        <div className="flex items-start gap-2">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
          <p>This is a practice summary from sample questions. It isn't saved to your account.</p>
        </div>
      </div>

      <QuizResultsSummary
        correctCount={correctCount}
        incorrectCount={incorrectCount}
        totalCount={responses.length}
        totalTimeSeconds={totalTimeSeconds}
        filterConfig={filterConfig}
        onReviewIncorrect={handleReviewIncorrect}
      />

      {!feedbackOpen && (
        <div className="flex justify-center">
          <Button variant="outline" size="sm" onClick={() => setFeedbackOpen(true)}>
            Give feedback
          </Button>
        </div>
      )}

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-lg font-medium text-foreground">
            {reviewFilter === "incorrect" ? "Incorrect Answers" : "Review"}
          </h2>
          {reviewFilter === "incorrect" && (
            <Button variant="ghost" size="sm" onClick={handleShowAll}>
              Show all questions
            </Button>
          )}
        </div>
        <Accordion className="flex flex-col gap-2" value={openItems} onValueChange={setOpenItems} multiple>
          {visibleIndexes.map((index) => (
            <QuestionReviewItem
              key={questions[index].id}
              question={questions[index]}
              questionNumber={index + 1}
              response={responses[index]}
            />
          ))}
        </Accordion>
      </div>
    </div>
  );
}
