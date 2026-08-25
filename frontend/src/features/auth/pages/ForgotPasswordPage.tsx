import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { MailCheck } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { RateLimitBanner } from "@/components/common/ErrorState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthCard } from "@/features/auth/components/AuthCard";
import * as authApi from "@/lib/api/auth";
import { normalizeApiError } from "@/lib/api/errors";
import { ROUTES } from "@/lib/constants";

const schema = z.object({ email: z.email("Enter a valid email") });
type FormValues = z.infer<typeof schema>;

export function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const mutation = useMutation({
    mutationFn: (values: FormValues) => authApi.requestPasswordReset(values.email),
    onSuccess: () => setSubmitted(true),
  });

  const error = mutation.isError ? normalizeApiError(mutation.error) : null;

  if (submitted) {
    return (
      <AuthCard title="Check your email">
        <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-card p-6 text-center">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
            <MailCheck className="h-5 w-5" />
          </span>
          <p className="text-sm text-muted-foreground">
            If that email is registered, we've sent a reset link. It can take a minute to arrive.
          </p>
          <button
            onClick={() => {
              setSubmitted(false);
              reset();
            }}
            className="text-sm font-medium text-primary hover:underline"
          >
            Try a different email
          </button>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="Forgot your password?"
      description="Enter your email and we'll send you a reset link."
      footer={
        <Link to={ROUTES.login} className="font-medium text-primary hover:underline">
          Back to log in
        </Link>
      }
    >
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="flex flex-col gap-4">
        {error?.isRateLimited && <RateLimitBanner message="Too many reset attempts. Try again in about an hour." />}

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" autoComplete="email" {...register("email")} />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>

        <Button type="submit" className="mt-2 w-full" size="lg" disabled={mutation.isPending}>
          {mutation.isPending ? "Sending..." : "Send reset link"}
        </Button>
      </form>
    </AuthCard>
  );
}
