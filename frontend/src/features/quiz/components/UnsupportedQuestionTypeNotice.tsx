import { Construction } from "lucide-react";

import { Button } from "@/components/ui/button";
import { QUESTION_TYPE_LABELS, type QuestionType } from "@/types/question";

export function UnsupportedQuestionTypeNotice({ questionType, onSkip }: { questionType: QuestionType; onSkip: () => void }) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-border bg-muted/40 p-10 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
        <Construction className="h-5 w-5" />
      </span>
      <div>
        <h3 className="font-display text-base font-medium text-foreground">
          {QUESTION_TYPE_LABELS[questionType]}: coming soon
        </h3>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          This question type is part of the full NGN schema but isn't interactive in this preview yet.
        </p>
      </div>
      <Button variant="outline" onClick={onSkip}>
        Skip to next question
      </Button>
    </div>
  );
}
