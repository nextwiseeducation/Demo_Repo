import { Lightbulb } from "lucide-react";

import type { Question } from "@/types/question";

export function RationalePanel({ question, wasCorrect }: { question: Question; wasCorrect: boolean }) {
  return (
    <div className="rounded-xl border border-secondary bg-secondary/30 p-5">
      <div className="flex items-center gap-2">
        <Lightbulb className="h-4 w-4 text-primary" />
        <h3 className="font-serif text-lg font-medium text-foreground">Rationale</h3>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-foreground/90">{question.rationale_correct}</p>
      {!wasCorrect && question.rationale_incorrect && (
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{question.rationale_incorrect}</p>
      )}
    </div>
  );
}
