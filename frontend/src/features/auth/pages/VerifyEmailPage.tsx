import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, XCircle } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { AuthCard } from "@/features/auth/components/AuthCard";
import * as authApi from "@/lib/api/auth";
import { ROUTES } from "@/lib/constants";

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const query = useQuery({
    queryKey: ["verify-email", token],
    queryFn: () => authApi.verifyEmail(token!),
    enabled: Boolean(token),
    retry: false,
  });

  if (!token) {
    return (
      <AuthCard title="Invalid verification link">
        <InvalidLinkNotice />
      </AuthCard>
    );
  }

  if (query.isPending) {
    return (
      <AuthCard title="Verifying your email">
        <LoadingSpinner />
      </AuthCard>
    );
  }

  if (query.isError) {
    return (
      <AuthCard title="This link isn't valid">
        <InvalidLinkNotice />
      </AuthCard>
    );
  }

  return (
    <AuthCard title="Email verified">
      <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-card p-6 text-center">
        <span className="flex h-11 w-11 items-center justify-center rounded-full bg-success/10 text-success">
          <CheckCircle2 className="h-5 w-5" />
        </span>
        <p className="text-sm text-muted-foreground">Your email is verified — you can now log in.</p>
        <Button render={<Link to={ROUTES.login}>Log in</Link>} className="w-full" />
      </div>
    </AuthCard>
  );
}

function InvalidLinkNotice() {
  return (
    <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-card p-6 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <XCircle className="h-5 w-5" />
      </span>
      <p className="text-sm text-muted-foreground">
        This verification link is invalid or has expired. Links expire after 3 days — there's currently no self-serve
        way to resend one, so contact support if you're stuck.
      </p>
      <Button variant="outline" render={<Link to={ROUTES.login}>Back to log in</Link>} className="w-full" />
    </div>
  );
}
