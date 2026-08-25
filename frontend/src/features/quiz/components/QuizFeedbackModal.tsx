import type { ReactNode } from "react";
import { useState } from "react";
import { toast } from "sonner";

import { StarRating } from "@/components/common/StarRating";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Textarea } from "@/components/ui/textarea";
import { submitQuizFeedback } from "@/lib/api/feedback";
import {
  DIFFICULTY_RATING_LABELS,
  REALISM_RATING_LABELS,
  RECOMMEND_LIKELIHOOD_LABELS,
  type DifficultyRating,
  type RealismRating,
  type RecommendLikelihood,
} from "@/types/feedback";

const DIFFICULTY_KEYS = Object.keys(DIFFICULTY_RATING_LABELS) as DifficultyRating[];
const REALISM_KEYS = Object.keys(REALISM_RATING_LABELS) as RealismRating[];
const RECOMMEND_KEYS = Object.keys(RECOMMEND_LIKELIHOOD_LABELS) as RecommendLikelihood[];

interface QuizFeedbackModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  questionCount: number;
}

export function QuizFeedbackModal({ open, onOpenChange, questionCount }: QuizFeedbackModalProps) {
  const [overallRating, setOverallRating] = useState(0);
  const [questionQualityRating, setQuestionQualityRating] = useState(0);
  const [difficultyRating, setDifficultyRating] = useState<DifficultyRating | null>(null);
  const [realismRating, setRealismRating] = useState<RealismRating | null>(null);
  const [rationaleRating, setRationaleRating] = useState(0);
  const [hadIssue, setHadIssue] = useState<"yes" | "no">("no");
  const [issueQuestionNumber, setIssueQuestionNumber] = useState("");
  const [issueDescription, setIssueDescription] = useState("");
  const [likedMost, setLikedMost] = useState("");
  const [improvement, setImprovement] = useState("");
  const [recommend, setRecommend] = useState<RecommendLikelihood | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [attemptedSubmit, setAttemptedSubmit] = useState(false);

  const missingFields = [
    overallRating === 0 && "overall rating (1)",
    questionQualityRating === 0 && "question quality (2)",
    difficultyRating === null && "difficulty (3)",
    realismRating === null && "realism (4)",
    rationaleRating === 0 && "rationale helpfulness (5)",
    hadIssue === "yes" && issueQuestionNumber.trim().length === 0 && "the question number (6)",
    recommend === null && "would you recommend NextWise (9)",
  ].filter((v): v is string => Boolean(v));
  const canSubmit = missingFields.length === 0;

  function reset() {
    setOverallRating(0);
    setQuestionQualityRating(0);
    setDifficultyRating(null);
    setRealismRating(null);
    setRationaleRating(0);
    setHadIssue("no");
    setIssueQuestionNumber("");
    setIssueDescription("");
    setLikedMost("");
    setImprovement("");
    setRecommend(null);
    setAttemptedSubmit(false);
  }

  async function handleSubmit() {
    if (!canSubmit || !difficultyRating || !realismRating || !recommend) {
      setAttemptedSubmit(true);
      return;
    }
    setSubmitting(true);
    try {
      await submitQuizFeedback({
        overall_rating: overallRating,
        question_quality_rating: questionQualityRating,
        difficulty_rating: difficultyRating,
        realism_rating: realismRating,
        rationale_helpfulness_rating: rationaleRating,
        had_question_issue: hadIssue === "yes",
        issue_question_number:
          hadIssue === "yes" && issueQuestionNumber ? Number(issueQuestionNumber) : undefined,
        issue_description: hadIssue === "yes" ? issueDescription.trim() || undefined : undefined,
        liked_most: likedMost.trim() || undefined,
        improvement_suggestion: improvement.trim() || undefined,
        recommend_likelihood: recommend,
      });
      toast.success("Thanks for your feedback!");
      reset();
      onOpenChange(false);
    } catch {
      toast.error("Couldn't submit your feedback. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  // BETA-ONLY: skipping is disabled so every user leaves feedback — see
  // handleSkip and the Skip button below, both commented out rather than
  // deleted so this is a one-line revert once beta testing wraps up.
  // function handleSkip() {
  //   reset();
  //   onOpenChange(false);
  // }

  return (
    // onOpenChange is intentionally a no-op: this dialog is controlled
    // purely by the `open` prop (driven by QuizResultsPage), and the only
    // path that's allowed to close it is a successful submit inside
    // handleSubmit below. Without this, Base UI would still call
    // onOpenChange (and thus close the dialog) on Escape or an
    // outside/backdrop press, silently reopening the "skip" loophole this
    // change is meant to close. disablePointerDismissal additionally stops
    // an outside press from even attempting to dismiss it.
    <Dialog open={open} onOpenChange={() => {}} disablePointerDismissal>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg" showCloseButton={false}>
        <DialogHeader>
          <DialogTitle>After-Quiz Feedback</DialogTitle>
          <DialogDescription>Help us improve NextWise. This takes about a minute.</DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-5 py-2">
          <FeedbackField label="1. How would you rate this quiz overall?">
            <StarRating value={overallRating} onChange={setOverallRating} label="Overall rating" />
          </FeedbackField>

          <FeedbackField label="2. How would you rate the quality of the questions?">
            <StarRating value={questionQualityRating} onChange={setQuestionQualityRating} label="Question quality" />
          </FeedbackField>

          <FeedbackField label="3. How was the difficulty?">
            <RadioGroup value={difficultyRating ?? ""} onValueChange={(v) => setDifficultyRating(v as DifficultyRating)}>
              {DIFFICULTY_KEYS.map((key) => (
                <RadioOption key={key} id={`difficulty-${key}`} value={key} label={DIFFICULTY_RATING_LABELS[key]} />
              ))}
            </RadioGroup>
          </FeedbackField>

          <FeedbackField label="4. How realistic did the questions feel compared with the NCLEX?">
            <RadioGroup value={realismRating ?? ""} onValueChange={(v) => setRealismRating(v as RealismRating)}>
              {REALISM_KEYS.map((key) => (
                <RadioOption key={key} id={`realism-${key}`} value={key} label={REALISM_RATING_LABELS[key]} />
              ))}
            </RadioGroup>
          </FeedbackField>

          <FeedbackField label="5. How helpful were the rationales?">
            <StarRating value={rationaleRating} onChange={setRationaleRating} label="Rationale helpfulness" />
          </FeedbackField>

          <FeedbackField label="6. Did you encounter any question that you believe was unclear, incorrect, or had another issue?">
            <RadioGroup
              value={hadIssue}
              onValueChange={(v) => setHadIssue(v as "yes" | "no")}
              className="grid-flow-col justify-start gap-4"
            >
              <RadioOption id="had-issue-yes" value="yes" label="Yes" />
              <RadioOption id="had-issue-no" value="no" label="No" />
            </RadioGroup>
            {hadIssue === "yes" && (
              <div className="mt-3 flex flex-col gap-3 rounded-lg border border-border bg-muted/30 p-3">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="issue-question-number">Question number</Label>
                  <Input
                    id="issue-question-number"
                    type="number"
                    min={1}
                    max={questionCount}
                    value={issueQuestionNumber}
                    onChange={(e) => setIssueQuestionNumber(e.target.value)}
                    placeholder={`1–${questionCount}`}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="issue-description">What was the issue?</Label>
                  <Textarea
                    id="issue-description"
                    value={issueDescription}
                    onChange={(e) => setIssueDescription(e.target.value)}
                    rows={2}
                  />
                </div>
              </div>
            )}
          </FeedbackField>

          <FeedbackField label="7. What did you like most about this quiz?" hint="Optional">
            <Textarea value={likedMost} onChange={(e) => setLikedMost(e.target.value)} rows={2} />
          </FeedbackField>

          <FeedbackField label="8. What should we improve?" hint="Optional">
            <Textarea value={improvement} onChange={(e) => setImprovement(e.target.value)} rows={2} />
          </FeedbackField>

          <FeedbackField label="9. Would you recommend NextWise to another nursing student preparing for the NCLEX?">
            <RadioGroup value={recommend ?? ""} onValueChange={(v) => setRecommend(v as RecommendLikelihood)}>
              {RECOMMEND_KEYS.map((key) => (
                <RadioOption key={key} id={`recommend-${key}`} value={key} label={RECOMMEND_LIKELIHOOD_LABELS[key]} />
              ))}
            </RadioGroup>
          </FeedbackField>

          {attemptedSubmit && !canSubmit && (
            <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              Please answer: {missingFields.join(", ")}.
            </p>
          )}
        </div>

        <DialogFooter>
          {/* BETA-ONLY: Skip button removed so feedback isn't optional — restore alongside handleSkip above to bring it back. */}
          {/* <Button variant="outline" onClick={handleSkip} disabled={submitting}>
            Skip
          </Button> */}
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? "Submitting…" : "Submit feedback"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function FeedbackField({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-sm font-medium text-foreground">{label}</p>
        {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
      </div>
      {children}
    </div>
  );
}

function RadioOption({ id, value, label }: { id: string; value: string; label: string }) {
  return (
    <div className="group/field-label flex items-center gap-2">
      <RadioGroupItem id={id} value={value} />
      <Label htmlFor={id} className="font-normal">
        {label}
      </Label>
    </div>
  );
}
