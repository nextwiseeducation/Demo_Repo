import { Lightbulb } from "lucide-react";

import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { ReportIssueDialog } from "@/features/quiz/components/ReportIssueDialog";
import { DIFFICULTY_LABELS, type Question } from "@/types/question";
import type { QuestionResponse } from "@/types/quiz";

interface QuestionReviewItemProps {
  question: Question;
  /** 1-based position within the quiz — shown on the Q-number badge and passed to ReportIssueDialog. */
  questionNumber: number;
  response: QuestionResponse;
}

/** "PRIORITIZE_HYPOTHESES" -> "Prioritize Hypotheses" — clinical_judgment_skill comes back as a raw enum key. */
function formatEnumLabel(value: string): string {
  return value
    .toLowerCase()
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * One row of the results review accordion, extracted so QuizResultsPage can
 * filter/reorder rows without inlining this much JSX per question. Mirrors
 * QuestionCard's metadata-badge pattern (topic/difficulty/etc.) for the
 * expanded content, plus the "your answer vs correct answer" + rationale
 * breakdown specific to a completed attempt.
 */
export function QuestionReviewItem({ question, questionNumber, response }: QuestionReviewItemProps) {
  const selectedChoices = question.answer_choices.filter((c) => response.selected_choice_ids.includes(c.id));
  const correctChoices = question.answer_choices.filter((c) => c.is_correct);

  return (
    <AccordionItem value={question.id} className="rounded-xl border border-border bg-card px-4">
      <AccordionTrigger className="gap-3 py-3 text-left hover:no-underline">
        <div className="flex flex-1 items-center gap-3">
          {response.is_correct ? (
            <Badge variant="outline" className="shrink-0 border-transparent bg-success/10 text-success">
              Correct
            </Badge>
          ) : (
            <Badge variant="destructive" className="shrink-0">
              Incorrect
            </Badge>
          )}
          <span className="line-clamp-1 text-sm font-medium text-foreground">{question.stem}</span>
          <Badge variant="outline" className="ml-auto shrink-0">
            Q{questionNumber}
          </Badge>
        </div>
      </AccordionTrigger>
      <AccordionContent className="flex flex-col gap-4 pb-4">
        <p className="text-sm text-foreground">{question.stem}</p>

        <div className="flex flex-wrap gap-1.5">
          <Badge variant="outline">{question.topic}</Badge>
          <Badge variant="secondary">{DIFFICULTY_LABELS[question.difficulty]}</Badge>
          <Badge variant="outline">{question.nclex_client_needs_category}</Badge>
          <Badge variant="outline">{formatEnumLabel(question.clinical_judgment_skill)}</Badge>
        </div>

        <div className="flex flex-col gap-1.5 text-sm">
          <p>
            <span className="font-medium text-foreground">Your answer: </span>
            <span className={response.is_correct ? "text-success" : "text-destructive"}>
              {selectedChoices.length > 0
                ? selectedChoices.map((c) => c.choice_text).join("; ")
                : "No answer selected"}
            </span>
          </p>
          {!response.is_correct && (
            <p>
              <span className="font-medium text-foreground">Correct answer: </span>
              <span className="text-success">{correctChoices.map((c) => c.choice_text).join("; ")}</span>
            </p>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-medium text-foreground">Why?</h3>
          <ul className="flex flex-col gap-2.5 text-sm">
            {question.answer_choices.map((choice) => {
              const wasSelected = response.selected_choice_ids.includes(choice.id);
              return (
                <li key={choice.id} className="flex flex-col gap-1">
                  <span
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
                  </span>
                  {choice.rationale && <span className="text-muted-foreground">{choice.rationale}</span>}
                </li>
              );
            })}
          </ul>
        </div>

        {question.key_takeaway && (
          <div className="flex gap-2 rounded-lg border border-accent/30 bg-accent/10 p-3 text-sm">
            <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
            <div className="flex flex-col gap-1">
              <p className="font-medium text-foreground">Key Takeaway</p>
              <p className="text-foreground/90">{question.key_takeaway}</p>
            </div>
          </div>
        )}

        <div className="flex w-full justify-end">
          <ReportIssueDialog questionStem={question.stem} questionNumber={questionNumber} />
        </div>
      </AccordionContent>
    </AccordionItem>
  );
}
