import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useTaxonomyOptions } from "@/features/admin/hooks/useTaxonomyOptions";
import type { CaseStudyDraft } from "@/types/admin";

const NEW_CASE_VALUE = "__new__";

interface CaseStudyFieldsProps {
  caseStudy: CaseStudyDraft | null;
  caseStudySequence: number | null;
  onCaseStudyChange: (caseStudy: CaseStudyDraft | null) => void;
  onSequenceChange: (sequence: number | null) => void;
}

/**
 * NGN_CASE authoring: one Question row is one case ITEM (see
 * Question.case_study_sequence) — this section lets the editor pick an
 * existing case or create one inline, then set this item's position
 * within it. The actual item structure (MCQ/MATRIX/etc, per ngn_type)
 * renders below via the normal StructureBuilder dispatch.
 */
export function CaseStudyFields({
  caseStudy,
  caseStudySequence,
  onCaseStudyChange,
  onSequenceChange,
}: CaseStudyFieldsProps) {
  const { data: taxonomy } = useTaxonomyOptions();
  const isNew = !caseStudy?.id;

  function handleCaseSelect(value: string | null) {
    if (!value) return;
    if (value === NEW_CASE_VALUE) {
      onCaseStudyChange({ external_id: "", title: "", shared_scenario: "" });
      return;
    }
    const existing = taxonomy?.case_studies.find((c) => c.id.toString() === value);
    if (existing) {
      onCaseStudyChange({ id: existing.id, title: existing.title });
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border p-3">
      <span className="text-sm font-medium text-foreground">Case study</span>

      <div className="flex flex-col gap-1">
        <Label className="text-xs text-muted-foreground">Case</Label>
        <Select value={caseStudy?.id?.toString() ?? (caseStudy ? NEW_CASE_VALUE : "")} onValueChange={handleCaseSelect}>
          <SelectTrigger>
            <SelectValue placeholder="Choose an existing case or create a new one" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={NEW_CASE_VALUE}>+ Create new case</SelectItem>
            {taxonomy?.case_studies.map((c) => (
              <SelectItem key={c.id} value={c.id.toString()}>
                {c.title} {c.external_id ? `(${c.external_id})` : ""}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {caseStudy && isNew ? (
        <>
          <div className="flex flex-col gap-1">
            <Label className="text-xs text-muted-foreground">Case external ID (optional)</Label>
            <Input
              value={caseStudy.external_id ?? ""}
              onChange={(e) => onCaseStudyChange({ ...caseStudy, external_id: e.target.value })}
              placeholder="CASE-014"
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label className="text-xs text-muted-foreground">Case title</Label>
            <Input
              value={caseStudy.title ?? ""}
              onChange={(e) => onCaseStudyChange({ ...caseStudy, title: e.target.value })}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label className="text-xs text-muted-foreground">Shared clinical scenario</Label>
            <Textarea
              value={caseStudy.shared_scenario ?? ""}
              onChange={(e) => onCaseStudyChange({ ...caseStudy, shared_scenario: e.target.value })}
              rows={4}
            />
          </div>
        </>
      ) : null}

      <div className="flex flex-col gap-1">
        <Label className="text-xs text-muted-foreground">Sequence within case</Label>
        <Input
          type="number"
          min={1}
          value={caseStudySequence ?? ""}
          onChange={(e) => onSequenceChange(e.target.value ? Number(e.target.value) : null)}
          className="w-24"
        />
      </div>
    </div>
  );
}
