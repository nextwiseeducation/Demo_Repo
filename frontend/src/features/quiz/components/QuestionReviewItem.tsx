import { Lightbulb } from "lucide-react";

import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { ReportIssueDialog } from "@/features/quiz/components/ReportIssueDialog";
import { effectiveQuestionType, DIFFICULTY_LABELS, type Question } from "@/types/question";
import type { QuestionResponse } from "@/types/quiz";

/**
 * "Your answer" / "Why?" text for the 5 NGN structural types, whose review
 * data doesn't fit the answer_choices shape the rest of this file assumes.
 * Reads only the post-submit revealed fields (matrix_cells, bowtie_options,
 * cloze_blanks, dragdrop_items, hotspot_targets), which SUBMIT_RESULT
 * already merges onto `question` the same way it does for answer_choices —
 * every response on this page has already gone through that.
 */
function structuredSummary(question: Question, response: QuestionResponse): { yourAnswer: string; correctAnswer: string; why: { label: string; rationale?: string; isCorrect: boolean }[] } {
  const sa = response.structured_answer;
  const type = effectiveQuestionType(question);

  if (type === "MATRIX") {
    const selections = sa?.kind === "MATRIX" ? sa.selections : [];
    const colName = (id: number) => question.matrix_columns.find((c) => c.id === id)?.text ?? "?";
    const yourAnswer = question.matrix_rows
      .map((row) => {
        const picked = selections.find((s) => s.row_id === row.id);
        return `${row.text}: ${picked ? colName(picked.column_id) : "—"}`;
      })
      .join("; ");
    const correctAnswer = question.matrix_rows
      .map((row) => {
        const correctCell = question.matrix_cells?.find((c) => c.row_id === row.id && c.is_correct);
        return `${row.text}: ${correctCell ? colName(correctCell.column_id) : "?"}`;
      })
      .join("; ");
    const why = (question.matrix_cells ?? [])
      .filter((c) => c.rationale)
      .map((c) => ({
        label: `${question.matrix_rows.find((r) => r.id === c.row_id)?.text ?? ""} — ${colName(c.column_id)}`,
        rationale: c.rationale,
        isCorrect: c.is_correct,
      }));
    return { yourAnswer, correctAnswer, why };
  }

  if (type === "BOWTIE") {
    const selectedIds = sa?.kind === "BOWTIE" ? sa.selectedOptionIds : [];
    const yourAnswer = question.bowtie_options
      .filter((o) => selectedIds.includes(o.id))
      .map((o) => o.option_text)
      .join("; ") || "No answer selected";
    const correctAnswer = question.bowtie_options
      .filter((o) => o.is_correct)
      .map((o) => o.option_text)
      .join("; ");
    const why = question.bowtie_options
      .filter((o) => o.rationale)
      .map((o) => ({ label: o.option_text, rationale: o.rationale, isCorrect: o.is_correct ?? false }));
    return { yourAnswer, correctAnswer, why };
  }

  if (type === "CLOZE") {
    const selections = sa?.kind === "CLOZE" ? sa.selections : [];
    const optionText = (blankOptions: { id: number; option_text: string }[], id?: number) =>
      blankOptions.find((o) => o.id === id)?.option_text ?? "—";
    const yourAnswer = question.cloze_blanks
      .map((blank) => optionText(blank.options, selections.find((s) => s.blank_id === blank.id)?.option_id))
      .join("; ");
    const correctAnswer = question.cloze_blanks
      .map((blank) => blank.options.find((o) => o.is_correct)?.option_text ?? "?")
      .join("; ");
    const why = question.cloze_blanks.flatMap((blank) =>
      blank.options
        .filter((o) => o.rationale)
        .map((o) => ({ label: `${blank.blank_key}: ${o.option_text}`, rationale: o.rationale, isCorrect: o.is_correct ?? false })),
    );
    return { yourAnswer, correctAnswer, why };
  }

  if (type === "DRAG_DROP") {
    const isSequence = question.dragdrop_categories.length === 0;
    if (isSequence) {
      const placements = sa?.kind === "DRAG_DROP" ? sa.placements : [];
      const orderById = new Map(placements.map((p) => [p.item_id, p.order]));
      const yourOrdered = [...question.dragdrop_items].sort((a, b) => (orderById.get(a.id) ?? 0) - (orderById.get(b.id) ?? 0));
      const correctOrdered = [...question.dragdrop_items].sort((a, b) => (a.correct_order ?? 0) - (b.correct_order ?? 0));
      return {
        yourAnswer: yourOrdered.map((i) => i.text).join(" → "),
        correctAnswer: correctOrdered.map((i) => i.text).join(" → "),
        why: question.dragdrop_items.filter((i) => i.rationale).map((i) => ({ label: i.text, rationale: i.rationale, isCorrect: true })),
      };
    }
    const placements = sa?.kind === "DRAG_DROP" ? sa.placements : [];
    const categoryName = (id: number | null) => question.dragdrop_categories.find((c) => c.id === id)?.name ?? "Unplaced";
    const yourAnswer = question.dragdrop_items
      .map((item) => `${item.text}: ${categoryName(placements.find((p) => p.item_id === item.id)?.category_id ?? null)}`)
      .join("; ");
    const correctAnswer = question.dragdrop_items.map((item) => `${item.text}: ${categoryName(item.correct_category_id ?? null)}`).join("; ");
    const why = question.dragdrop_items
      .filter((i) => i.rationale)
      .map((i) => ({ label: i.text, rationale: i.rationale, isCorrect: true }));
    return { yourAnswer, correctAnswer, why };
  }

  // HOTSPOT
  const selectedIds = sa?.kind === "HOTSPOT" ? sa.selectedTargetIds : [];
  const yourAnswer = question.hotspot_targets
    .filter((t) => selectedIds.includes(t.id))
    .map((t) => t.target_text)
    .join("; ") || "No answer selected";
  const correctAnswer = question.hotspot_targets
    .filter((t) => t.is_correct)
    .map((t) => t.target_text)
    .join("; ");
  const why = question.hotspot_targets
    .filter((t) => t.rationale)
    .map((t) => ({ label: t.target_text, rationale: t.rationale, isCorrect: t.is_correct ?? false }));
  return { yourAnswer, correctAnswer, why };
}

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
  const isChoiceBased = effectiveQuestionType(question) === "MCQ" || effectiveQuestionType(question) === "SATA" || effectiveQuestionType(question) === "EMR";
  const selectedChoices = question.answer_choices.filter((c) => response.selected_choice_ids.includes(c.id));
  const correctChoices = question.answer_choices.filter((c) => c.is_correct);
  const structured = isChoiceBased ? null : structuredSummary(question, response);

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
              {structured
                ? structured.yourAnswer
                : selectedChoices.length > 0
                  ? selectedChoices.map((c) => c.choice_text).join("; ")
                  : "No answer selected"}
            </span>
          </p>
          {!response.is_correct && (
            <p>
              <span className="font-medium text-foreground">Correct answer: </span>
              <span className="text-success">
                {structured ? structured.correctAnswer : correctChoices.map((c) => c.choice_text).join("; ")}
              </span>
            </p>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-medium text-foreground">Why?</h3>
          <ul className="flex flex-col gap-2.5 text-sm">
            {structured
              ? structured.why.map((row, index) => (
                  <li key={index} className="flex flex-col gap-1">
                    <span className={row.isCorrect ? "font-medium text-success" : "font-medium text-destructive"}>{row.label}</span>
                    {row.rationale && <span className="text-muted-foreground">{row.rationale}</span>}
                  </li>
                ))
              : question.answer_choices.map((choice) => {
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
