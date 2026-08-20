import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, XCircle } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useSearchParams } from "react-router-dom";
import { z } from "zod";

import { RateLimitBanner } from "@/components/common/ErrorState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthCard } from "@/features/auth/components/AuthCard";
import { PasswordRequirementsHint } from "@/features/auth/components/PasswordRequirementsHint";
import * as authApi from "@/lib/api/auth";
import { normalizeApiError } from "@/lib/api/errors";
import { ROUTES } from "@/lib/constants";

const schema = z
  .object({
    new_password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords don't match",
    path: ["confirm_password"],
  });

type FormValues = z.infer<typeof schema>;

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const uid = searchParams.get("uid");
  const token = searchParams.get("token");
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setError,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const password = watch("new_password", "");

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      authApi.confirmPasswordReset({ uid: uid!, token: token!, new_password: values.new_password }),
    onSuccess: () => setSuccess(true),
    onError: (error) => {
      const normalized = normalizeApiError(error);
      // A bad uid/token returns {detail} (dead link — nothing left to
      // retry). A weak password returns field errors (form stays usable).
      // Conflating these would hide a real validation error behind a scary
      // "link expired" message, or vice versa.
      if (normalized.fieldErrors?.new_password) {
        setError("new_password", { message: normalized.fieldErrors.new_password[0] });
      }
    },
  });

  if (!uid || !token) {
    return (
      <AuthCard title="Invalid reset link">
        <DeadLinkNotice />
      </AuthCard>
    );
  }

  const normalizedError = mutation.isError ? normalizeApiError(mutation.error) : null;
  const isDeadLink = normalizedError?.detail && !normalizedError.isRateLimited;

  if (isDeadLink) {
    return (
      <AuthCard title="This link isn't valid">
        <DeadLinkNotice />
      </AuthCard>
    );
  }

  if (success) {
    return (
      <AuthCard title="Password reset">
        <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-card p-6 text-center">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-success/10 text-success">
            <CheckCircle2 className="h-5 w-5" />
          </span>
          <p className="text-sm text-muted-foreground">Your password has been reset — you can now log in.</p>
          <Button render={<Link to={ROUTES.login}>Log in</Link>} className="w-full" />
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard title="Set a new password">
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="flex flex-col gap-4">
        {normalizedError?.isRateLimited && (
          <RateLimitBanner message="Too many attempts — try again in about an hour." />
        )}

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="new_password">New password</Label>
          <Input id="new_password" type="password" autoComplete="new-password" {...register("new_password")} />
          <PasswordRequirementsHint password={password} />
          {errors.new_password && <p className="text-xs text-destructive">{errors.new_password.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="confirm_password">Confirm password</Label>
          <Input id="confirm_password" type="password" autoComplete="new-password" {...register("confirm_password")} />
          {errors.confirm_password && <p className="text-xs text-destructive">{errors.confirm_password.message}</p>}
        </div>

        <Button type="submit" className="mt-2 w-full" size="lg" disabled={mutation.isPending}>
          {mutation.isPending ? "Resetting..." : "Reset password"}
        </Button>
      </form>
    </AuthCard>
  );
}

function DeadLinkNotice() {
  return (
    <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-card p-6 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <XCircle className="h-5 w-5" />
      </span>
      <p className="text-sm text-muted-foreground">
        This password reset link is invalid or has expired. Request a new one from the login page.
      </p>
      <Button variant="outline" render={<Link to={ROUTES.forgotPassword}>Request a new link</Link>} className="w-full" />
    </div>
  );
}
