import { Check, X } from "lucide-react";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import type { AnswerChoice } from "@/types/question";

export function SATAChoiceList({
  choices,
  selectedIds,
  submitted,
  onToggle,
  label = "Select all that apply",
}: {
  choices: AnswerChoice[];
  selectedIds: string[];
  submitted: boolean;
  onToggle: (choiceId: string) => void;
  /** Overridable so EMRChoiceList (identical interaction, different instruction copy) can reuse this without duplicating the markup. */
  label?: string;
}) {
  return (
    <div className="choices">
      <p className="sata-label">{label}</p>
      {[...choices]
        .sort((a, b) => a.display_order - b.display_order)
        .map((choice) => {
          const isSelected = selectedIds.includes(choice.id);
          const isCorrect = submitted && choice.is_correct;
          const isWrongPick = submitted && isSelected && !choice.is_correct;
          return (
            <Label
              key={choice.id}
              htmlFor={choice.id}
              className={cn("choice stacked", !submitted && isSelected && "selected", isCorrect && "correct", isWrongPick && "incorrect")}
            >
              <div className="choice-row">
                <Checkbox id={choice.id} checked={isSelected} onCheckedChange={() => onToggle(choice.id)} disabled={submitted} />
                <span style={{ flex: 1 }}>{choice.choice_text}</span>
                {isCorrect && (
                  <span className="mk ok">
                    <Check className="h-3 w-3" />
                  </span>
                )}
                {isWrongPick && (
                  <span className="mk no">
                    <X className="h-3 w-3" />
                  </span>
                )}
              </div>
              {submitted && choice.rationale && <p className="choice-rationale">{choice.rationale}</p>}
            </Label>
          );
        })}
    </div>
  );
}
