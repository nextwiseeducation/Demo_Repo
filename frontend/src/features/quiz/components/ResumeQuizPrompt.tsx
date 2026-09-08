import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { getActiveQuizSessionId, setActiveQuizSessionId } from "@/lib/activeQuizSession";
import * as quizzesApi from "@/lib/api/quizzes";
import { ROUTES } from "@/lib/constants";

/**
 * "Would you like to continue the quiz you left?" — mounted once in
 * AppShell, so it runs once per real app load for every protected route.
 *
 * Deliberately only checks the backend when sessionStorage has no active
 * session id already: if it does, that same tab already knows which
 * session it's mid-quiz on (see lib/activeQuizSession.ts) — that's the
 * plain-refresh case, which QuizSessionPage resumes silently, no prompt.
 * This prompt exists for the OTHER case: sessionStorage was cleared because
 * the browser actually closed, but the server still has an unfinished
 * session — recoverable only by asking, since a silent auto-resume here
 * would drop the student back into a quiz they may not even remember
 * starting.
 */
export function ResumeQuizPrompt() {
  const navigate = useNavigate();
  const [dismissed, setDismissed] = useState(false);

  const activeQuery = useQuery({
    queryKey: ["quiz-active-session"],
    queryFn: () => quizzesApi.getActiveQuizSession(),
    enabled: !getActiveQuizSessionId(),
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const abandonMutation = useMutation({
    mutationFn: (sessionId: string) => quizzesApi.abandonQuizSession(sessionId),
    onSuccess: () => {
      toast.success("Previous quiz progress was not saved.");
      setDismissed(true);
    },
    onError: () => {
      toast.error("Couldn't discard the previous quiz — please try again.");
    },
  });

  const session = activeQuery.data?.session ?? null;
  const open = Boolean(session) && !dismissed;

  if (!session) return null;

  function handleContinue() {
    if (!session) return;
    setActiveQuizSessionId(session.id);
    setDismissed(true);
    navigate(ROUTES.quizSession, { state: { session } });
  }

  function handleDiscard() {
    if (!session) return;
    abandonMutation.mutate(session.id);
  }

  return (
    // Forced choice, same reasoning as QuizFeedbackModal: this decision
    // ("keep the previous attempt or let it go") shouldn't be dismissible
    // via Escape or an outside click — that would leave the state genuinely
    // ambiguous both to the student and to future logins on this account.
    <Dialog open={open} onOpenChange={() => {}} disablePointerDismissal>
      <DialogContent showCloseButton={false}>
        <DialogHeader>
          <DialogTitle>Continue your last quiz?</DialogTitle>
          <DialogDescription>
            You have a practice quiz in progress ({session.current_question_index}/{session.questions.length}{" "}
            questions answered). Would you like to continue where you left off? If you select No, this quiz's
            progress will not be saved.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={handleDiscard} disabled={abandonMutation.isPending}>
            No
          </Button>
          <Button onClick={handleContinue} disabled={abandonMutation.isPending}>
            Yes, continue
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
