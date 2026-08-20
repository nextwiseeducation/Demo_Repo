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
import { PasswordRequirementsHint } from "@/features/auth/components/PasswordRequirementsHint";
import * as authApi from "@/lib/api/auth";
import { normalizeApiError } from "@/lib/api/errors";
import { ROUTES } from "@/lib/constants";

const schema = z
  .object({
    full_name: z.string().min(1, "Enter your full name"),
    email: z.email("Enter a valid email"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords don't match",
    path: ["confirm_password"],
  });

type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setError,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const password = watch("password", "");

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      authApi.register({ email: values.email, password: values.password, full_name: values.full_name }),
    onSuccess: (_data, variables) => setSubmittedEmail(variables.email),
    onError: (error) => {
      const normalized = normalizeApiError(error);
      if (normalized.fieldErrors) {
        for (const [field, messages] of Object.entries(normalized.fieldErrors)) {
          if (field === "email" || field === "password" || field === "full_name") {
            setError(field, { message: messages[0] });
          }
        }
      }
    },
  });

  if (submittedEmail) {
    return (
      <AuthCard title="Check your email">
        <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-card p-6 text-center">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
            <MailCheck className="h-5 w-5" />
          </span>
          <p className="text-sm text-muted-foreground">
            We sent a verification link to <span className="font-medium text-foreground">{submittedEmail}</span>. It
            can take a minute to arrive — check your spam folder too. The link expires in 3 days.
          </p>
          <Link to={ROUTES.login} className="text-sm font-medium text-primary hover:underline">
            Back to log in
          </Link>
        </div>
      </AuthCard>
    );
  }

  const rateLimited = mutation.isError && normalizeApiError(mutation.error).isRateLimited;

  return (
    <AuthCard
      title="Create your account"
      description="Start practicing NCLEX-style questions today."
      footer={
        <>
          Already have an account?{" "}
          <Link to={ROUTES.login} className="font-medium text-primary hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="flex flex-col gap-4">
        {rateLimited && <RateLimitBanner message="Too many registration attempts — try again in about an hour." />}

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="full_name">Full name</Label>
          <Input id="full_name" autoComplete="name" {...register("full_name")} />
          {errors.full_name && <p className="text-xs text-destructive">{errors.full_name.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" autoComplete="email" {...register("email")} />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" autoComplete="new-password" {...register("password")} />
          <PasswordRequirementsHint password={password} />
          {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="confirm_password">Confirm password</Label>
          <Input id="confirm_password" type="password" autoComplete="new-password" {...register("confirm_password")} />
          {errors.confirm_password && <p className="text-xs text-destructive">{errors.confirm_password.message}</p>}
        </div>

        <Button type="submit" className="mt-2 w-full" size="lg" disabled={mutation.isPending}>
          {mutation.isPending ? "Creating account..." : "Create account"}
        </Button>
      </form>
    </AuthCard>
  );
}
