import type { Question } from "@/types/question";
import type { StructuredAnswer } from "@/types/quiz";
import type { SubmitAnswerResult } from "@/lib/api/questions";

export interface AnswerState {
  /** MCQ / SATA / EMR only. */
  selectedChoiceIds: string[];
  /** MATRIX / BOWTIE / CLOZE / DRAG_DROP / HOTSPOT only. */
  structuredAnswer?: StructuredAnswer;
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
  | { type: "SET_STRUCTURED_ANSWER"; questionId: string; answer: StructuredAnswer }
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
    case "SET_STRUCTURED_ANSWER": {
      const existing = state.answers[action.questionId];
      if (existing?.submitted) return state;
      return {
        ...state,
        answers: {
          ...state.answers,
          [action.questionId]: { selectedChoiceIds: [], structuredAnswer: action.answer, submitted: false },
        },
      };
    }
    case "SUBMIT_RESULT": {
      const existing = state.answers[action.questionId];
      if (!existing) return state;
      const result = action.result;

      return {
        ...state,
        answers: {
          ...state.answers,
          [action.questionId]: { ...existing, submitted: true, isCorrect: result.is_correct },
        },
        questions: state.questions.map((q) => {
          if (q.id !== action.questionId) return q;

          // Merges whichever answer key came back into this question's own
          // matching collection, in place — the same "starts undefined,
          // filled in once revealed" pattern QuestionCard/MCQChoiceList/
          // SATAChoiceList already read from answer_choices directly.
          if (result.choices) {
            const byId = new Map(result.choices.map((c) => [c.id, c]));
            return { ...q, answer_choices: q.answer_choices.map((c) => ({ ...c, ...byId.get(c.id) })) };
          }
          if (result.matrix_cells) {
            return { ...q, matrix_cells: result.matrix_cells };
          }
          if (result.bowtie_options) {
            const byId = new Map(result.bowtie_options.map((o) => [o.id, o]));
            return { ...q, bowtie_options: q.bowtie_options.map((o) => ({ ...o, ...byId.get(o.id) })) };
          }
          if (result.cloze_blanks) {
            const byBlankId = new Map(result.cloze_blanks.map((b) => [b.blank_id, b]));
            return {
              ...q,
              cloze_blanks: q.cloze_blanks.map((blank) => {
                const revealed = byBlankId.get(blank.id);
                if (!revealed) return blank;
                const byOptionId = new Map(revealed.options.map((o) => [o.id, o]));
                return { ...blank, options: blank.options.map((o) => ({ ...o, ...byOptionId.get(o.id) })) };
              }),
            };
          }
          if (result.dragdrop_items) {
            const byId = new Map(result.dragdrop_items.map((i) => [i.id, i]));
            return { ...q, dragdrop_items: q.dragdrop_items.map((i) => ({ ...i, ...byId.get(i.id) })) };
          }
          if (result.hotspot_targets) {
            const byId = new Map(result.hotspot_targets.map((t) => [t.id, t]));
            return { ...q, hotspot_targets: q.hotspot_targets.map((t) => ({ ...t, ...byId.get(t.id) })) };
          }
          return q;
        }),
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
