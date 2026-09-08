/**
 * Tracks the in-progress quiz session's id in sessionStorage — the browser
 * primitive that survives a page refresh but is cleared when the tab/
 * browser actually closes. That distinction is exactly what separates the
 * two resume paths the quiz-taking flow needs:
 *
 *   - A refresh (or a direct reload of /quiz/session) keeps sessionStorage,
 *     so QuizSessionPage can silently re-fetch and resume the same
 *     question, no prompt needed.
 *   - Closing the browser and logging back in clears sessionStorage, so
 *     AppShell's ResumeQuizPrompt falls back to asking the backend (GET
 *     /quizzes/sessions/active/) and — if it finds one — asks the student
 *     whether to continue instead of resuming silently.
 *
 * localStorage would defeat this distinction entirely (it survives a closed
 * browser too); a plain in-memory variable wouldn't survive the refresh
 * case. sessionStorage is the one option that matches both requirements.
 */

const STORAGE_KEY = "nw_active_quiz_session_id";

export function getActiveQuizSessionId(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    // Private-browsing modes etc. can make sessionStorage throw on access —
    // resume is a nice-to-have, never worth crashing the quiz flow over.
    return null;
  }
}

export function setActiveQuizSessionId(sessionId: string): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, sessionId);
  } catch {
    // See getActiveQuizSessionId — losing resume-on-refresh is acceptable,
    // crashing is not.
  }
}

export function clearActiveQuizSessionId(): void {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // See getActiveQuizSessionId.
  }
}
