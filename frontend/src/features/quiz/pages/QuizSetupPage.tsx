import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, Sparkles, TrendingUp } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import * as questionsApi from "@/lib/api/questions";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { DIFFICULTY_LABELS, QUESTION_TYPE_LABELS, SUPPORTED_QUESTION_TYPES, type Difficulty, type QuestionType } from "@/types/question";
import type { QuizFilterConfig } from "@/types/quiz";

const PRESET_COUNTS = [10, 20, 30, 50, 75, 100];
const MAX_CUSTOM_COUNT = 500;
const QUICK_PRACTICE_COUNT = 20;
const DIFFICULTY_LEVELS: Difficulty[] = ["EASY", "MEDIUM", "HARD"];
const ALL_TYPES = Object.keys(QUESTION_TYPE_LABELS) as QuestionType[];

function joinLabels(labels: string[]): string {
  if (labels.length === 0) return "";
  if (labels.length === 1) return labels[0];
  if (labels.length === 2) return `${labels[0]} and ${labels[1]}`;
  return `${labels.slice(0, -1).join(", ")}, and ${labels[labels.length - 1]}`;
}

/** "RECOGNIZE_CUES" -> "Recognize Cues" — clinical_judgment_skill has no label map on the frontend yet. */
function humanizeEnum(value: string): string {
  return value
    .toLowerCase()
    .split("_")
    .map((word) => (word ? word[0].toUpperCase() + word.slice(1) : word))
    .join(" ");
}

export function QuizSetupPage() {
  const navigate = useNavigate();
  const [nursingSystem, setNursingSystem] = useState<string | null>(null);
  const [topic, setTopic] = useState<string | null>(null);
  const [clientNeed, setClientNeed] = useState<string | null>(null);
  const [clinicalJudgmentSkill, setClinicalJudgmentSkill] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty[]>([]);
  const [questionTypes, setQuestionTypes] = useState<QuestionType[]>(["MCQ", "SATA"]);
  const [questionCount, setQuestionCount] = useState(20);
  const [isCustomCount, setIsCustomCount] = useState(false);
  const [customCountInput, setCustomCountInput] = useState("");
  const [customCountError, setCustomCountError] = useState<string | null>(null);
  const [showMoreFilters, setShowMoreFilters] = useState(false);

  const questionsQuery = useQuery({ queryKey: ["questions"], queryFn: questionsApi.listQuestions });
  const allQuestions = questionsQuery.data ?? [];

  // Built from whatever's actually in the bank rather than a fixed list —
  // a hardcoded list would drift out of sync with real content the moment
  // the content team adds a value this dropdown doesn't know about.
  const nursingSystems = [...new Set(allQuestions.map((q) => q.nursing_system))].sort();
  const topics = [...new Set(allQuestions.filter((q) => !nursingSystem || q.nursing_system === nursingSystem).map((q) => q.topic))].sort();
  const clientNeeds = [...new Set(allQuestions.map((q) => q.nclex_client_needs_category))].sort();
  const clinicalJudgmentSkills = [...new Set(allQuestions.map((q) => q.clinical_judgment_skill))].sort();

  function toggleType(type: QuestionType) {
    if (!SUPPORTED_QUESTION_TYPES.includes(type)) return;
    setQuestionTypes((prev) => (prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]));
  }

  function toggleDifficulty(level: Difficulty) {
    setDifficulty((prev) => (prev.includes(level) ? prev.filter((d) => d !== level) : [...prev, level]));
  }

  function handleNursingSystemChange(value: string | null) {
    setNursingSystem(value);
    // Topic is scoped to the selected system — clear it if it no longer applies.
    if (value && topic && !allQuestions.some((q) => q.nursing_system === value && q.topic === topic)) {
      setTopic(null);
    }
  }

  function handleCustomCountChange(value: string) {
    setCustomCountInput(value);
    const parsed = Number(value);
    if (value.trim() === "" || !Number.isInteger(parsed) || parsed <= 0) {
      setCustomCountError("Enter a whole number greater than 0");
      return;
    }
    if (parsed > MAX_CUSTOM_COUNT) {
      setCustomCountError(`Max ${MAX_CUSTOM_COUNT} questions`);
      return;
    }
    setCustomCountError(null);
    setQuestionCount(parsed);
  }

  // Filtered entirely client-side over the questions already loaded by the
  // useQuery above. That's fine at the bank's current size (~9 questions),
  // but once the content team's 4,000+ question bank lands, this filtering
  // (and the matching-count display below) should move server-side —
  // GET /api/questions/ would need query params rather than shipping the
  // full bank to the browser on every page load.
  function filteredPool() {
    let pool = allQuestions.filter((q) => questionTypes.length === 0 || questionTypes.includes(q.question_type));
    if (nursingSystem) pool = pool.filter((q) => q.nursing_system === nursingSystem);
    if (topic) pool = pool.filter((q) => q.topic === topic);
    if (clientNeed) pool = pool.filter((q) => q.nclex_client_needs_category === clientNeed);
    if (clinicalJudgmentSkill) pool = pool.filter((q) => q.clinical_judgment_skill === clinicalJudgmentSkill);
    if (difficulty.length > 0) pool = pool.filter((q) => difficulty.includes(q.difficulty));
    return pool;
  }

  const matchingPool = filteredPool();
  const matchingCount = matchingPool.length;
  const effectiveCount = Math.min(questionCount, matchingCount);
  // Blocks Start until a valid number is typed — otherwise selecting
  // "Custom number" without entering anything would silently fall back to
  // whatever preset count was chosen before, which the "selected" custom
  // pill would misleadingly suggest is no longer in effect.
  const hasCountError = isCustomCount && (customCountInput.trim() === "" || customCountError !== null);
  const startDisabled =
    questionTypes.length === 0 || questionsQuery.isPending || allQuestions.length === 0 || matchingCount === 0 || hasCountError;

  function handleStart() {
    if (startDisabled) return;
    const filterConfig: QuizFilterConfig = {
      nursing_system: nursingSystem,
      difficulty,
      question_types: questionTypes,
      question_count: effectiveCount,
      topic,
      nclex_client_needs_category: clientNeed,
      clinical_judgment_skill: clinicalJudgmentSkill,
    };
    navigate(ROUTES.quizSession, { state: { questions: matchingPool.slice(0, effectiveCount), filterConfig } });
  }

  function handleQuickPractice() {
    const pool = allQuestions.filter((q) => SUPPORTED_QUESTION_TYPES.includes(q.question_type));
    const count = Math.min(QUICK_PRACTICE_COUNT, pool.length);
    if (count === 0) return;
    const filterConfig: QuizFilterConfig = {
      nursing_system: null,
      difficulty: [],
      question_types: [...SUPPORTED_QUESTION_TYPES],
      question_count: count,
      topic: null,
      nclex_client_needs_category: null,
      clinical_judgment_skill: null,
    };
    navigate(ROUTES.quizSession, { state: { questions: pool.slice(0, count), filterConfig } });
  }

  const selectedDifficultyLabels = difficulty.map((d) => DIFFICULTY_LABELS[d]);
  const selectedTypeLabels = questionTypes.map((t) => QUESTION_TYPE_LABELS[t]);

  const summaryText = questionsQuery.isPending
    ? "Loading questions..."
    : questionTypes.length === 0
      ? "Select at least one question type to continue"
      : [
          `${effectiveCount} question${effectiveCount === 1 ? "" : "s"}`,
          difficulty.length > 0 ? joinLabels(selectedDifficultyLabels) : null,
          nursingSystem,
          topic,
          clientNeed,
          joinLabels(selectedTypeLabels),
        ]
          .filter((part): part is string => Boolean(part))
          .join(" · ");

  const matchStatusText = questionsQuery.isPending
    ? null
    : matchingCount === 0
      ? "No questions match your filters yet — try adjusting them."
      : matchingCount < questionCount
        ? `Only ${matchingCount} question${matchingCount === 1 ? "" : "s"} match${matchingCount === 1 ? "es" : ""} your filters — you can practice with ${matchingCount}, or adjust your filters.`
        : `${matchingCount} question${matchingCount === 1 ? "" : "s"} match${matchingCount === 1 ? "es" : ""} your filters`;

  return (
    <div className="page">
      <div>
        <h1 className="page-title">Practice NCLEX-RN® Questions</h1>
        <p className="page-sub">
          {questionsQuery.isError
            ? "Couldn't load the question bank. Try refreshing the page."
            : "Build a practice session based on what you want to study."}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="card flex flex-col gap-3 p-5">
          <div className="flex items-center gap-2">
            <Sparkles className="h-[18px] w-[18px] text-[color:var(--primary)]" />
            <span className="text-[15px] font-semibold text-[color:var(--fg)]">Quick Practice</span>
          </div>
          <p className="text-[13.5px] leading-relaxed text-[color:var(--muted-fg)]">
            Jump straight in with {QUICK_PRACTICE_COUNT} mixed multiple-choice and SATA questions — no filters needed.
          </p>
          <button
            type="button"
            className="btn-primary mt-auto self-start"
            disabled={questionsQuery.isPending || allQuestions.length === 0}
            onClick={handleQuickPractice}
          >
            Start quick practice
          </button>
        </div>

        <div className="card flex flex-col gap-3 p-5">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-[18px] w-[18px] text-[color:var(--muted-fg)]" />
            <span className="text-[15px] font-semibold text-[color:var(--fg)]">Practice My Weak Areas</span>
            <span className="soon-badge">Soon</span>
          </div>
          <p className="text-[13.5px] leading-relaxed text-[color:var(--muted-fg)]">
            Automatically pull questions from your weakest categories and the ones you've previously gotten wrong.
          </p>
          <button type="button" className="btn-primary mt-auto self-start" disabled>
            Coming soon
          </button>
          <p className="text-[12px] leading-relaxed text-[color:var(--muted-fg)]">
            Coming soon — this needs your answer history, which we're not tracking yet.
          </p>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">Filters</div>
        </div>
        <div className="card-content">
          <div className="field">
            <label>Question count</label>
            <div className="pill-row">
              {PRESET_COUNTS.map((count) => (
                <button
                  key={count}
                  type="button"
                  onClick={() => {
                    setIsCustomCount(false);
                    setQuestionCount(count);
                  }}
                  className={cn("pill", !isCustomCount && questionCount === count && "selected")}
                >
                  {count}
                </button>
              ))}
              <button type="button" onClick={() => setIsCustomCount(true)} className={cn("pill", isCustomCount && "selected")}>
                Custom number
              </button>
            </div>
            {isCustomCount && (
              <div className="flex flex-col gap-1 pt-1">
                <input
                  type="number"
                  min={1}
                  max={MAX_CUSTOM_COUNT}
                  value={customCountInput}
                  onChange={(e) => handleCustomCountChange(e.target.value)}
                  placeholder={`Number of questions (1–${MAX_CUSTOM_COUNT})`}
                  className="h-[38px] w-full rounded-[10px] border border-[color:var(--border)] bg-[#fdfdff] px-3 text-[14px] text-[color:var(--fg)] outline-none focus:border-[color:var(--primary)]"
                />
                {customCountError && <span className="text-[12.5px] text-[color:var(--destructive)]">{customCountError}</span>}
              </div>
            )}
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

          <div className="field">
            <label>Difficulty</label>
            <div className="pill-row">
              {DIFFICULTY_LEVELS.map((level) => (
                <button
                  key={level}
                  type="button"
                  onClick={() => toggleDifficulty(level)}
                  className={cn("pill", difficulty.includes(level) && "selected")}
                >
                  {DIFFICULTY_LABELS[level]}
                </button>
              ))}
            </div>
          </div>

          <div className="field-grid">
            <div className="field">
              <label>Nursing system</label>
              <Select value={nursingSystem ?? "any"} onValueChange={(v) => handleNursingSystemChange(v === "any" ? null : String(v))}>
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
              <label>Topic</label>
              <Select value={topic ?? "any"} onValueChange={(v) => setTopic(v === "any" ? null : String(v))}>
                <SelectTrigger className="h-[38px] w-full rounded-[10px] border-[color:var(--border)] bg-[#fdfdff] text-[14px]">
                  <SelectValue placeholder="All topics" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">All topics</SelectItem>
                  {topics.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="field">
            <button
              type="button"
              className="flex w-fit items-center gap-1.5 text-[13.5px] font-semibold text-[color:var(--primary)]"
              onClick={() => setShowMoreFilters((v) => !v)}
            >
              {showMoreFilters ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              {showMoreFilters ? "Fewer filters" : "More filters"}
            </button>
          </div>

          {showMoreFilters && (
            <>
              <div className="field-grid">
                <div className="field">
                  <label>NCLEX Client Need</label>
                  <Select value={clientNeed ?? "any"} onValueChange={(v) => setClientNeed(v === "any" ? null : String(v))}>
                    <SelectTrigger className="h-[38px] w-full rounded-[10px] border-[color:var(--border)] bg-[#fdfdff] text-[14px]">
                      <SelectValue placeholder="All client needs" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="any">All client needs</SelectItem>
                      {clientNeeds.map((need) => (
                        <SelectItem key={need} value={need}>
                          {need}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="field">
                  <label>Clinical judgment skill</label>
                  <Select
                    value={clinicalJudgmentSkill ?? "any"}
                    onValueChange={(v) => setClinicalJudgmentSkill(v === "any" ? null : String(v))}
                  >
                    <SelectTrigger className="h-[38px] w-full rounded-[10px] border-[color:var(--border)] bg-[#fdfdff] text-[14px]">
                      <SelectValue placeholder="All skills" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="any">All skills</SelectItem>
                      {clinicalJudgmentSkills.map((skill) => (
                        <SelectItem key={skill} value={skill}>
                          {humanizeEnum(skill)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="pt-1 text-[12px] leading-snug text-[color:var(--muted-fg)]">
                    Most NGN question formats aren't interactive yet — this filters by the clinical judgment skill tagged on
                    each question, MCQ and SATA included.
                  </p>
                </div>
              </div>

              <div className="field">
                <label className="flex items-center gap-2">
                  Timing
                  <span className="soon-badge">Soon</span>
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button type="button" disabled className="type-btn disabled">
                    Untimed
                  </button>
                  <button type="button" disabled className="type-btn disabled">
                    Timed
                  </button>
                </div>
                <p className="pt-1 text-[12px] leading-snug text-[color:var(--muted-fg)]">
                  Coming soon — session timers aren't available yet.
                </p>
              </div>
            </>
          )}

          <div className="divider" />

          <div className="flex flex-col gap-2">
            {matchStatusText && (
              <span
                className={cn(
                  "text-[13px] font-medium",
                  matchingCount === 0 ? "text-[color:var(--destructive)]" : "text-[color:var(--muted-fg)]",
                )}
              >
                {matchStatusText}
              </span>
            )}
            <div className="summary">
              <span className="summary-text">{summaryText}</span>
              <button type="button" className="btn-primary" disabled={startDisabled} onClick={handleStart}>
                Start practice quiz
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
