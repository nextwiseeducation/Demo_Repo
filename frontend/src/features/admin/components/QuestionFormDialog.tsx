import { useEffect, useState } from "react";

import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { CaseStudyFields } from "@/features/admin/components/builders/CaseStudyFields";
import { StructureBuilder } from "@/features/admin/components/builders/index";
import { useAdminQuestion, useCreateAdminQuestion, useUpdateAdminQuestion } from "@/features/admin/hooks/useAdminQuestions";
import { useTaxonomyOptions } from "@/features/admin/hooks/useTaxonomyOptions";
import { normalizeApiError } from "@/lib/api/errors";
import {
  CLINICAL_JUDGMENT_SKILL_LABELS,
  COGNITIVE_LEVEL_LABELS,
  DIFFICULTY_LABELS,
  nextDraftKey,
  STRUCTURE_KEYS_BY_TYPE,
  type AdminQuestionDetail,
  type QuestionDraft,
} from "@/types/admin";
import { QUESTION_TYPE_LABELS, SUPPORTED_QUESTION_TYPES, type QuestionType } from "@/types/question";

interface QuestionFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** null = create mode; a question id = edit mode. */
  questionId: string | null;
}

const ALL_QUESTION_TYPES = [...SUPPORTED_QUESTION_TYPES, "NGN_CASE" as const];
const ALL_STRUCTURE_KEYS: (keyof QuestionDraft)[] = [
  "answer_choices",
  "matrix_columns",
  "matrix_rows",
  "bowtie_options",
  "cloze_blanks",
  "dragdrop_categories",
  "dragdrop_items",
  "hotspot_targets",
];

function defaultStructureFor(type: QuestionType): Partial<QuestionDraft> {
  const cleared: Partial<QuestionDraft> = Object.fromEntries(ALL_STRUCTURE_KEYS.map((k) => [k, undefined]));
  switch (type) {
    case "MCQ":
    case "SATA":
    case "EMR":
      return {
        ...cleared,
        answer_choices: [
          { choice_text: "", is_correct: true, display_order: 0, rationale: "" },
          { choice_text: "", is_correct: false, display_order: 1, rationale: "" },
        ],
      };
    case "MATRIX": {
      const c0 = nextDraftKey();
      const c1 = nextDraftKey();
      return {
        ...cleared,
        matrix_columns: [
          { key: c0, text: "", display_order: 0 },
          { key: c1, text: "", display_order: 1 },
        ],
        matrix_rows: [
          {
            key: nextDraftKey(),
            text: "",
            display_order: 0,
            cells: [
              { column_key: c0, is_correct: false, rationale: "" },
              { column_key: c1, is_correct: false, rationale: "" },
            ],
          },
        ],
      };
    }
    case "BOWTIE":
      return { ...cleared, bowtie_options: [] };
    case "CLOZE":
      return { ...cleared, cloze_blanks: [] };
    case "DRAG_DROP":
      return { ...cleared, dragdrop_categories: [], dragdrop_items: [] };
    case "HOTSPOT":
      return { ...cleared, hotspot_targets: [] };
    default:
      return cleared;
  }
}

function emptyDraft(): QuestionDraft {
  return {
    question_type: "MCQ",
    stem: "",
    clinical_scenario: "",
    difficulty: "MEDIUM",
    nursing_system_id: 0,
    topic_id: 0,
    nclex_client_needs_category_id: 0,
    nclex_client_needs_subcategory_id: 0,
    clinical_judgment_skill: "",
    cognitive_level: "",
    rationale_correct: "",
    rationale_incorrect: "",
    reference: "",
    key_takeaway: "",
    is_active: true,
    ...defaultStructureFor("MCQ"),
  };
}

function detailToDraft(detail: AdminQuestionDetail): QuestionDraft {
  return {
    external_id: detail.external_id,
    question_type: detail.question_type,
    ngn_type: detail.ngn_type,
    stem: detail.stem,
    clinical_scenario: detail.clinical_scenario,
    case_study: detail.case_study
      ? {
          id: detail.case_study.id,
          external_id: detail.case_study.external_id,
          title: detail.case_study.title,
          shared_scenario: detail.case_study.shared_scenario,
        }
      : null,
    case_study_sequence: detail.case_study_sequence,
    difficulty: detail.difficulty,
    domain_id: detail.domain_id,
    nursing_system_id: detail.nursing_system_id,
    topic_id: detail.topic_id,
    subtopic_id: detail.subtopic_id,
    nclex_client_needs_category_id: detail.nclex_client_needs_category_id,
    nclex_client_needs_subcategory_id: detail.nclex_client_needs_subcategory_id,
    clinical_judgment_skill: detail.clinical_judgment_skill,
    clinical_judgment_skill_secondary: detail.clinical_judgment_skill_secondary,
    cognitive_level: detail.cognitive_level,
    tag_ids: detail.tag_ids,
    rationale_correct: detail.rationale_correct ?? "",
    rationale_incorrect: detail.rationale_incorrect ?? "",
    reference: detail.reference ?? "",
    key_takeaway: detail.key_takeaway ?? "",
    is_active: detail.is_active,
    answer_choices: detail.answer_choices.map((c) => ({
      id: c.id,
      choice_text: c.choice_text,
      is_correct: c.is_correct,
      display_order: c.display_order,
      rationale: c.rationale,
    })),
    matrix_columns: detail.matrix_columns.map((c) => ({ key: String(c.id), text: c.text, display_order: c.display_order })),
    matrix_rows: detail.matrix_rows.map((r) => ({
      key: String(r.id),
      text: r.text,
      display_order: r.display_order,
      cells: r.cells.map((cell) => ({
        column_key: String(cell.column_id),
        is_correct: cell.is_correct,
        rationale: cell.rationale,
      })),
    })),
    bowtie_options: detail.bowtie_options.map((o) => ({
      section: o.section,
      option_text: o.option_text,
      is_correct: o.is_correct,
      display_order: o.display_order,
      rationale: o.rationale,
    })),
    cloze_blanks: detail.cloze_blanks.map((b) => ({
      blank_key: b.blank_key,
      display_order: b.display_order,
      options: b.options.map((o) => ({ option_text: o.option_text, is_correct: o.is_correct, rationale: o.rationale })),
    })),
    dragdrop_categories: detail.dragdrop_categories.map((c) => ({
      key: String(c.id),
      name: c.name,
      display_order: c.display_order,
    })),
    dragdrop_items: detail.dragdrop_items.map((i) => ({
      text: i.text,
      display_order: i.display_order,
      correct_category_key: i.correct_category !== null ? String(i.correct_category) : null,
      correct_order: i.correct_order,
      rationale: i.rationale,
    })),
    hotspot_targets: detail.hotspot_targets.map((t) => ({
      target_text: t.target_text,
      is_correct: t.is_correct,
      display_order: t.display_order,
      rationale: t.rationale,
    })),
  };
}

/** Strips structure keys that don't belong to the effective type, and NGN_CASE-only fields when not applicable, before the payload is sent. */
function buildPayload(draft: QuestionDraft): QuestionDraft {
  const effective = draft.question_type === "NGN_CASE" ? draft.ngn_type : draft.question_type;
  const allowed = new Set(effective ? (STRUCTURE_KEYS_BY_TYPE[effective] ?? []) : []);
  const payload: QuestionDraft = { ...draft };
  for (const key of ALL_STRUCTURE_KEYS) {
    if (!allowed.has(key)) delete payload[key];
  }
  if (draft.question_type !== "NGN_CASE") {
    delete payload.case_study;
    delete payload.case_study_sequence;
    delete payload.ngn_type;
  }
  return payload;
}

export function QuestionFormDialog({ open, onOpenChange, questionId }: QuestionFormDialogProps) {
  const isEdit = questionId !== null;
  const { data: detail, isPending: detailPending } = useAdminQuestion(questionId);
  const { data: taxonomy } = useTaxonomyOptions();
  const createMutation = useCreateAdminQuestion();
  const updateMutation = useUpdateAdminQuestion();

  const [draft, setDraft] = useState<QuestionDraft>(emptyDraft);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setFormError(null);
    if (isEdit && detail) {
      setDraft(detailToDraft(detail));
    } else if (!isEdit) {
      setDraft(emptyDraft());
    }
  }, [open, isEdit, detail]);

  function patch(p: Partial<QuestionDraft>) {
    setDraft((prev) => ({ ...prev, ...p }));
  }

  function handleQuestionTypeChange(value: string | null) {
    if (!value) return;
    const type = value as QuestionType;
    patch({ question_type: type, ngn_type: null, ...defaultStructureFor(type) });
  }

  function handleNgnTypeChange(value: string | null) {
    if (!value) return;
    const type = value as QuestionType;
    patch({ ngn_type: type, ...defaultStructureFor(type) });
  }

  function handleSubmit() {
    setFormError(null);
    const payload = buildPayload(draft);
    const onError = (error: unknown) => {
      const normalized = normalizeApiError(error);
      const detailMessage =
        normalized.detail ??
        (normalized.fieldErrors ? Object.values(normalized.fieldErrors).flat().join(" ") : null);
      setFormError(detailMessage ?? "Couldn't save this question.");
    };

    if (isEdit) {
      updateMutation.mutate({ id: questionId, draft: payload }, { onSuccess: () => onOpenChange(false), onError });
    } else {
      createMutation.mutate(payload, { onSuccess: () => onOpenChange(false), onError });
    }
  }

  const isSaving = createMutation.isPending || updateMutation.isPending;
  const selectedSystem = taxonomy?.nursing_systems.find((s) => s.id === draft.nursing_system_id);
  const selectedCategory = taxonomy?.client_needs_categories.find((c) => c.id === draft.nclex_client_needs_category_id);
  const showLoadingSkeleton = isEdit && detailPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] w-full max-w-3xl overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit question" : "Add question"}</DialogTitle>
        </DialogHeader>

        {showLoadingSkeleton ? (
          <Skeleton className="h-96 w-full" />
        ) : (
          <div className="flex flex-col gap-4">
            {isEdit ? (
              <p className="text-xs text-muted-foreground">
                Question ID: {questionId} · Created {detail ? new Date(detail.created_at).toLocaleString() : ""}
              </p>
            ) : null}

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">Question type</Label>
                <Select value={draft.question_type} onValueChange={handleQuestionTypeChange} disabled={isEdit}>
                  <SelectTrigger>
                    <SelectValue>{(value: string) => QUESTION_TYPE_LABELS[value as QuestionType] ?? value}</SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {ALL_QUESTION_TYPES.map((type) => (
                      <SelectItem key={type} value={type}>
                        {QUESTION_TYPE_LABELS[type]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {isEdit ? (
                  <p className="text-[11px] text-muted-foreground">Type cannot be changed after creation.</p>
                ) : null}
              </div>

              {draft.question_type === "NGN_CASE" ? (
                <div className="flex flex-col gap-1">
                  <Label className="text-xs text-muted-foreground">Renders as</Label>
                  <Select value={draft.ngn_type ?? ""} onValueChange={handleNgnTypeChange}>
                    <SelectTrigger>
                      <SelectValue placeholder="Choose the item type" />
                    </SelectTrigger>
                    <SelectContent>
                      {SUPPORTED_QUESTION_TYPES.map((type) => (
                        <SelectItem key={type} value={type}>
                          {QUESTION_TYPE_LABELS[type]}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ) : null}
            </div>

            {draft.question_type === "NGN_CASE" ? (
              <CaseStudyFields
                caseStudy={draft.case_study ?? null}
                caseStudySequence={draft.case_study_sequence ?? null}
                onCaseStudyChange={(case_study) => patch({ case_study })}
                onSequenceChange={(case_study_sequence) => patch({ case_study_sequence })}
              />
            ) : null}

            <div className="flex flex-col gap-1">
              <Label className="text-xs text-muted-foreground">Stem</Label>
              <Textarea value={draft.stem} onChange={(e) => patch({ stem: e.target.value })} rows={3} />
            </div>

            <div className="flex flex-col gap-1">
              <Label className="text-xs text-muted-foreground">Clinical scenario (optional)</Label>
              <Textarea
                value={draft.clinical_scenario ?? ""}
                onChange={(e) => patch({ clinical_scenario: e.target.value })}
                rows={2}
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">Difficulty</Label>
                <Select
                  value={draft.difficulty}
                  onValueChange={(value) => patch({ difficulty: value as QuestionDraft["difficulty"] })}
                >
                  <SelectTrigger>
                    <SelectValue>{(value: string) => DIFFICULTY_LABELS[value as "EASY" | "MEDIUM" | "HARD"] ?? value}</SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(DIFFICULTY_LABELS).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">Nursing system</Label>
                <Select
                  value={draft.nursing_system_id ? draft.nursing_system_id.toString() : ""}
                  onValueChange={(value) => patch({ nursing_system_id: Number(value), topic_id: 0 })}
                >
                  <SelectTrigger>
                    <SelectValue>
                      {(value: string) => taxonomy?.nursing_systems.find((s) => s.id.toString() === value)?.name ?? "Choose"}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {taxonomy?.nursing_systems.map((s) => (
                      <SelectItem key={s.id} value={s.id.toString()}>
                        {s.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">Topic</Label>
                <Select
                  value={draft.topic_id ? draft.topic_id.toString() : ""}
                  onValueChange={(value) => patch({ topic_id: Number(value) })}
                  disabled={!selectedSystem}
                >
                  <SelectTrigger>
                    <SelectValue>
                      {(value: string) => selectedSystem?.topics.find((t) => t.id.toString() === value)?.name ?? "Choose"}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {selectedSystem?.topics.map((t) => (
                      <SelectItem key={t.id} value={t.id.toString()}>
                        {t.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">NCLEX Client Needs category</Label>
                <Select
                  value={draft.nclex_client_needs_category_id ? draft.nclex_client_needs_category_id.toString() : ""}
                  onValueChange={(value) =>
                    patch({ nclex_client_needs_category_id: Number(value), nclex_client_needs_subcategory_id: 0 })
                  }
                >
                  <SelectTrigger>
                    <SelectValue>
                      {(value: string) =>
                        taxonomy?.client_needs_categories.find((c) => c.id.toString() === value)?.name ?? "Choose"
                      }
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {taxonomy?.client_needs_categories.map((c) => (
                      <SelectItem key={c.id} value={c.id.toString()}>
                        {c.name} ({c.exam_type})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">NCLEX Client Needs subcategory</Label>
                <Select
                  value={draft.nclex_client_needs_subcategory_id ? draft.nclex_client_needs_subcategory_id.toString() : ""}
                  onValueChange={(value) => patch({ nclex_client_needs_subcategory_id: Number(value) })}
                  disabled={!selectedCategory}
                >
                  <SelectTrigger>
                    <SelectValue>
                      {(value: string) =>
                        selectedCategory?.subcategories.find((s) => s.id.toString() === value)?.name ?? "Choose"
                      }
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {selectedCategory?.subcategories.map((s) => (
                      <SelectItem key={s.id} value={s.id.toString()}>
                        {s.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">Clinical judgment skill</Label>
                <Select
                  value={draft.clinical_judgment_skill}
                  onValueChange={(value) => value && patch({ clinical_judgment_skill: value })}
                >
                  <SelectTrigger>
                    <SelectValue>{(value: string) => CLINICAL_JUDGMENT_SKILL_LABELS[value] ?? "Choose"}</SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(CLINICAL_JUDGMENT_SKILL_LABELS).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">Cognitive level (Bloom's)</Label>
                <Select value={draft.cognitive_level} onValueChange={(value) => value && patch({ cognitive_level: value })}>
                  <SelectTrigger>
                    <SelectValue>{(value: string) => COGNITIVE_LEVEL_LABELS[value] ?? "Choose"}</SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(COGNITIVE_LEVEL_LABELS).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="rounded-lg border border-border p-3">
              <StructureBuilder draft={draft} onChange={patch} />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">Rationale (correct)</Label>
                <Textarea
                  value={draft.rationale_correct ?? ""}
                  onChange={(e) => patch({ rationale_correct: e.target.value })}
                  rows={2}
                />
              </div>
              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">Rationale (incorrect, optional)</Label>
                <Textarea
                  value={draft.rationale_incorrect ?? ""}
                  onChange={(e) => patch({ rationale_incorrect: e.target.value })}
                  rows={2}
                />
              </div>
              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">Reference (optional)</Label>
                <Input value={draft.reference ?? ""} onChange={(e) => patch({ reference: e.target.value })} />
              </div>
              <div className="flex flex-col gap-1">
                <Label className="text-xs text-muted-foreground">Key takeaway (optional)</Label>
                <Input value={draft.key_takeaway ?? ""} onChange={(e) => patch({ key_takeaway: e.target.value })} />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Switch checked={draft.is_active ?? true} onCheckedChange={(checked) => patch({ is_active: checked })} />
              <Label className="text-sm text-foreground">Active (visible in quizzes)</Label>
            </div>

            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSaving || showLoadingSkeleton}>
            {isSaving ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
