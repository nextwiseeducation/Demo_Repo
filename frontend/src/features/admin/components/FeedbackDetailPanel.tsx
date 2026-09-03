import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { FeedbackStatusSelect } from "@/features/admin/components/FeedbackStatusSelect";
import { useAdminFeedbackDetail } from "@/features/admin/hooks/useAdminFeedback";
import type {
  AdminIssueReportDetail,
  AdminQuizFeedbackDetail,
  FeedbackKind,
} from "@/types/admin";
import {
  DIFFICULTY_RATING_LABELS,
  QUESTION_ISSUE_TYPE_LABELS,
  REALISM_RATING_LABELS,
  RECOMMEND_LIKELIHOOD_LABELS,
  type DifficultyRating,
  type QuestionIssueType,
  type RealismRating,
  type RecommendLikelihood,
} from "@/types/feedback";

interface FeedbackDetailPanelProps {
  kind: FeedbackKind;
  id: string | null;
  onOpenChange: (open: boolean) => void;
  onDelete: (id: string) => void;
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm text-foreground">{value || "—"}</span>
    </div>
  );
}

function SurveyDetail({ detail }: { detail: AdminQuizFeedbackDetail }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Field label="Overall rating" value={`${detail.overall_rating} / 5`} />
      <Field label="Question quality" value={`${detail.question_quality_rating} / 5`} />
      <Field label="Rationale helpfulness" value={`${detail.rationale_helpfulness_rating} / 5`} />
      <Field label="Difficulty" value={DIFFICULTY_RATING_LABELS[detail.difficulty_rating as DifficultyRating]} />
      <Field label="Realism" value={REALISM_RATING_LABELS[detail.realism_rating as RealismRating]} />
      <Field label="Would recommend" value={RECOMMEND_LIKELIHOOD_LABELS[detail.recommend_likelihood as RecommendLikelihood]} />
      <div className="sm:col-span-2">
        <Field label="Liked most" value={detail.liked_most} />
      </div>
      <div className="sm:col-span-2">
        <Field label="Improvement suggestion" value={detail.improvement_suggestion} />
      </div>
      {detail.had_question_issue ? (
        <div className="sm:col-span-2">
          <Field
            label={`Reported an issue${detail.issue_question_number ? ` (Q${detail.issue_question_number})` : ""}`}
            value={detail.issue_description}
          />
        </div>
      ) : null}
    </div>
  );
}

function IssueDetail({ detail }: { detail: AdminIssueReportDetail }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Field label="Issue type" value={QUESTION_ISSUE_TYPE_LABELS[detail.issue_type as QuestionIssueType]} />
      <Field label="Question # in quiz" value={detail.question_number_in_quiz ?? undefined} />
      <div className="sm:col-span-2">
        <Field label="Question stem (as seen by the student)" value={detail.question_stem_snapshot} />
      </div>
      <div className="sm:col-span-2">
        <Field label="Description" value={detail.description} />
      </div>
    </div>
  );
}

export function FeedbackDetailPanel({ kind, id, onOpenChange, onDelete }: FeedbackDetailPanelProps) {
  const { data, isPending } = useAdminFeedbackDetail(kind, id);

  return (
    <Dialog open={id !== null} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] w-full max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{kind === "survey" ? "Survey feedback" : "Question issue report"}</DialogTitle>
        </DialogHeader>

        {isPending || !data ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">{data.student_name || "(no name on file)"}</p>
                <p className="text-xs text-muted-foreground">{data.student_email}</p>
              </div>
              <FeedbackStatusSelect kind={kind} id={data.id} status={data.status} />
            </div>
            <p className="text-xs text-muted-foreground">Submitted {new Date(data.created_at).toLocaleString()}</p>

            {kind === "survey" ? (
              <SurveyDetail detail={data as AdminQuizFeedbackDetail} />
            ) : (
              <IssueDetail detail={data as AdminIssueReportDetail} />
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          {data ? (
            <Button variant="destructive" onClick={() => onDelete(data.id)}>
              Delete
            </Button>
          ) : null}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
