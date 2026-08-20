import type { Question } from "@/types/question";

export interface AnswerState {
  selectedChoiceIds: string[];
  submitted: boolean;
}

export interface QuizSessionState {
  questions: Question[];
  currentIndex: number;
  answers: Record<string, AnswerState>;
}

type Action =
  | { type: "SELECT_SINGLE"; questionId: string; choiceId: string }
  | { type: "TOGGLE_MULTI"; questionId: string; choiceId: string }
  | { type: "SUBMIT"; questionId: string }
  | { type: "NEXT" };

export function createInitialState(questions: Question[]): QuizSessionState {
  return { questions, currentIndex: 0, answers: {} };
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
    case "SUBMIT": {
      const existing = state.answers[action.questionId];
      if (!existing) return state;
      return {
        ...state,
        answers: { ...state.answers, [action.questionId]: { ...existing, submitted: true } },
      };
    }
    case "NEXT":
      return { ...state, currentIndex: Math.min(state.currentIndex + 1, state.questions.length - 1) };
    default:
      return state;
  }
}

/**
 * Simplest defensible SATA rule: the selected set must exactly match the
 * correct set. The schema has no partial-credit field, so this should be
 * validated against Milestone 3's real grading logic once it exists rather
 * than assumed to match production.
 */
export function isAnswerCorrect(question: Question, selectedChoiceIds: string[]): boolean {
  const correctIds = question.answer_choices.filter((c) => c.is_correct).map((c) => c.id).sort();
  const selectedSorted = [...selectedChoiceIds].sort();
  return correctIds.length === selectedSorted.length && correctIds.every((id, i) => id === selectedSorted[i]);
}
