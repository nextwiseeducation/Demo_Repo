import { SATAChoiceList } from "@/features/quiz/components/SATAChoiceList";
import type { AnswerChoice } from "@/types/question";

/**
 * Extended Multiple Response: same AnswerChoice model, same multi-select
 * interaction and exact-set grading as SATA (see Question.rationale's own
 * "MCQ, SATA, and EMR" comment on the backend) — EMR items are typically
 * longer option lists, which is why NCLEX gives them a distinct label, but
 * there's no structural difference to render.
 */
export function EMRChoiceList(props: {
  choices: AnswerChoice[];
  selectedIds: string[];
  submitted: boolean;
  onToggle: (choiceId: string) => void;
}) {
  return <SATAChoiceList {...props} label="Select all findings that apply" />;
}
