import { Construction, FileWarning } from "lucide-react";

import { Button } from "@/components/ui/button";
import { QUESTION_TYPE_LABELS, type QuestionType } from "@/types/question";

export function UnsupportedQuestionTypeNotice({
  questionType,
  onSkip,
  reason = "TYPE_NOT_SUPPORTED",
}: {
  questionType: QuestionType;
  onSkip: () => void;
  /**
   * TYPE_NOT_SUPPORTED: this question_type genuinely has no renderer yet.
   * MISSING_CONTENT: the type IS supported, but this specific question has
   * no answer data to render (e.g. an NGN Case Study item whose options
   * were authored as inline text rather than structured choices — see
   * import_ngn_item_bank.py's own "KNOWN LIMITATION" docstring). Distinct
   * copy so this reads as a content gap, not a missing feature.
   */
  reason?: "TYPE_NOT_SUPPORTED" | "MISSING_CONTENT";
}) {
  const isMissingContent = reason === "MISSING_CONTENT";
  return (
    <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-border bg-muted/40 p-10 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
        {isMissingContent ? <FileWarning className="h-5 w-5" /> : <Construction className="h-5 w-5" />}
      </span>
      <div>
        <h3 className="font-display text-base font-medium text-foreground">
          {isMissingContent ? "This question isn't ready yet" : `${QUESTION_TYPE_LABELS[questionType]}: coming soon`}
        </h3>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          {isMissingContent
            ? "Its answer options haven't been added to the question bank yet, so it can't be graded."
            : "This question type is part of the full NGN schema but isn't interactive in this preview yet."}
        </p>
      </div>
      <Button variant="outline" onClick={onSkip}>
        Skip to next question
      </Button>
    </div>
  );
}
