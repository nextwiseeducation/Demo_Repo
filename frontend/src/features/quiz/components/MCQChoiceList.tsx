import { Check, X } from "lucide-react";

import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { cn } from "@/lib/utils";
import type { AnswerChoice } from "@/types/question";

export function MCQChoiceList({
  choices,
  selectedId,
  submitted,
  onSelect,
}: {
  choices: AnswerChoice[];
  selectedId: string | null;
  submitted: boolean;
  onSelect: (choiceId: string) => void;
}) {
  return (
    <RadioGroup value={selectedId ?? ""} onValueChange={(value) => onSelect(String(value))} className="choices">
      {[...choices]
        .sort((a, b) => a.display_order - b.display_order)
        .map((choice) => {
          const isSelected = choice.id === selectedId;
          const isCorrect = submitted && choice.is_correct;
          const isWrongPick = submitted && isSelected && !choice.is_correct;
          return (
            <Label
              key={choice.id}
              htmlFor={choice.id}
              className={cn("choice stacked", !submitted && isSelected && "selected", isCorrect && "correct", isWrongPick && "incorrect")}
            >
              <div className="choice-row">
                <RadioGroupItem id={choice.id} value={choice.id} disabled={submitted} />
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
    </RadioGroup>
  );
}
