import { Plus } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { RationaleField } from "@/features/admin/components/builders/RationaleField";
import { OptionRowActions } from "@/features/admin/components/builders/OptionRowActions";
import type { HotSpotTargetDraft } from "@/types/admin";

interface HotSpotBuilderProps {
  stem: string;
  targets: HotSpotTargetDraft[];
  onChange: (targets: HotSpotTargetDraft[]) => void;
}

/**
 * Targets are validated server-side against the exact stem text, so this
 * builder has the editor SELECT the phrase from the stem itself (via the
 * browser's own text selection) rather than free-typing it — that
 * eliminates the whole class of near-miss whitespace/typo failures the
 * server-side "must appear verbatim" rule exists to catch.
 */
export function HotSpotBuilder({ stem, targets, onChange }: HotSpotBuilderProps) {
  const [selectedText, setSelectedText] = useState("");

  function handleStemMouseUp() {
    const selection = window.getSelection()?.toString().trim() ?? "";
    setSelectedText(selection);
  }

  function addTarget() {
    if (!selectedText) return;
    onChange([
      ...targets,
      { target_text: selectedText, is_correct: false, display_order: targets.length, rationale: "" },
    ]);
    setSelectedText("");
  }

  function updateTarget(index: number, patch: Partial<HotSpotTargetDraft>) {
    onChange(targets.map((t, i) => (i === index ? { ...t, ...patch } : t)));
  }

  function removeTarget(index: number) {
    onChange(targets.filter((_, i) => i !== index).map((t, i) => ({ ...t, display_order: i })));
  }

  return (
    <div className="flex flex-col gap-3">
      <div>
        <p className="text-sm font-medium text-foreground">Select a phrase from the stem, then add it as a target</p>
        <div
          onMouseUp={handleStemMouseUp}
          className="mt-2 rounded-lg border border-border bg-muted/30 p-3 text-sm text-foreground select-text"
        >
          {stem || <span className="text-muted-foreground">Write the stem above first.</span>}
        </div>
        <div className="mt-2 flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {selectedText ? `Selected: "${selectedText}"` : "Highlight text above to select it"}
          </span>
          <Button variant="outline" size="sm" onClick={addTarget} disabled={!selectedText}>
            <Plus className="h-4 w-4" />
            Add as target
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {targets.map((target, index) => (
          <div key={index} className="flex flex-col gap-2 rounded-lg border border-border p-3">
            <div className="flex items-center gap-2">
              <Checkbox
                checked={target.is_correct}
                onCheckedChange={(checked) => updateTarget(index, { is_correct: checked === true })}
                aria-label={`Mark target ${index + 1} correct`}
              />
              <span className="flex-1 text-sm text-foreground">{target.target_text}</span>
              <OptionRowActions onDelete={() => removeTarget(index)} />
            </div>
            <RationaleField value={target.rationale} onChange={(v) => updateTarget(index, { rationale: v })} />
          </div>
        ))}
      </div>

      {targets.length === 0 ? (
        <p className="text-xs text-destructive">At least one target is required.</p>
      ) : null}
    </div>
  );
}
