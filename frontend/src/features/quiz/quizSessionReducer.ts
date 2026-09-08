import type { Question } from "@/types/question";
import type { QuizSession, SessionResponseSummary, StructuredAnswer } from "@/types/quiz";
import type { SubmitAnswerResult } from "@/lib/api/questions";

export interface AnswerState {
  /** MCQ / SATA / EMR only. */
  selectedChoiceIds: string[];
  /** MATRIX / BOWTIE / CLOZE / DRAG_DROP / HOTSPOT only. */
  structuredAnswer?: StructuredAnswer;
  submitted: boolean;
  /** Set once SUBMIT_RESULT lands (or hydrated from a prior session — see createInitialState) — the backend's verdict, not recomputed client-side. */
  isCorrect?: boolean;
}

export interface QuizSessionState {
  questions: Question[];
  currentIndex: number;
  answers: Record<string, AnswerState>;
  /** Question ids the student has "marked for review" (UWorld's Marked flag) — independent of answers. */
  markedIds: Set<string>;
  /**
   * Question ids the student has actually been shown in this session,
   * answered or not — what separates "skipped" (visited, still no answer)
   * from "not reached yet" in the question navigator. Persisted server-side
   * via QuizSessionPositionView so it survives a refresh/resume, not just
   * kept client-side.
   */
  visitedIds: Set<string>;
}

type AnswerKeyPayload = SubmitAnswerResult | Omit<SessionResponseSummary, "question_id" | "is_correct" | "selected_choice_ids" | "structured_answer">;

/**
 * Merges whichever answer key fields are present on `result` into the one
 * matching question, in place — the "starts undefined, filled in once
 * revealed" pattern QuestionCard/MCQChoiceList/SATAChoiceList already read
 * from answer_choices etc. directly. Shared by SUBMIT_RESULT (a just-graded
 * answer) and createInitialState (bulk-hydrating every already-answered
 * question from QuizSession.responses on load/resume) so the two can't
 * drift on how a revealed key gets merged in.
 */
function mergeAnswerKeyIntoQuestion(question: Question, result: AnswerKeyPayload): Question {
  if (result.choices) {
    const byId = new Map(result.choices.map((c) => [c.id, c]));
    return { ...question, answer_choices: question.answer_choices.map((c) => ({ ...c, ...byId.get(c.id) })) };
  }
  if (result.matrix_cells) {
    return { ...question, matrix_cells: result.matrix_cells };
  }
  if (result.bowtie_options) {
    const byId = new Map(result.bowtie_options.map((o) => [o.id, o]));
    return { ...question, bowtie_options: question.bowtie_options.map((o) => ({ ...o, ...byId.get(o.id) })) };
  }
  if (result.cloze_blanks) {
    const byBlankId = new Map(result.cloze_blanks.map((b) => [b.blank_id, b]));
    return {
      ...question,
      cloze_blanks: question.cloze_blanks.map((blank) => {
        const revealed = byBlankId.get(blank.id);
        if (!revealed) return blank;
        const byOptionId = new Map(revealed.options.map((o) => [o.id, o]));
        return { ...blank, options: blank.options.map((o) => ({ ...o, ...byOptionId.get(o.id) })) };
      }),
    };
  }
  if (result.dragdrop_items) {
    const byId = new Map(result.dragdrop_items.map((i) => [i.id, i]));
    return { ...question, dragdrop_items: question.dragdrop_items.map((i) => ({ ...i, ...byId.get(i.id) })) };
  }
  if (result.hotspot_targets) {
    const byId = new Map(result.hotspot_targets.map((t) => [t.id, t]));
    return { ...question, hotspot_targets: question.hotspot_targets.map((t) => ({ ...t, ...byId.get(t.id) })) };
  }
  return question;
}

type Action =
  | { type: "SELECT_SINGLE"; questionId: string; choiceId: string }
  | { type: "TOGGLE_MULTI"; questionId: string; choiceId: string }
  | { type: "SET_STRUCTURED_ANSWER"; questionId: string; answer: StructuredAnswer }
  | { type: "SUBMIT_RESULT"; questionId: string; result: SubmitAnswerResult }
  | { type: "MARK_TOGGLED"; questionId: string; marked: boolean }
  | { type: "GOTO"; index: number };

/**
 * Builds the reducer's starting state directly from a QuizSession as the
 * backend hands it over — whether that's a freshly-created session (no
 * prior answers/visits/marks), a same-tab refresh, or a resume after
 * login. Hydrating everything here in one shot (rather than dispatching
 * follow-up actions after mount) means a question the student already
 * answered renders in its final, locked-in, rationale-revealed state
 * immediately, with no flash of the unanswered form first.
 */
export function createInitialState(session: QuizSession): QuizSessionState {
  const answers: Record<string, AnswerState> = {};
  let questions = session.questions;

  for (const response of session.responses) {
    questions = questions.map((q) => (q.id === response.question_id ? mergeAnswerKeyIntoQuestion(q, response) : q));
    answers[response.question_id] = {
      selectedChoiceIds: response.selected_choice_ids,
      structuredAnswer: response.structured_answer ?? undefined,
      submitted: true,
      isCorrect: response.is_correct,
    };
  }

  const currentIndex = Math.min(Math.max(session.current_question_index, 0), Math.max(questions.length - 1, 0));
  const visitedIds = new Set(session.visited_question_ids);
  // The question about to be displayed counts as visited even if the
  // server hasn't recorded it yet (e.g. the very first question of a
  // brand-new session, before QuizSessionPage's position effect has fired).
  const currentQuestionId = questions[currentIndex]?.id;
  if (currentQuestionId) visitedIds.add(currentQuestionId);

  return {
    questions,
    currentIndex,
    answers,
    markedIds: new Set(session.marked_question_ids),
    visitedIds,
  };
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
        questions: state.questions.map((q) => (q.id === action.questionId ? mergeAnswerKeyIntoQuestion(q, result) : q)),
      };
    }
    case "MARK_TOGGLED": {
      const markedIds = new Set(state.markedIds);
      if (action.marked) markedIds.add(action.questionId);
      else markedIds.delete(action.questionId);
      return { ...state, markedIds };
    }
    case "GOTO": {
      const currentIndex = Math.min(Math.max(action.index, 0), state.questions.length - 1);
      const questionId = state.questions[currentIndex]?.id;
      const visitedIds = new Set(state.visitedIds);
      if (questionId) visitedIds.add(questionId);
      return { ...state, currentIndex, visitedIds };
    }
    default:
      return state;
  }
}
