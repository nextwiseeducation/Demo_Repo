import { ArrowRight, ClipboardList } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/features/auth/AuthContext";
import { ROUTES } from "@/lib/constants";
import { QUESTION_TYPE_LABELS, SUPPORTED_QUESTION_TYPES, type QuestionType } from "@/types/question";

const ALL_TYPES = Object.keys(QUESTION_TYPE_LABELS) as QuestionType[];

export function DashboardPage() {
  const { user } = useAuth();
  const firstName = user?.full_name?.split(" ")[0] || user?.email;

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="font-display text-2xl font-semibold text-foreground">Welcome back, {firstName}</h1>
        <p className="mt-1 text-sm text-muted-foreground">Ready to keep building your clinical judgment?</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Your progress</CardTitle>
          </CardHeader>
          <CardContent>
            <EmptyState
              icon={ClipboardList}
              title="No quizzes completed yet"
              description="Start your first practice quiz to see your performance breakdown here."
            />
          </CardContent>
        </Card>

        <Card className="flex flex-col justify-between border-primary/20 bg-primary text-primary-foreground">
          <CardHeader>
            <CardTitle className="text-primary-foreground">Start a practice quiz</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-[color:var(--brand-indigo-light)]">
              Practice MCQ and SATA questions with instant rationales.
            </p>
            <Button
              variant="secondary"
              className="mt-4 w-full"
              render={
                <Link to={ROUTES.quizSetup}>
                  Start now
                  <ArrowRight className="h-4 w-4" />
                </Link>
              }
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Question type coverage</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
            {ALL_TYPES.map((type) => {
              // NGN_CASE isn't in SUPPORTED_QUESTION_TYPES itself (it's a
              // wrapper that renders as whichever real type its ngn_type
              // names, not a renderer of its own — see effectiveQuestionType),
              // but every type it can wrap to is now supported, so it reads
              // as available here too.
              const available = type === "NGN_CASE" || SUPPORTED_QUESTION_TYPES.includes(type);
              return (
                <div
                  key={type}
                  className="flex flex-col gap-1.5 rounded-lg border border-border bg-card px-3 py-2.5"
                >
                  <span className="text-xs font-medium text-foreground">{QUESTION_TYPE_LABELS[type]}</span>
                  <Badge variant={available ? "secondary" : "outline"} className="w-fit">
                    {available ? "Available now" : "Coming soon"}
                  </Badge>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
