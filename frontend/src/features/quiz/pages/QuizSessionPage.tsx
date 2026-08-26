import { useReducer } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { MCQChoiceList } from "@/features/quiz/components/MCQChoiceList";
import { QuestionCard } from "@/features/quiz/components/QuestionCard";
import { QuizProgressBar } from "@/features/quiz/components/QuizProgressBar";
import { SATAChoiceList } from "@/features/quiz/components/SATAChoiceList";
import { UnsupportedQuestionTypeNotice } from "@/features/quiz/components/UnsupportedQuestionTypeNotice";
import { createInitialState, isAnswerCorrect, quizSessionReducer } from "@/features/quiz/quizSessionReducer";
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

  return <QuizSessionInner questions={state.questions} />;
}

function QuizSessionInner({ questions }: { questions: Question[] }) {
  const navigate = useNavigate();
  const [session, dispatch] = useReducer(quizSessionReducer, createInitialState(questions));

  const question = session.questions[session.currentIndex];
  const answer = session.answers[question.id];
  const submitted = answer?.submitted ?? false;
  const selectedIds = answer?.selectedChoiceIds ?? [];
  const isLastQuestion = session.currentIndex === session.questions.length - 1;
  const isSupported = question.question_type === "MCQ" || question.question_type === "SATA";

  function goNextOrFinish() {
    if (isLastQuestion) {
      const responses: QuestionResponse[] = session.questions.map((q) => {
        const a = session.answers[q.id];
        return {
          question_id: q.id,
          selected_choice_ids: a?.selectedChoiceIds ?? [],
          is_correct: a ? isAnswerCorrect(q, a.selectedChoiceIds) : false,
        };
      });
      navigate(ROUTES.quizResults, { state: { questions: session.questions, responses } });
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

      {isSupported && (
        <div className="actions">
          {!submitted ? (
            <>
              <span className="hint">A rationale for every option appears after you submit.</span>
              <button
                type="button"
                className="btn-primary"
                disabled={selectedIds.length === 0}
                onClick={() => dispatch({ type: "SUBMIT", questionId: question.id })}
              >
                Submit answer
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
