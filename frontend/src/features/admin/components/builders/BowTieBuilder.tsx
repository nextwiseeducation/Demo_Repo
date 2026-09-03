import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { OptionRowActions, reorder } from "@/features/admin/components/builders/OptionRowActions";
import { RationaleField } from "@/features/admin/components/builders/RationaleField";
import { BOWTIE_SECTIONS, BOWTIE_SECTION_LABELS, type BowTieOptionDraft } from "@/types/admin";

interface BowTieBuilderProps {
  options: BowTieOptionDraft[];
  onChange: (options: BowTieOptionDraft[]) => void;
}

/** Three independent columns (Assessment / Condition / Action) — each requires at least one option and one correct answer. */
export function BowTieBuilder({ options, onChange }: BowTieBuilderProps) {
  function sectionOptions(section: BowTieOptionDraft["section"]) {
    return options.filter((o) => o.section === section);
  }

  function updateSection(section: BowTieOptionDraft["section"], next: BowTieOptionDraft[]) {
    onChange([...options.filter((o) => o.section !== section), ...next]);
  }

  function addOption(section: BowTieOptionDraft["section"]) {
    const current = sectionOptions(section);
    updateSection(section, [
      ...current,
      { section, option_text: "", is_correct: false, display_order: current.length, rationale: "" },
    ]);
  }

  function updateOption(section: BowTieOptionDraft["section"], index: number, patch: Partial<BowTieOptionDraft>) {
    const current = sectionOptions(section);
    updateSection(section, current.map((o, i) => (i === index ? { ...o, ...patch } : o)));
  }

  function removeOption(section: BowTieOptionDraft["section"], index: number) {
    const current = sectionOptions(section);
    updateSection(
      section,
      current.filter((_, i) => i !== index).map((o, i) => ({ ...o, display_order: i })),
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {BOWTIE_SECTIONS.map((section) => {
        const current = sectionOptions(section);
        return (
          <div key={section} className="flex flex-col gap-3 rounded-lg border border-border p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-foreground">{BOWTIE_SECTION_LABELS[section]}</span>
              <Button variant="ghost" size="icon-xs" onClick={() => addOption(section)} aria-label={`Add ${section} option`}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            {current.map((option, index) => (
              <div key={index} className="flex flex-col gap-2 rounded-md border border-border p-2">
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={option.is_correct}
                    onCheckedChange={(checked) => updateOption(section, index, { is_correct: checked === true })}
                    aria-label={`Mark ${section} option ${index + 1} correct`}
                  />
                  <Input
                    value={option.option_text}
                    onChange={(e) => updateOption(section, index, { option_text: e.target.value })}
                    className="flex-1 text-sm"
                  />
                  <OptionRowActions
                    onMoveUp={() => updateSection(section, reorder(current, index, -1))}
                    onMoveDown={() => updateSection(section, reorder(current, index, 1))}
                    onDelete={() => removeOption(section, index)}
                    canMoveUp={index > 0}
                    canMoveDown={index < current.length - 1}
                  />
                </div>
                <RationaleField
                  value={option.rationale}
                  onChange={(v) => updateOption(section, index, { rationale: v })}
                />
              </div>
            ))}
            {current.length === 0 ? (
              <p className="text-xs text-destructive">At least one option is required.</p>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
