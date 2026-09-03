import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface RationaleFieldProps {
  value: string;
  onChange: (value: string) => void;
  label?: string;
}

/**
 * Shared by every child-model builder — AnswerChoice, MatrixCell,
 * BowTieOption, ClozeOption, DragDropItem and HotSpotTarget all carry an
 * editable per-option rationale field, so this exists once rather than
 * six times.
 */
export function RationaleField({ value, onChange, label = "Rationale" }: RationaleFieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={2}
        className="text-sm"
        placeholder="Why is this option correct or incorrect?"
      />
    </div>
  );
}
