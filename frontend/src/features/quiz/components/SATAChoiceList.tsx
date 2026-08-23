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
}: {
  choices: AnswerChoice[];
  selectedIds: string[];
  submitted: boolean;
  onToggle: (choiceId: string) => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Select all that apply</p>
      {[...choices]
        .sort((a, b) => a.display_order - b.display_order)
        .map((choice) => {
          const isSelected = selectedIds.includes(choice.id);
          return (
            <Label
              key={choice.id}
              htmlFor={choice.id}
              className={cn(
                "group/field-label flex cursor-pointer flex-col gap-2 rounded-lg border border-border bg-card px-4 py-3 text-sm font-normal transition-colors",
                !submitted && isSelected && "border-primary bg-secondary/50",
                !submitted && "hover:border-primary/50",
                submitted && choice.is_correct && "border-success bg-success/10",
                submitted && isSelected && !choice.is_correct && "border-destructive bg-destructive/10",
              )}
            >
              <div className="flex items-center gap-3">
                <Checkbox
                  id={choice.id}
                  checked={isSelected}
                  onCheckedChange={() => onToggle(choice.id)}
                  disabled={submitted}
                />
                <span className="flex-1 text-foreground">{choice.choice_text}</span>
                {submitted && choice.is_correct && <Check className="h-4 w-4 shrink-0 text-success" />}
                {submitted && isSelected && !choice.is_correct && <X className="h-4 w-4 shrink-0 text-destructive" />}
              </div>
              {submitted && choice.rationale && (
                <p className="pl-7 text-sm leading-relaxed text-muted-foreground">{choice.rationale}</p>
              )}
            </Label>
          );
        })}
    </div>
  );
}
