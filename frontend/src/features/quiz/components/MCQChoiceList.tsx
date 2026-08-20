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
    <RadioGroup value={selectedId ?? ""} onValueChange={(value) => onSelect(String(value))}>
      {[...choices]
        .sort((a, b) => a.display_order - b.display_order)
        .map((choice) => {
          const isSelected = choice.id === selectedId;
          return (
            <Label
              key={choice.id}
              htmlFor={choice.id}
              className={cn(
                "group/field-label flex cursor-pointer items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 text-sm font-normal transition-colors",
                !submitted && isSelected && "border-primary bg-secondary/50",
                !submitted && "hover:border-primary/50",
                submitted && choice.is_correct && "border-success bg-success/10",
                submitted && isSelected && !choice.is_correct && "border-destructive bg-destructive/10",
              )}
            >
              <RadioGroupItem id={choice.id} value={choice.id} disabled={submitted} />
              <span className="flex-1 text-foreground">{choice.choice_text}</span>
              {submitted && choice.is_correct && <Check className="h-4 w-4 shrink-0 text-success" />}
              {submitted && isSelected && !choice.is_correct && <X className="h-4 w-4 shrink-0 text-destructive" />}
            </Label>
          );
        })}
    </RadioGroup>
  );
}
