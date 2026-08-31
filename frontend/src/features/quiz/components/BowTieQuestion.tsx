import { Check, X } from "lucide-react";

import { cn } from "@/lib/utils";
import { BOWTIE_SECTION_LABELS, type BowTieOption, type BowTieSection } from "@/types/question";

const SECTION_ORDER: BowTieSection[] = ["ASSESSMENT", "CONDITION", "ACTION"];

export function BowTieQuestion({
  options,
  selectedOptionIds,
  submitted,
  onToggle,
}: {
  options: BowTieOption[];
  selectedOptionIds: number[];
  submitted: boolean;
  onToggle: (optionId: number) => void;
}) {
  const bySection = (section: BowTieSection) =>
    options.filter((o) => o.section === section).sort((a, b) => a.display_order - b.display_order);

  return (
    <div className="bowtie">
      <p className="sata-label">Complete the bow-tie</p>
      <div className="bowtie-diagram" aria-hidden="true">
        <span className="bowtie-wing bowtie-wing-left" />
        <span className="bowtie-knot" />
        <span className="bowtie-wing bowtie-wing-right" />
      </div>
      <div className="bowtie-cols">
        {SECTION_ORDER.map((section) => (
          <div key={section} className="bowtie-col">
            <span className="bowtie-col-label">{BOWTIE_SECTION_LABELS[section]}</span>
            <div className="bowtie-options">
              {bySection(section).map((option) => {
                const isSelected = selectedOptionIds.includes(option.id);
                const isCorrect = submitted && option.is_correct;
                const isWrongPick = submitted && isSelected && !option.is_correct;
                return (
                  <button
                    key={option.id}
                    type="button"
                    disabled={submitted}
                    onClick={() => onToggle(option.id)}
                    className={cn(
                      "bowtie-option",
                      !submitted && isSelected && "selected",
                      isCorrect && "correct",
                      isWrongPick && "incorrect",
                    )}
                  >
                    <span style={{ flex: 1 }}>{option.option_text}</span>
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
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      {submitted && (
        <div className="bowtie-rationales">
          {options
            .filter((o) => o.rationale)
            .map((option) => (
              <p key={option.id} className="choice-rationale">
                <span className="matrix-row-rationale-label">{option.option_text}: </span>
                {option.rationale}
              </p>
            ))}
        </div>
      )}
    </div>
  );
}
