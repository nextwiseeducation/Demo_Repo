import { Flag } from "lucide-react";

import type { AnswerState } from "@/features/quiz/quizSessionReducer";
import { cn } from "@/lib/utils";
import type { Question } from "@/types/question";

interface QuestionNavigatorProps {
  questions: Question[];
  currentIndex: number;
  answers: Record<string, AnswerState>;
  /** Questions the student has been shown (answered or not) — see QuizSessionState.visitedIds. */
  visitedIds: Set<string>;
  markedIds: Set<string>;
  onJump: (index: number) => void;
}

/**
 * UWorld-style question palette: every question in the session as a
 * clickable number, so "easily return to anything I skipped or flagged"
 * doesn't mean clicking Previous/Next repeatedly — a skipped or marked
 * question is directly reachable in one click, with its state visible at a
 * glance before jumping.
 */
export function QuestionNavigator({ questions, currentIndex, answers, visitedIds, markedIds, onJump }: QuestionNavigatorProps) {
  return (
    <div className="q-nav">
      <div className="q-nav-grid">
        {questions.map((q, index) => {
          const answer = answers[q.id];
          const isCurrent = index === currentIndex;
          const isAnswered = answer?.submitted ?? false;
          const isVisited = visitedIds.has(q.id);
          const isMarked = markedIds.has(q.id);
          // "Skipped" means visited, unanswered, and NOT the one currently
          // on screen — the question being actively viewed hasn't been
          // skipped yet, it just hasn't been answered yet. Without
          // excluding isCurrent here, the current question (always in
          // visitedIds — see quizSessionReducer's createInitialState/GOTO)
          // would carry both "current" and "skipped" classes at once, and
          // since they share CSS specificity, source order made the
          // skipped (amber) style win over current (blue) every time.
          const isSkipped = !isAnswered && isVisited && !isCurrent;
          const statusLabel = isAnswered
            ? answer?.isCorrect
              ? "answered correctly"
              : "answered incorrectly"
            : isSkipped
              ? "skipped"
              : "not yet viewed";

          return (
            <button
              key={q.id}
              type="button"
              className={cn(
                "q-nav-item",
                isCurrent && "current",
                isAnswered && (answer?.isCorrect ? "correct" : "incorrect"),
                isSkipped && "skipped",
              )}
              onClick={() => onJump(index)}
              aria-current={isCurrent ? "true" : undefined}
              aria-label={`Question ${index + 1}, ${statusLabel}${isMarked ? ", marked for review" : ""}`}
            >
              {index + 1}
              {isMarked && <Flag className="q-nav-flag" aria-hidden="true" />}
            </button>
          );
        })}
      </div>
      <div className="q-nav-legend">
        <LegendItem className="current" label="Current" />
        <LegendItem className="correct" label="Correct" />
        <LegendItem className="incorrect" label="Incorrect" />
        <LegendItem className="skipped" label="Skipped" />
        <span className="q-nav-legend-item">
          <Flag className="q-nav-flag" aria-hidden="true" />
          Marked
        </span>
      </div>
    </div>
  );
}

function LegendItem({ className, label }: { className: string; label: string }) {
  return (
    <span className="q-nav-legend-item">
      <i className={cn("q-nav-dot", className)} />
      {label}
    </span>
  );
}
