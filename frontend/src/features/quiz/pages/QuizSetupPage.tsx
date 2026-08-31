import { keepPreviousData, useMutation, useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useId, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import * as quizzesApi from "@/lib/api/quizzes";
import { ROUTES } from "@/lib/constants";
import { QUESTION_MODE_STATUS_LABELS, type QuestionFormat, type QuestionModeStatus, type QuizFilters } from "@/types/quiz";

const QUESTION_FORMATS: { value: QuestionFormat; label: string }[] = [
  { value: "TRADITIONAL", label: "Traditional" },
  { value: "NGN", label: "Next Gen" },
];

const CUSTOM_STATUS_OPTIONS: QuestionModeStatus[] = ["UNUSED", "INCORRECT", "MARKED", "OMITTED", "CORRECT"];

const MAX_QUESTION_COUNT = 500;
const DEFAULT_TIME_LIMIT_MINUTES = 60;

export function QuizSetupPage() {
  const navigate = useNavigate();

  const [questionTypes, setQuestionTypes] = useState<QuestionFormat[]>(["TRADITIONAL", "NGN"]);
  const [questionMode, setQuestionMode] = useState<"STANDARD" | "CUSTOM">("STANDARD");
  const [statusFilters, setStatusFilters] = useState<QuestionModeStatus[]>([]);
  const [domains, setDomains] = useState<number[]>([]);
  const [nursingSystems, setNursingSystems] = useState<number[]>([]);
  const [clientNeeds, setClientNeeds] = useState<number[]>([]);
  const [categoryTab, setCategoryTab] = useState<"subjects" | "client_needs">("subjects");
  const [isTutorMode, setIsTutorMode] = useState(true);
  const [isTimed, setIsTimed] = useState(false);
  const [timeLimitMinutes, setTimeLimitMinutes] = useState(DEFAULT_TIME_LIMIT_MINUTES);
  const [questionCount, setQuestionCount] = useState(20);
  const [questionCountError, setQuestionCountError] = useState<string | null>(null);

  // The one thing every card's live counts/option lists come from — see
  // getFacetCounts' own docstring for why arrays are comma-joined rather
  // than passed as plain axios params.
  const debouncedFilters = useDebouncedValue(
    { question_types: questionTypes, status_filters: statusFilters, domains, nursing_systems: nursingSystems, nclex_client_needs_subcategories: clientNeeds },
    300,
  );
  const facetQuery = useQuery({
    queryKey: ["quiz-facet-counts", debouncedFilters],
    queryFn: () => quizzesApi.getFacetCounts(debouncedFilters),
    placeholderData: keepPreviousData,
  });
  const counts = facetQuery.data;

  const createMutation = useMutation({
    mutationFn: quizzesApi.createQuizSession,
    onSuccess: (session) => navigate(ROUTES.quizSession, { state: { session } }),
  });

  function toggleQuestionType(format: QuestionFormat) {
    setQuestionTypes((prev) => {
      if (prev.includes(format)) {
        // Never allow the last remaining type to be unchecked — a quiz
        // needs at least one format to draw from.
        return prev.length === 1 ? prev : prev.filter((f) => f !== format);
      }
      return [...prev, format];
    });
  }

  function toggleStatusFilter(statusValue: QuestionModeStatus) {
    setStatusFilters((prev) => (prev.includes(statusValue) ? prev.filter((s) => s !== statusValue) : [...prev, statusValue]));
  }

  function toggleId(list: number[], setList: (next: number[]) => void, id: number) {
    setList(list.includes(id) ? list.filter((v) => v !== id) : [...list, id]);
  }

  function handleQuestionCountChange(value: string) {
    const parsed = Number(value);
    if (value.trim() === "" || !Number.isInteger(parsed) || parsed <= 0) {
      setQuestionCountError("Enter a whole number greater than 0");
      setQuestionCount(0);
      return;
    }
    if (parsed > MAX_QUESTION_COUNT) {
      setQuestionCountError(`Max ${MAX_QUESTION_COUNT} questions`);
      setQuestionCount(parsed);
      return;
    }
    setQuestionCountError(null);
    setQuestionCount(parsed);
  }

  function handleGenerateQuiz() {
    const filters: QuizFilters = {
      question_types: questionTypes,
      question_mode: questionMode,
      status_filters: statusFilters,
      domains,
      nursing_systems: nursingSystems,
      nclex_client_needs_subcategories: clientNeeds,
      is_tutor_mode: isTutorMode,
      is_timed: isTimed,
      time_limit_minutes: isTimed ? timeLimitMinutes : null,
      question_count: questionCount,
    };
    createMutation.mutate(filters);
  }

  const generateDisabled =
    createMutation.isPending || questionCountError !== null || questionCount === 0 || (questionMode === "CUSTOM" && statusFilters.length === 0);

  return (
    <div className="page">
      <div>
        <h1 className="page-title">Practice NCLEX-RN® Questions</h1>
        <p className="page-sub">Build a practice session based on what you want to study.</p>
      </div>

      <div className="grid gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Test Mode</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <ToggleRow
              label="Tutor"
              description="Shows the correct answer and explanation after you answer each question."
              checked={isTutorMode}
              onCheckedChange={setIsTutorMode}
            />
            <ToggleRow
              label="Timed"
              description="Sets a time limit on the test."
              checked={isTimed}
              onCheckedChange={setIsTimed}
            />
            {isTimed && (
              <div className="flex flex-col gap-1.5 pl-1">
                <Label htmlFor="time-accommodation">Time Accommodation (minutes)</Label>
                <p className="text-xs text-muted-foreground">Simulate your test accommodation by adjusting the allotted test time.</p>
                <Input
                  id="time-accommodation"
                  type="number"
                  min={1}
                  className="w-40"
                  value={timeLimitMinutes}
                  onChange={(e) => setTimeLimitMinutes(Math.max(1, Number(e.target.value) || 1))}
                />
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Question Type</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {QUESTION_FORMATS.map(({ value, label }) => {
              const stat = counts?.question_types[value];
              return (
                <CheckboxRow
                  key={value}
                  label={label}
                  checked={questionTypes.includes(value)}
                  disabled={questionTypes.length === 1 && questionTypes.includes(value)}
                  onCheckedChange={() => toggleQuestionType(value)}
                  trailing={stat ? <Badge variant="outline">{`${stat.unused}/${stat.total}`}</Badge> : null}
                />
              );
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Question Mode</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={questionMode} onValueChange={(v) => setQuestionMode(v as "STANDARD" | "CUSTOM")}>
              <TabsList>
                <TabsTrigger value="STANDARD">Standard</TabsTrigger>
                <TabsTrigger value="CUSTOM">Custom</TabsTrigger>
              </TabsList>
              <TabsContent value="STANDARD" className="pt-3">
                <p className="text-sm text-muted-foreground">Draws only from questions you haven't used yet.</p>
              </TabsContent>
              <TabsContent value="CUSTOM" className="flex flex-col gap-3 pt-3">
                {CUSTOM_STATUS_OPTIONS.map((statusValue) => {
                  const stat = counts?.question_mode[statusValue];
                  return (
                    <CheckboxRow
                      key={statusValue}
                      label={QUESTION_MODE_STATUS_LABELS[statusValue]}
                      checked={statusFilters.includes(statusValue)}
                      onCheckedChange={() => toggleStatusFilter(statusValue)}
                      trailing={stat ? <Badge variant="outline">{`${stat.count} (${stat.ngn_count} NGN)`}</Badge> : null}
                    />
                  );
                })}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Question Category</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={categoryTab} onValueChange={(v) => setCategoryTab(v as "subjects" | "client_needs")}>
              <TabsList>
                <TabsTrigger value="subjects">Subjects</TabsTrigger>
                <TabsTrigger value="client_needs">Client Needs</TabsTrigger>
              </TabsList>

              <TabsContent value="subjects" className="flex flex-col gap-5 pt-3">
                <div className="flex flex-col gap-3">
                  <span className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Subjects</span>
                  {(counts?.domains ?? []).map((row) => (
                    <CheckboxRow
                      key={row.id}
                      label={row.name}
                      checked={domains.includes(row.id)}
                      onCheckedChange={() => toggleId(domains, setDomains, row.id)}
                      trailing={<Badge variant="outline">{row.count}</Badge>}
                    />
                  ))}
                </div>
                <div className="flex flex-col gap-3">
                  <span className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Systems</span>
                  {(counts?.nursing_systems ?? []).map((row) => (
                    <CheckboxRow
                      key={row.id}
                      label={row.name}
                      checked={nursingSystems.includes(row.id)}
                      onCheckedChange={() => toggleId(nursingSystems, setNursingSystems, row.id)}
                      trailing={<Badge variant="outline">{row.count}</Badge>}
                    />
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="client_needs" className="flex flex-col gap-3 pt-3">
                <CheckboxRow
                  label="Select All"
                  checked={clientNeeds.length > 0 && clientNeeds.length === (counts?.nclex_client_needs_subcategories.length ?? 0)}
                  onCheckedChange={() =>
                    setClientNeeds(
                      clientNeeds.length === (counts?.nclex_client_needs_subcategories.length ?? 0)
                        ? []
                        : (counts?.nclex_client_needs_subcategories.map((row) => row.id) ?? []),
                    )
                  }
                />
                {(counts?.nclex_client_needs_subcategories ?? []).map((row) => (
                  <CheckboxRow
                    key={row.id}
                    label={row.name}
                    checked={clientNeeds.includes(row.id)}
                    onCheckedChange={() => toggleId(clientNeeds, setClientNeeds, row.id)}
                    trailing={<Badge variant="outline">{row.count}</Badge>}
                  />
                ))}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>No. of Questions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Input
                type="number"
                min={1}
                max={MAX_QUESTION_COUNT}
                value={questionCount || ""}
                onChange={(e) => handleQuestionCountChange(e.target.value)}
                className="w-40"
              />
              {questionCountError && <span className="text-xs text-destructive">{questionCountError}</span>}
              {questionMode === "CUSTOM" && statusFilters.length === 0 && (
                <span className="text-xs text-destructive">Select at least one Question Mode option in the Custom tab.</span>
              )}
              {createMutation.isError && (
                <span className="text-xs text-destructive">
                  {(createMutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
                    "Couldn't generate a quiz — try adjusting your filters."}
                </span>
              )}
            </div>
            <Button type="button" className="self-start" disabled={generateDisabled} onClick={handleGenerateQuiz}>
              {createMutation.isPending ? "Generating..." : "Generate Quiz"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ToggleRow({
  label,
  description,
  checked,
  onCheckedChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="flex flex-col gap-0.5">
        <span className="text-sm font-medium text-foreground">{label}</span>
        <span className="text-xs text-muted-foreground">{description}</span>
      </div>
      <Switch aria-label={label} checked={checked} onCheckedChange={onCheckedChange} className="mt-0.5 shrink-0" />
    </div>
  );
}

function CheckboxRow({
  label,
  checked,
  disabled,
  onCheckedChange,
  trailing,
}: {
  label: string;
  checked: boolean;
  disabled?: boolean;
  onCheckedChange: (checked: boolean) => void;
  trailing?: ReactNode;
}) {
  // A plain <label> wrapping Base UI's Checkbox does not reliably forward
  // clicks to its internal hidden input (it renders as a <span
  // role="checkbox"> sibling to a visually-hidden native input, connected
  // via aria-labelledby — not something a wrapping <label> toggles the way
  // it would a real <input>). Sibling id/htmlFor, matching how
  // RegisterPage.tsx already does this, is the pattern that actually works.
  const id = useId();
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex items-center gap-2.5">
        <Checkbox id={id} checked={checked} disabled={disabled} onCheckedChange={(v) => onCheckedChange(v === true)} />
        <Label htmlFor={id} className="text-sm font-normal text-foreground">
          {label}
        </Label>
      </div>
      {trailing}
    </div>
  );
}
