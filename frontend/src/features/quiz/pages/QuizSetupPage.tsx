import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MOCK_QUESTIONS } from "@/features/quiz/data/mockQuestions";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { DIFFICULTY_LABELS, QUESTION_TYPE_LABELS, SUPPORTED_QUESTION_TYPES, type Difficulty, type QuestionType } from "@/types/question";
import type { QuizFilterConfig } from "@/types/quiz";

const NURSING_SYSTEMS = ["Cardiovascular", "Respiratory", "Endocrine", "Pharmacology", "Renal"];
const QUESTION_COUNTS = [5, 10, 20];
const ALL_TYPES = Object.keys(QUESTION_TYPE_LABELS) as QuestionType[];

export function QuizSetupPage() {
  const navigate = useNavigate();
  const [nursingSystem, setNursingSystem] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty | null>(null);
  const [questionTypes, setQuestionTypes] = useState<QuestionType[]>(["MCQ", "SATA"]);
  const [questionCount, setQuestionCount] = useState(5);

  function toggleType(type: QuestionType) {
    if (!SUPPORTED_QUESTION_TYPES.includes(type)) return;
    setQuestionTypes((prev) => (prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]));
  }

  function handleStart() {
    let pool = MOCK_QUESTIONS.filter((q) => questionTypes.length === 0 || questionTypes.includes(q.question_type));
    if (nursingSystem) pool = pool.filter((q) => q.nursing_system === nursingSystem);
    if (difficulty) pool = pool.filter((q) => q.difficulty === difficulty);
    if (pool.length === 0) pool = MOCK_QUESTIONS.filter((q) => SUPPORTED_QUESTION_TYPES.includes(q.question_type));

    const filterConfig: QuizFilterConfig = {
      nursing_system: nursingSystem,
      difficulty,
      question_types: questionTypes,
      question_count: questionCount,
    };

    navigate(ROUTES.quizSession, { state: { questions: pool.slice(0, questionCount), filterConfig } });
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-foreground">Start a practice quiz</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Using a sample question set for this preview, not the full content-team bank.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-foreground">Nursing system</label>
              <Select value={nursingSystem ?? "any"} onValueChange={(v) => setNursingSystem(v === "any" ? null : String(v))}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Any system" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">Any system</SelectItem>
                  {NURSING_SYSTEMS.map((system) => (
                    <SelectItem key={system} value={system}>
                      {system}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-foreground">Question count</label>
              <Select value={String(questionCount)} onValueChange={(v) => setQuestionCount(Number(v))}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {QUESTION_COUNTS.map((count) => (
                    <SelectItem key={count} value={String(count)}>
                      {count} questions
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-foreground">Difficulty</label>
            <div className="flex flex-wrap gap-2">
              {(["EASY", "MEDIUM", "HARD"] as Difficulty[]).map((level) => (
                <button
                  key={level}
                  type="button"
                  onClick={() => setDifficulty((prev) => (prev === level ? null : level))}
                  className={cn(
                    "rounded-full border px-3 py-1 text-sm font-medium transition-colors",
                    difficulty === level
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border text-muted-foreground hover:border-primary/50",
                  )}
                >
                  {DIFFICULTY_LABELS[level]}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-foreground">Question types</label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {ALL_TYPES.map((type) => {
                const supported = SUPPORTED_QUESTION_TYPES.includes(type);
                const selected = questionTypes.includes(type);
                return (
                  <button
                    key={type}
                    type="button"
                    disabled={!supported}
                    onClick={() => toggleType(type)}
                    className={cn(
                      "flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-left text-xs font-medium transition-colors",
                      !supported && "cursor-not-allowed border-border/60 text-muted-foreground/50",
                      supported && selected && "border-primary bg-secondary/50 text-foreground",
                      supported && !selected && "border-border text-muted-foreground hover:border-primary/50",
                    )}
                  >
                    {QUESTION_TYPE_LABELS[type]}
                    {!supported && (
                      <Badge variant="outline" className="shrink-0 text-[10px]">
                        Soon
                      </Badge>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      <Button size="lg" onClick={handleStart}>
        Start practice quiz
      </Button>
    </div>
  );
}
