import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { OptionRowActions } from "@/features/admin/components/builders/OptionRowActions";
import { RationaleField } from "@/features/admin/components/builders/RationaleField";
import type { ClozeBlankDraft } from "@/types/admin";

interface ClozeBuilderProps {
  stem: string;
  blanks: ClozeBlankDraft[];
  onChange: (blanks: ClozeBlankDraft[]) => void;
}

const STEM_TOKEN_PATTERN = /\[([^[\]]+)]/g;

function stemTokens(stem: string): string[] {
  return [...stem.matchAll(STEM_TOKEN_PATTERN)].map((m) => m[1].trim().toLowerCase());
}

/** Each blank_key must match a literal [blank key] token in the stem — enforced server-side, surfaced here as a live hint. */
export function ClozeBuilder({ stem, blanks, onChange }: ClozeBuilderProps) {
  const tokens = new Set(stemTokens(stem));
  const blankKeys = new Set(blanks.map((b) => b.blank_key.trim().toLowerCase()));
  const missingInStem = blanks.filter((b) => !tokens.has(b.blank_key.trim().toLowerCase()));
  const missingBlank = [...tokens].filter((t) => !blankKeys.has(t));

  function updateBlank(index: number, patch: Partial<ClozeBlankDraft>) {
    onChange(blanks.map((b, i) => (i === index ? { ...b, ...patch } : b)));
  }

  function addBlank() {
    onChange([
      ...blanks,
      {
        blank_key: `dropdown ${blanks.length + 1}`,
        display_order: blanks.length,
        options: [
          { option_text: "", is_correct: true, rationale: "" },
          { option_text: "", is_correct: false, rationale: "" },
        ],
      },
    ]);
  }

  function removeBlank(index: number) {
    onChange(blanks.filter((_, i) => i !== index).map((b, i) => ({ ...b, display_order: i })));
  }

  function updateOption(blankIndex: number, optionIndex: number, patch: Partial<ClozeBlankDraft["options"][number]>) {
    const blank = blanks[blankIndex];
    updateBlank(blankIndex, {
      options: blank.options.map((o, i) => (i === optionIndex ? { ...o, ...patch } : o)),
    });
  }

  function setCorrectOption(blankIndex: number, optionIndex: number) {
    const blank = blanks[blankIndex];
    updateBlank(blankIndex, {
      options: blank.options.map((o, i) => ({ ...o, is_correct: i === optionIndex })),
    });
  }

  function addOption(blankIndex: number) {
    const blank = blanks[blankIndex];
    updateBlank(blankIndex, { options: [...blank.options, { option_text: "", is_correct: false, rationale: "" }] });
  }

  function removeOption(blankIndex: number, optionIndex: number) {
    const blank = blanks[blankIndex];
    updateBlank(blankIndex, { options: blank.options.filter((_, i) => i !== optionIndex) });
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-muted-foreground">
        Write <code>[blank key]</code> placeholders directly in the stem above (e.g. "assess the client's{" "}
        <code>[dropdown 1]</code>"), then define each blank's options here.
      </p>

      {missingInStem.length > 0 ? (
        <p className="text-xs text-destructive">
          No matching stem placeholder for: {missingInStem.map((b) => b.blank_key).join(", ")}
        </p>
      ) : null}
      {missingBlank.length > 0 ? (
        <p className="text-xs text-destructive">Stem has placeholder(s) with no blank defined: {missingBlank.join(", ")}</p>
      ) : null}

      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-foreground">Blanks</span>
        <Button variant="outline" size="sm" onClick={addBlank}>
          <Plus className="h-4 w-4" />
          Add blank
        </Button>
      </div>

      {blanks.map((blank, blankIndex) => (
        <div key={blankIndex} className="flex flex-col gap-3 rounded-lg border border-border p-3">
          <div className="flex items-center gap-2">
            <Label className="text-xs text-muted-foreground">Blank key</Label>
            <Input
              value={blank.blank_key}
              onChange={(e) => updateBlank(blankIndex, { blank_key: e.target.value })}
              className="max-w-48"
            />
            <OptionRowActions onDelete={() => removeBlank(blankIndex)} />
          </div>

          <div className="flex flex-col gap-2 pl-4">
            {blank.options.map((option, optionIndex) => (
              <div key={optionIndex} className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={option.is_correct}
                    onCheckedChange={() => setCorrectOption(blankIndex, optionIndex)}
                    aria-label={`Mark option ${optionIndex + 1} correct`}
                  />
                  <Input
                    value={option.option_text}
                    onChange={(e) => updateOption(blankIndex, optionIndex, { option_text: e.target.value })}
                    placeholder={`Option ${optionIndex + 1}`}
                    className="flex-1"
                  />
                  <OptionRowActions onDelete={() => removeOption(blankIndex, optionIndex)} />
                </div>
                <RationaleField
                  value={option.rationale}
                  onChange={(v) => updateOption(blankIndex, optionIndex, { rationale: v })}
                />
              </div>
            ))}
            <Button variant="ghost" size="sm" className="w-fit" onClick={() => addOption(blankIndex)}>
              <Plus className="h-4 w-4" />
              Add option
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
