import { useMutation } from "@tanstack/react-query";
import { Bookmark, BookmarkCheck } from "lucide-react";
import { useEffect, useReducer, useRef } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { BowTieQuestion } from "@/features/quiz/components/BowTieQuestion";
import { ClozeQuestion } from "@/features/quiz/components/ClozeQuestion";
import { DragDropQuestion, type DragDropPlacement } from "@/features/quiz/components/DragDropQuestion";
import { EMRChoiceList } from "@/features/quiz/components/EMRChoiceList";
import { HotSpotQuestion } from "@/features/quiz/components/HotSpotQuestion";
import { MatrixQuestion } from "@/features/quiz/components/MatrixQuestion";
import { MCQChoiceList } from "@/features/quiz/components/MCQChoiceList";
import { QuestionCard } from "@/features/quiz/components/QuestionCard";
import { QuestionFeedbackBar } from "@/features/quiz/components/QuestionFeedbackBar";
import { QuizProgressBar } from "@/features/quiz/components/QuizProgressBar";
import { SATAChoiceList } from "@/features/quiz/components/SATAChoiceList";
import { UnsupportedQuestionTypeNotice } from "@/features/quiz/components/UnsupportedQuestionTypeNotice";
import { createInitialState, quizSessionReducer, type AnswerState } from "@/features/quiz/quizSessionReducer";
import * as quizzesApi from "@/lib/api/quizzes";
import { ROUTES } from "@/lib/constants";
import { effectiveQuestionType, SUPPORTED_QUESTION_TYPES, type Question } from "@/types/question";
import type { QuestionResponse, QuizSession as QuizSessionData, StructuredAnswer } from "@/types/quiz";

interface LocationState {
  session: QuizSessionData;
}

export function QuizSessionPage() {
  const location = useLocation();
  const state = location.state as LocationState | null;

  // The session itself now lives server-side (a real QuizSession +
  // StudentResponseLog rows, written as each answer is submitted below) —
  // what's carried here is just the already-created session's id +
  // ordered questions, handed off from QuizSetupPage's "Generate Quiz".
  // There's no GET-by-id endpoint yet, so a direct refresh/link still has
  // nothing to resume from and bounces to setup, same as before.
  if (!state?.session?.questions?.length) {
    return <Navigate to={ROUTES.quizSetup} replace />;
  }

  return <QuizSessionInner quizSession={state.session} />;
}

/**
 * Whether `answer` is complete enough to submit, for the given question's
 * effective type — gates the Submit button. Matrix and Cloze require every
 * row/blank to be answered (a partial grid or sentence isn't a real
 * attempt); the others only require at least one selection, matching
 * MCQ/SATA's existing "something is selected" bar.
 */
function hasAnswer(question: Question, answer: AnswerState | undefined): boolean {
  if (!answer) return false;
  const type = effectiveQuestionType(question);
  if (type === "MCQ" || type === "SATA" || type === "EMR") return answer.selectedChoiceIds.length > 0;

  const sa = answer.structuredAnswer;
  if (!sa) return false;
  switch (sa.kind) {
    case "MATRIX":
      return question.matrix_rows.every((row) => sa.selections.some((s) => s.row_id === row.id));
    case "BOWTIE":
      return sa.selectedOptionIds.length > 0;
    case "CLOZE":
      return question.cloze_blanks.every((blank) => sa.selections.some((s) => s.blank_id === blank.id));
    case "DRAG_DROP":
      return sa.placements.length > 0;
    case "HOTSPOT":
      return sa.selectedTargetIds.length > 0;
    default:
      return false;
  }
}

/**
 * Whether this question actually has answer data to render, for its
 * effective type — false for a question whose type is fully supported but
 * whose own content is incomplete (e.g. an NGN Case Study item authored
 * with its options as inline stem text rather than structured choices; see
 * import_ngn_item_bank.py's "KNOWN LIMITATION" docstring). Gates isSupported
 * below so that case lands on the skippable notice instead of an
 * interactive-looking component with nothing in it and a Submit button that
 * can never become enabled.
 */
function hasRenderableData(question: Question): boolean {
  switch (effectiveQuestionType(question)) {
    case "MCQ":
    case "SATA":
    case "EMR":
      return question.answer_choices.length > 0;
    case "MATRIX":
      return question.matrix_rows.length > 0 && question.matrix_columns.length > 0;
    case "BOWTIE":
      return question.bowtie_options.length > 0;
    case "CLOZE":
      return question.cloze_blanks.length > 0;
    case "DRAG_DROP":
      return question.dragdrop_items.length > 0;
    case "HOTSPOT":
      return question.hotspot_targets.length > 0;
    default:
      return false;
  }
}

/** Builds the one populated field submitSessionAnswer needs, from whichever answer shape this question's effective type uses. */
function buildSubmitFields(question: Question, answer: AnswerState) {
  const type = effectiveQuestionType(question);
  if (type === "MCQ" || type === "SATA" || type === "EMR") {
    return { selectedChoiceIds: answer.selectedChoiceIds };
  }
  const sa = answer.structuredAnswer;
  switch (sa?.kind) {
    case "MATRIX":
      return { matrixSelections: sa.selections };
    case "BOWTIE":
      return { bowtieOptionIds: sa.selectedOptionIds };
    case "CLOZE":
      return { clozeSelections: sa.selections };
    case "DRAG_DROP":
      return { dragdropPlacements: sa.placements };
    case "HOTSPOT":
      return { hotspotTargetIds: sa.selectedTargetIds };
    default:
      return {};
  }
}

function QuizSessionInner({ quizSession }: { quizSession: QuizSessionData }) {
  const navigate = useNavigate();
  const [session, dispatch] = useReducer(quizSessionReducer, createInitialState(quizSession.questions));
  // Wall-clock start of this session — diffed at finish to report total
  // time spent to the results page. A ref (not state) since it's write-once
  // and reading it never needs to trigger a re-render.
  const startedAtRef = useRef(Date.now());
  // Wall-clock start of the *currently displayed* question — reset below
  // whenever currentIndex changes. Separate from startedAtRef (total-quiz
  // timer) on purpose: this is purely "when did this question first render",
  // orthogonal to answer/session state, so it lives outside the reducer.
  const questionStartedAtRef = useRef(Date.now());
  // Captured once, synchronously, at the moment "Submit answer" is clicked —
  // not recomputed on later re-renders, so it doesn't keep growing while the
  // feedback bar sits on screen or the student lingers before "Next question".
  const questionTimeSpentRef = useRef(0);

  const question = session.questions[session.currentIndex];
  const answer = session.answers[question.id];
  const submitted = answer?.submitted ?? false;
  const selectedIds = answer?.selectedChoiceIds ?? [];
  const structuredAnswer = answer?.structuredAnswer;
  const isLastQuestion = session.currentIndex === session.questions.length - 1;
  const effectiveType = effectiveQuestionType(question);
  const isTypeSupported = SUPPORTED_QUESTION_TYPES.includes(effectiveType);
  const isSupported = isTypeSupported && hasRenderableData(question);
  const isMarked = session.markedIds.has(question.id);
  // Test Mode's Tutor toggle (quiz-setup page) — when off, the correct
  // answer/rationale bar stays hidden after each question, matching
  // UWorld's actual Tutor-vs-not distinction.
  const showFeedbackBar = quizSession.filter_config.is_tutor_mode;

  useEffect(() => {
    questionStartedAtRef.current = Date.now();
  }, [session.currentIndex]);

  const submitMutation = useMutation({
    mutationFn: ({ questionId, answer }: { questionId: string; answer: AnswerState }) =>
      quizzesApi.submitSessionAnswer(quizSession.id, {
        questionId,
        timeTakenSeconds: questionTimeSpentRef.current,
        ...buildSubmitFields(question, answer),
      }),
    onSuccess: (result, { questionId }) => dispatch({ type: "SUBMIT_RESULT", questionId, result }),
  });

  const bookmarkMutation = useMutation({
    mutationFn: () => quizzesApi.toggleBookmark(question.id),
    onSuccess: (result) => dispatch({ type: "MARK_TOGGLED", questionId: question.id, marked: result.marked }),
  });

  // Running accuracy across every question submitted so far this session
  // (including the one just answered) — no reducer plumbing needed, this
  // folds straight out of session.answers.
  const answeredSoFar = Object.values(session.answers).filter((a) => a.submitted);
  const correctSoFar = answeredSoFar.filter((a) => a.isCorrect).length;
  const accuracyPercent =
    answeredSoFar.length > 0 ? Math.round((correctSoFar / answeredSoFar.length) * 100) : 0;

  function goNextOrFinish() {
    if (isLastQuestion) {
      // By now every answered question already has its answer key merged
      // into session.questions (see quizSessionReducer's SUBMIT_RESULT) —
      // a.isCorrect is the backend's own verdict from that same response,
      // not recomputed here.
      const responses: QuestionResponse[] = session.questions.map((q) => {
        const a = session.answers[q.id];
        return {
          question_id: q.id,
          selected_choice_ids: a?.selectedChoiceIds ?? [],
          structured_answer: a?.structuredAnswer,
          is_correct: a?.isCorrect ?? false,
        };
      });
      const totalTimeSeconds = Math.round((Date.now() - startedAtRef.current) / 1000);
      navigate(ROUTES.quizResults, {
        state: { questions: session.questions, responses, totalTimeSeconds },
      });
      return;
    }
    dispatch({ type: "NEXT" });
  }

  function setStructuredAnswer(next: StructuredAnswer) {
    dispatch({ type: "SET_STRUCTURED_ANSWER", questionId: question.id, answer: next });
  }

  function renderQuestionBody() {
    switch (effectiveType) {
      case "MCQ":
        return (
          <MCQChoiceList
            choices={question.answer_choices}
            selectedId={selectedIds[0] ?? null}
            submitted={submitted}
            onSelect={(choiceId) => dispatch({ type: "SELECT_SINGLE", questionId: question.id, choiceId })}
          />
        );
      case "SATA":
        return (
          <SATAChoiceList
            choices={question.answer_choices}
            selectedIds={selectedIds}
            submitted={submitted}
            onToggle={(choiceId) => dispatch({ type: "TOGGLE_MULTI", questionId: question.id, choiceId })}
          />
        );
      case "EMR":
        return (
          <EMRChoiceList
            choices={question.answer_choices}
            selectedIds={selectedIds}
            submitted={submitted}
            onToggle={(choiceId) => dispatch({ type: "TOGGLE_MULTI", questionId: question.id, choiceId })}
          />
        );
      case "MATRIX": {
        const selections = structuredAnswer?.kind === "MATRIX" ? structuredAnswer.selections : [];
        return (
          <MatrixQuestion
            rows={question.matrix_rows}
            columns={question.matrix_columns}
            selections={selections}
            submitted={submitted}
            cellResults={question.matrix_cells}
            onSelect={(rowId, columnId) =>
              setStructuredAnswer({
                kind: "MATRIX",
                selections: [...selections.filter((s) => s.row_id !== rowId), { row_id: rowId, column_id: columnId }],
              })
            }
          />
        );
      }
      case "BOWTIE": {
        const selectedOptionIds = structuredAnswer?.kind === "BOWTIE" ? structuredAnswer.selectedOptionIds : [];
        return (
          <BowTieQuestion
            options={question.bowtie_options}
            selectedOptionIds={selectedOptionIds}
            submitted={submitted}
            onToggle={(optionId) =>
              setStructuredAnswer({
                kind: "BOWTIE",
                selectedOptionIds: selectedOptionIds.includes(optionId)
                  ? selectedOptionIds.filter((id) => id !== optionId)
                  : [...selectedOptionIds, optionId],
              })
            }
          />
        );
      }
      case "CLOZE": {
        const selections = structuredAnswer?.kind === "CLOZE" ? structuredAnswer.selections : [];
        return (
          <ClozeQuestion
            stem={question.stem}
            blanks={question.cloze_blanks}
            selections={selections}
            submitted={submitted}
            onSelect={(blankId, optionId) =>
              setStructuredAnswer({
                kind: "CLOZE",
                selections: [...selections.filter((s) => s.blank_id !== blankId), { blank_id: blankId, option_id: optionId }],
              })
            }
          />
        );
      }
      case "DRAG_DROP": {
        const placements: DragDropPlacement[] = structuredAnswer?.kind === "DRAG_DROP" ? structuredAnswer.placements : [];
        return (
          <DragDropQuestion
            items={question.dragdrop_items}
            categories={question.dragdrop_categories}
            placements={placements}
            submitted={submitted}
            onChange={(next) => setStructuredAnswer({ kind: "DRAG_DROP", placements: next })}
          />
        );
      }
      case "HOTSPOT": {
        const selectedTargetIds = structuredAnswer?.kind === "HOTSPOT" ? structuredAnswer.selectedTargetIds : [];
        return (
          <HotSpotQuestion
            clinicalScenario={question.case_study?.shared_scenario ?? question.clinical_scenario}
            stem={question.stem}
            targets={question.hotspot_targets}
            selectedTargetIds={selectedTargetIds}
            submitted={submitted}
            onToggle={(targetId) =>
              setStructuredAnswer({
                kind: "HOTSPOT",
                selectedTargetIds: selectedTargetIds.includes(targetId)
                  ? selectedTargetIds.filter((id) => id !== targetId)
                  : [...selectedTargetIds, targetId],
              })
            }
          />
        );
      }
      default:
        return null;
    }
  }

  return (
    <div className="page page-wide">
      <div className="flex items-center justify-between gap-3">
        <QuizProgressBar currentIndex={session.currentIndex} total={session.questions.length} question={question} />
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={bookmarkMutation.isPending}
          onClick={() => bookmarkMutation.mutate()}
        >
          {isMarked ? <BookmarkCheck className="h-4 w-4 text-primary" /> : <Bookmark className="h-4 w-4" />}
          {isMarked ? "Marked" : "Mark for review"}
        </Button>
      </div>

      {isSupported ? (
        <QuestionCard
          question={question}
          questionNumber={session.currentIndex + 1}
          hideStem={effectiveType === "HOTSPOT" || effectiveType === "CLOZE"}
          hideScenario={effectiveType === "HOTSPOT"}
        >
          {renderQuestionBody()}
        </QuestionCard>
      ) : (
        <UnsupportedQuestionTypeNotice
          questionType={effectiveType}
          onSkip={goNextOrFinish}
          reason={isTypeSupported ? "MISSING_CONTENT" : "TYPE_NOT_SUPPORTED"}
        />
      )}

      {isSupported && submitted && showFeedbackBar && (
        <QuestionFeedbackBar
          isCorrect={answer?.isCorrect ?? false}
          accuracyPercent={accuracyPercent}
          timeSpentSeconds={questionTimeSpentRef.current}
          updatedAt={question.updated_at}
        />
      )}

      {isSupported && (
        <div className="actions">
          {!submitted ? (
            <>
              <span className="hint">A rationale for every option appears after you submit.</span>
              <button
                type="button"
                className="btn-primary"
                disabled={!hasAnswer(question, answer) || submitMutation.isPending}
                onClick={() => {
                  if (!answer) return;
                  questionTimeSpentRef.current = Math.round((Date.now() - questionStartedAtRef.current) / 1000);
                  submitMutation.mutate({ questionId: question.id, answer });
                }}
              >
                {submitMutation.isPending ? "Submitting..." : "Submit answer"}
              </button>
            </>
          ) : (
            <button type="button" className="btn-primary" style={{ marginLeft: "auto" }} onClick={goNextOrFinish}>
              {isLastQuestion ? "See results" : "Next question"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
