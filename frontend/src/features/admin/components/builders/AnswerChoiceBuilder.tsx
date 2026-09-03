import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { OptionRowActions, reorder } from "@/features/admin/components/builders/OptionRowActions";
import { RationaleField } from "@/features/admin/components/builders/RationaleField";
import type { AnswerChoiceDraft } from "@/types/admin";
import type { QuestionType } from "@/types/question";

const MAX_CHOICES = 6;
const MIN_CHOICES = 2;

interface AnswerChoiceBuilderProps {
  questionType: QuestionType;
  choices: AnswerChoiceDraft[];
  onChange: (choices: AnswerChoiceDraft[]) => void;
}

/** MCQ/SATA/EMR — MCQ enforces single-correct via radio buttons; SATA/EMR allow multiple via checkboxes. */
export function AnswerChoiceBuilder({ questionType, choices, onChange }: AnswerChoiceBuilderProps) {
  const isSingleCorrect = questionType === "MCQ";

  function updateChoice(index: number, patch: Partial<AnswerChoiceDraft>) {
    onChange(choices.map((c, i) => (i === index ? { ...c, ...patch } : c)));
  }

  function setCorrect(index: number, isCorrect: boolean) {
    if (isSingleCorrect) {
      onChange(choices.map((c, i) => ({ ...c, is_correct: i === index })));
    } else {
      updateChoice(index, { is_correct: isCorrect });
    }
  }

  function addChoice() {
    onChange([
      ...choices,
      { choice_text: "", is_correct: false, display_order: choices.length, rationale: "" },
    ]);
  }

  function removeChoice(index: number) {
    onChange(
      choices.filter((_, i) => i !== index).map((c, i) => ({ ...c, display_order: i })),
    );
  }

  const radioValue = choices.findIndex((c) => c.is_correct).toString();

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-foreground">Answer choices</span>
        <Button variant="outline" size="sm" onClick={addChoice} disabled={choices.length >= MAX_CHOICES}>
          <Plus className="h-4 w-4" />
          Add choice
        </Button>
      </div>

      {isSingleCorrect ? (
        <RadioGroup
          value={radioValue}
          onValueChange={(value) => setCorrect(Number(value), true)}
          className="flex flex-col gap-3"
        >
          {choices.map((choice, index) => (
            <div key={index} className="flex flex-col gap-2 rounded-lg border border-border p-3">
              <div className="flex items-center gap-2">
                <RadioGroupItem value={index.toString()} aria-label={`Mark choice ${index + 1} correct`} />
                <Input
                  value={choice.choice_text}
                  onChange={(e) => updateChoice(index, { choice_text: e.target.value })}
                  placeholder={`Choice ${index + 1}`}
                  className="flex-1"
                />
                <OptionRowActions
                  onMoveUp={() => onChange(reorder(choices, index, -1))}
                  onMoveDown={() => onChange(reorder(choices, index, 1))}
                  onDelete={() => removeChoice(index)}
                  canMoveUp={index > 0}
                  canMoveDown={index < choices.length - 1}
                />
              </div>
              <RationaleField value={choice.rationale} onChange={(v) => updateChoice(index, { rationale: v })} />
            </div>
          ))}
        </RadioGroup>
      ) : (
        <div className="flex flex-col gap-3">
          {choices.map((choice, index) => (
            <div key={index} className="flex flex-col gap-2 rounded-lg border border-border p-3">
              <div className="flex items-center gap-2">
                <Checkbox
                  checked={choice.is_correct}
                  onCheckedChange={(checked) => setCorrect(index, checked === true)}
                  aria-label={`Mark choice ${index + 1} correct`}
                />
                <Input
                  value={choice.choice_text}
                  onChange={(e) => updateChoice(index, { choice_text: e.target.value })}
                  placeholder={`Choice ${index + 1}`}
                  className="flex-1"
                />
                <OptionRowActions
                  onMoveUp={() => onChange(reorder(choices, index, -1))}
                  onMoveDown={() => onChange(reorder(choices, index, 1))}
                  onDelete={() => removeChoice(index)}
                  canMoveUp={index > 0}
                  canMoveDown={index < choices.length - 1}
                />
              </div>
              <RationaleField value={choice.rationale} onChange={(v) => updateChoice(index, { rationale: v })} />
            </div>
          ))}
        </div>
      )}

      {choices.length < MIN_CHOICES ? (
        <p className="text-xs text-destructive">At least {MIN_CHOICES} choices are required.</p>
      ) : null}
    </div>
  );
}
