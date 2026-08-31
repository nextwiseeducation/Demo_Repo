import type { Question } from "@/types/question";
import type { SubmitAnswerResult } from "@/lib/api/questions";

export interface AnswerState {
  selectedChoiceIds: string[];
  submitted: boolean;
  /** Set once SUBMIT_RESULT lands — the backend's verdict, not recomputed client-side (the answer key isn't available client-side until then anyway). */
  isCorrect?: boolean;
}

export interface QuizSessionState {
  questions: Question[];
  currentIndex: number;
  answers: Record<string, AnswerState>;
  /** Question ids the student has "marked for review" (UWorld's Marked flag) — independent of answers. */
  markedIds: Set<string>;
}

type Action =
  | { type: "SELECT_SINGLE"; questionId: string; choiceId: string }
  | { type: "TOGGLE_MULTI"; questionId: string; choiceId: string }
  | { type: "SUBMIT_RESULT"; questionId: string; result: SubmitAnswerResult }
  | { type: "MARK_TOGGLED"; questionId: string; marked: boolean }
  | { type: "NEXT" };

export function createInitialState(questions: Question[]): QuizSessionState {
  return { questions, currentIndex: 0, answers: {}, markedIds: new Set() };
}

export function quizSessionReducer(state: QuizSessionState, action: Action): QuizSessionState {
  switch (action.type) {
    case "SELECT_SINGLE": {
      const existing = state.answers[action.questionId];
      if (existing?.submitted) return state;
      return {
        ...state,
        answers: {
          ...state.answers,
          [action.questionId]: { selectedChoiceIds: [action.choiceId], submitted: false },
        },
      };
    }
    case "TOGGLE_MULTI": {
      const existing = state.answers[action.questionId] ?? { selectedChoiceIds: [], submitted: false };
      if (existing.submitted) return state;
      const isSelected = existing.selectedChoiceIds.includes(action.choiceId);
      const selectedChoiceIds = isSelected
        ? existing.selectedChoiceIds.filter((id) => id !== action.choiceId)
        : [...existing.selectedChoiceIds, action.choiceId];
      return {
        ...state,
        answers: { ...state.answers, [action.questionId]: { selectedChoiceIds, submitted: false } },
      };
    }
    case "SUBMIT_RESULT": {
      const existing = state.answers[action.questionId];
      if (!existing) return state;
      // Merges the revealed answer key into the matching question's
      // answer_choices in place — MCQChoiceList/SATAChoiceList/
      // QuizResultsPage already read choice.is_correct/choice.rationale
      // directly and unconditionally once `submitted` is true, so this is
      // the only place that needs to know those fields start out absent.
      const resultById = new Map(action.result.choices.map((c) => [c.id, c]));
      return {
        ...state,
        answers: {
          ...state.answers,
          [action.questionId]: { ...existing, submitted: true, isCorrect: action.result.is_correct },
        },
        questions: state.questions.map((q) =>
          q.id !== action.questionId
            ? q
            : {
                ...q,
                answer_choices: q.answer_choices.map((c) => ({ ...c, ...resultById.get(c.id) })),
              },
        ),
      };
    }
    case "MARK_TOGGLED": {
      const markedIds = new Set(state.markedIds);
      if (action.marked) markedIds.add(action.questionId);
      else markedIds.delete(action.questionId);
      return { ...state, markedIds };
    }
    case "NEXT":
      return { ...state, currentIndex: Math.min(state.currentIndex + 1, state.questions.length - 1) };
    default:
      return state;
  }
}
