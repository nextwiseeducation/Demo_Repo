import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import * as questionsApi from "@/lib/api/questions";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { DIFFICULTY_LABELS, QUESTION_TYPE_LABELS, SUPPORTED_QUESTION_TYPES, type Difficulty, type QuestionType } from "@/types/question";
import type { QuizFilterConfig } from "@/types/quiz";

const QUESTION_COUNTS = [5, 10, 20];
const ALL_TYPES = Object.keys(QUESTION_TYPE_LABELS) as QuestionType[];

function joinLabels(labels: string[]): string {
  if (labels.length === 0) return "";
  if (labels.length === 1) return labels[0];
  if (labels.length === 2) return `${labels[0]} and ${labels[1]}`;
  return `${labels.slice(0, -1).join(", ")}, and ${labels[labels.length - 1]}`;
}

export function QuizSetupPage() {
  const navigate = useNavigate();
  const [nursingSystem, setNursingSystem] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty | null>(null);
  const [questionTypes, setQuestionTypes] = useState<QuestionType[]>(["MCQ", "SATA"]);
  const [questionCount, setQuestionCount] = useState(5);

  const questionsQuery = useQuery({ queryKey: ["questions"], queryFn: questionsApi.listQuestions });
  const allQuestions = questionsQuery.data ?? [];
  // Built from whatever's actually in the bank rather than a fixed list —
  // a hardcoded system list would drift out of sync with real content the
  // moment the content team adds a system this dropdown doesn't know about.
  const nursingSystems = [...new Set(allQuestions.map((q) => q.nursing_system))].sort();

  function toggleType(type: QuestionType) {
    if (!SUPPORTED_QUESTION_TYPES.includes(type)) return;
    setQuestionTypes((prev) => (prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]));
  }

  function handleStart() {
    let pool = allQuestions.filter((q) => questionTypes.length === 0 || questionTypes.includes(q.question_type));
    if (nursingSystem) pool = pool.filter((q) => q.nursing_system === nursingSystem);
    if (difficulty) pool = pool.filter((q) => q.difficulty === difficulty);
    if (pool.length === 0) pool = allQuestions.filter((q) => SUPPORTED_QUESTION_TYPES.includes(q.question_type));

    const filterConfig: QuizFilterConfig = {
      nursing_system: nursingSystem,
      difficulty,
      question_types: questionTypes,
      question_count: questionCount,
    };

    navigate(ROUTES.quizSession, { state: { questions: pool.slice(0, questionCount), filterConfig } });
  }

  const selectedTypeLabels = questionTypes.map((t) => QUESTION_TYPE_LABELS[t]);
  const summaryText = questionsQuery.isPending
    ? "Loading questions..."
    : questionTypes.length === 0
      ? "Select at least one question type to continue"
      : `${questionCount} ${difficulty ? `${DIFFICULTY_LABELS[difficulty].toLowerCase()} ` : ""}question${questionCount === 1 ? "" : "s"} · ${joinLabels(selectedTypeLabels)}`;

  return (
    <div className="page">
      <div>
        <h1 className="page-title">Start a practice quiz</h1>
        <p className="page-sub">
          {questionsQuery.isError
            ? "Couldn't load the question bank. Try refreshing the page."
            : "MCQ and SATA questions are interactive today; other NGN formats are shown but not yet answerable."}
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">Filters</div>
        </div>
        <div className="card-content">
          <div className="field-grid">
            <div className="field">
              <label>Nursing system</label>
              <Select value={nursingSystem ?? "any"} onValueChange={(v) => setNursingSystem(v === "any" ? null : String(v))}>
                <SelectTrigger className="h-[38px] w-full rounded-[10px] border-[color:var(--border)] bg-[#fdfdff] text-[14px]">
                  <SelectValue placeholder="All systems" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">All systems</SelectItem>
                  {nursingSystems.map((system) => (
                    <SelectItem key={system} value={system}>
                      {system}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="field">
              <label>Question count</label>
              <Select value={String(questionCount)} onValueChange={(v) => setQuestionCount(Number(v))}>
                <SelectTrigger className="h-[38px] w-full rounded-[10px] border-[color:var(--border)] bg-[#fdfdff] text-[14px]">
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

          <div className="field">
            <label>Difficulty</label>
            <div className="pill-row">
              {(["EASY", "MEDIUM", "HARD"] as Difficulty[]).map((level) => (
                <button
                  key={level}
                  type="button"
                  onClick={() => setDifficulty((prev) => (prev === level ? null : level))}
                  className={cn("pill", difficulty === level && "selected")}
                >
                  {DIFFICULTY_LABELS[level]}
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <label>Question types</label>
            <div className="type-grid">
              {ALL_TYPES.map((type) => {
                const supported = SUPPORTED_QUESTION_TYPES.includes(type);
                const selected = questionTypes.includes(type);
                return (
                  <button
                    key={type}
                    type="button"
                    disabled={!supported}
                    onClick={() => toggleType(type)}
                    className={cn("type-btn", supported && selected && "selected", !supported && "disabled")}
                  >
                    {QUESTION_TYPE_LABELS[type]}
                    {!supported && <span className="soon-badge">Soon</span>}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="divider" />

          <div className="summary">
            <span className="summary-text">{summaryText}</span>
            <button
              type="button"
              className="btn-primary"
              disabled={questionTypes.length === 0 || questionsQuery.isPending || allQuestions.length === 0}
              onClick={handleStart}
            >
              Start practice quiz
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
