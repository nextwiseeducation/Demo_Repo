import { AnswerChoiceBuilder } from "@/features/admin/components/builders/AnswerChoiceBuilder";
import { BowTieBuilder } from "@/features/admin/components/builders/BowTieBuilder";
import { ClozeBuilder } from "@/features/admin/components/builders/ClozeBuilder";
import { DragDropBuilder } from "@/features/admin/components/builders/DragDropBuilder";
import { HotSpotBuilder } from "@/features/admin/components/builders/HotSpotBuilder";
import { MatrixBuilder } from "@/features/admin/components/builders/MatrixBuilder";
import type { QuestionDraft } from "@/types/admin";
import type { QuestionType } from "@/types/question";

interface StructureBuilderProps {
  draft: QuestionDraft;
  onChange: (patch: Partial<QuestionDraft>) => void;
}

/** Resolves NGN_CASE to its ngn_type — the effective type decides which structural builder renders, same rule the backend uses (effective_question_type). */
export function effectiveType(draft: QuestionDraft): QuestionType | null {
  if (draft.question_type === "NGN_CASE") return draft.ngn_type ?? null;
  return draft.question_type;
}

/** Dispatches to the right structural builder for the question's effective type. */
export function StructureBuilder({ draft, onChange }: StructureBuilderProps) {
  const type = effectiveType(draft);

  switch (type) {
    case "MCQ":
    case "SATA":
    case "EMR":
      return (
        <AnswerChoiceBuilder
          questionType={type}
          choices={draft.answer_choices ?? []}
          onChange={(answer_choices) => onChange({ answer_choices })}
        />
      );
    case "MATRIX":
      return (
        <MatrixBuilder
          columns={draft.matrix_columns ?? []}
          rows={draft.matrix_rows ?? []}
          onColumnsChange={(matrix_columns) => onChange({ matrix_columns })}
          onRowsChange={(matrix_rows) => onChange({ matrix_rows })}
        />
      );
    case "BOWTIE":
      return (
        <BowTieBuilder options={draft.bowtie_options ?? []} onChange={(bowtie_options) => onChange({ bowtie_options })} />
      );
    case "CLOZE":
      return (
        <ClozeBuilder
          stem={draft.stem}
          blanks={draft.cloze_blanks ?? []}
          onChange={(cloze_blanks) => onChange({ cloze_blanks })}
        />
      );
    case "DRAG_DROP":
      return (
        <DragDropBuilder
          categories={draft.dragdrop_categories ?? []}
          items={draft.dragdrop_items ?? []}
          onCategoriesChange={(dragdrop_categories) => onChange({ dragdrop_categories })}
          onItemsChange={(dragdrop_items) => onChange({ dragdrop_items })}
        />
      );
    case "HOTSPOT":
      return (
        <HotSpotBuilder
          stem={draft.stem}
          targets={draft.hotspot_targets ?? []}
          onChange={(hotspot_targets) => onChange({ hotspot_targets })}
        />
      );
    default:
      return (
        <p className="text-sm text-muted-foreground">
          {draft.question_type === "NGN_CASE"
            ? "Choose which item type this case question renders as above."
            : "Select a question type to build its answer structure."}
        </p>
      );
  }
}
