import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Textarea } from "@/components/ui/textarea";
import { submitQuestionIssueReport } from "@/lib/api/feedback";
import { QUESTION_ISSUE_TYPE_LABELS, type QuestionIssueType } from "@/types/feedback";

const ISSUE_TYPES = Object.keys(QUESTION_ISSUE_TYPE_LABELS) as QuestionIssueType[];

interface ReportIssueDialogProps {
  questionStem: string;
  questionNumber?: number;
}

/**
 * Lets a student flag a problem with a question the moment they see it,
 * instead of having to remember its number for the end-of-quiz survey.
 * question_stem_snapshot (not a Question id) is what's sent today, since
 * the quiz-taking flow still runs on mock questions with no real backend
 * row to reference — see types/feedback.ts.
 */
export function ReportIssueDialog({ questionStem, questionNumber }: ReportIssueDialogProps) {
  const [open, setOpen] = useState(false);
  const [issueType, setIssueType] = useState<QuestionIssueType | null>(null);
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [attemptedSubmit, setAttemptedSubmit] = useState(false);

  function reset() {
    setIssueType(null);
    setDescription("");
    setAttemptedSubmit(false);
  }

  async function handleSubmit() {
    if (!issueType) {
      setAttemptedSubmit(true);
      return;
    }
    setSubmitting(true);
    try {
      await submitQuestionIssueReport({
        question_stem_snapshot: questionStem,
        question_number_in_quiz: questionNumber,
        issue_type: issueType,
        description: description.trim() || undefined,
      });
      toast.success("Thanks — we'll take a look.");
      reset();
      setOpen(false);
    } catch {
      toast.error("Couldn't submit your report. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) reset();
      }}
    >
      <DialogTrigger
        render={
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
          />
        }
      >
        <span aria-hidden="true">🚩</span>
        Report an issue
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Report an issue</DialogTitle>
          <DialogDescription>
            {questionNumber ? `Question ${questionNumber} — ` : ""}
            let us know what's wrong and we'll take a look.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-1">
          <RadioGroup value={issueType ?? ""} onValueChange={(v) => setIssueType(v as QuestionIssueType)}>
            {ISSUE_TYPES.map((key) => (
              <div key={key} className="group/field-label flex items-center gap-2">
                <RadioGroupItem id={`issue-type-${key}`} value={key} />
                <Label htmlFor={`issue-type-${key}`} className="font-normal">
                  {QUESTION_ISSUE_TYPE_LABELS[key]}
                </Label>
              </div>
            ))}
          </RadioGroup>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="issue-report-description">Details (optional)</Label>
            <Textarea
              id="issue-report-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Anything specific we should know?"
            />
          </div>

          {attemptedSubmit && !issueType && (
            <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              Please select what the issue is.
            </p>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? "Submitting…" : "Submit report"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
