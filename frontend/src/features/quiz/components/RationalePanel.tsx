import { Lightbulb } from "lucide-react";

import type { Question } from "@/types/question";

/**
 * Always shows both halves of the rationale — why the correct answer is
 * correct, and why the other options aren't — regardless of whether the
 * student answered right or wrong. Previously rationale_incorrect only
 * appeared on a wrong answer, so a student who answered correctly never
 * saw why the distractors were wrong; the client asked for both to show
 * every time.
 */
export function RationalePanel({ question }: { question: Question }) {
  return (
    <div className="rounded-xl border border-secondary bg-secondary/30 p-5">
      <div className="flex items-center gap-2">
        <Lightbulb className="h-4 w-4 text-primary" />
        <h3 className="font-serif text-lg font-medium text-foreground">Rationale</h3>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-foreground/90">{question.rationale_correct}</p>
      {question.rationale_incorrect && (
        <div className="mt-3 border-t border-secondary pt-3">
          <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Why the other options are incorrect
          </p>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{question.rationale_incorrect}</p>
        </div>
      )}
    </div>
  );
}
