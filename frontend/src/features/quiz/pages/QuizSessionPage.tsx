import { useMutation } from "@tanstack/react-query";
import { useEffect, useReducer, useRef } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { MCQChoiceList } from "@/features/quiz/components/MCQChoiceList";
import { QuestionCard } from "@/features/quiz/components/QuestionCard";
import { QuestionFeedbackBar } from "@/features/quiz/components/QuestionFeedbackBar";
import { QuizProgressBar } from "@/features/quiz/components/QuizProgressBar";
import { SATAChoiceList } from "@/features/quiz/components/SATAChoiceList";
import { UnsupportedQuestionTypeNotice } from "@/features/quiz/components/UnsupportedQuestionTypeNotice";
import { createInitialState, quizSessionReducer } from "@/features/quiz/quizSessionReducer";
import * as questionsApi from "@/lib/api/questions";
import { ROUTES } from "@/lib/constants";
import type { Question } from "@/types/question";
import type { QuestionResponse, QuizFilterConfig } from "@/types/quiz";

interface LocationState {
  questions: Question[];
  filterConfig: QuizFilterConfig;
}

export function QuizSessionPage() {
  const location = useLocation();
  const state = location.state as LocationState | null;

  // Session config lives only in router state (nothing is persisted for
  // this mock feature) — a direct refresh/link here has nothing to resume.
  if (!state?.questions?.length) {
    return <Navigate to={ROUTES.quizSetup} replace />;
  }

  return <QuizSessionInner questions={state.questions} filterConfig={state.filterConfig} />;
}

function QuizSessionInner({ questions, filterConfig }: { questions: Question[]; filterConfig: QuizFilterConfig }) {
  const navigate = useNavigate();
  const [session, dispatch] = useReducer(quizSessionReducer, createInitialState(questions));
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
  const isLastQuestion = session.currentIndex === session.questions.length - 1;
  const isSupported = question.question_type === "MCQ" || question.question_type === "SATA";

  useEffect(() => {
    questionStartedAtRef.current = Date.now();
  }, [session.currentIndex]);

  const submitMutation = useMutation({
    mutationFn: ({ questionId, selectedChoiceIds }: { questionId: string; selectedChoiceIds: string[] }) =>
      questionsApi.submitAnswer(questionId, selectedChoiceIds),
    onSuccess: (result, { questionId }) => dispatch({ type: "SUBMIT_RESULT", questionId, result }),
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
          is_correct: a?.isCorrect ?? false,
        };
      });
      const totalTimeSeconds = Math.round((Date.now() - startedAtRef.current) / 1000);
      navigate(ROUTES.quizResults, {
        state: { questions: session.questions, responses, filterConfig, totalTimeSeconds },
      });
      return;
    }
    dispatch({ type: "NEXT" });
  }

  return (
    <div className="page">
      <QuizProgressBar currentIndex={session.currentIndex} total={session.questions.length} question={question} />

      {isSupported ? (
        <QuestionCard question={question} questionNumber={session.currentIndex + 1}>
          {question.question_type === "MCQ" ? (
            <MCQChoiceList
              choices={question.answer_choices}
              selectedId={selectedIds[0] ?? null}
              submitted={submitted}
              onSelect={(choiceId) => dispatch({ type: "SELECT_SINGLE", questionId: question.id, choiceId })}
            />
          ) : (
            <SATAChoiceList
              choices={question.answer_choices}
              selectedIds={selectedIds}
              submitted={submitted}
              onToggle={(choiceId) => dispatch({ type: "TOGGLE_MULTI", questionId: question.id, choiceId })}
            />
          )}
        </QuestionCard>
      ) : (
        <UnsupportedQuestionTypeNotice questionType={question.question_type} onSkip={goNextOrFinish} />
      )}

      {isSupported && submitted && (
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
                disabled={selectedIds.length === 0 || submitMutation.isPending}
                onClick={() => {
                  questionTimeSpentRef.current = Math.round((Date.now() - questionStartedAtRef.current) / 1000);
                  submitMutation.mutate({ questionId: question.id, selectedChoiceIds: selectedIds });
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
