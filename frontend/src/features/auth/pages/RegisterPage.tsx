import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { MailCheck } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { RateLimitBanner } from "@/components/common/ErrorState";
import { LegalLinkModal } from "@/components/common/LegalLinkModal";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthCard } from "@/features/auth/components/AuthCard";
import { PasswordRequirementsHint } from "@/features/auth/components/PasswordRequirementsHint";
import { NclexDisclaimerBody, TermsAndConditionsBody } from "@/features/marketing/pages/TermsAndConditionsPage";
import { PrivacyPolicyBody } from "@/features/marketing/pages/PrivacyPolicyPage";
import * as authApi from "@/lib/api/auth";
import { normalizeApiError } from "@/lib/api/errors";
import { ROUTES } from "@/lib/constants";

const schema = z
  .object({
    full_name: z.string().min(1, "Enter your full name"),
    email: z.email("Enter a valid email"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string(),
    // Required so a student cannot submit registration without
    // affirmatively acknowledging the NCLEX Examination Disclaimer — the
    // backend also enforces this independently (see RegisterSerializer),
    // this is just the client-side gate that keeps the form from even
    // submitting an unchecked box.
    accepted_disclaimer: z.boolean().refine((val) => val === true, {
      message: "You must acknowledge the NCLEX Examination Disclaimer to continue.",
    }),
    // Separate from accepted_disclaimer — a distinct legal document, a
    // distinct checkbox, a distinct backend record (see RegisterSerializer).
    accepted_terms: z.boolean().refine((val) => val === true, {
      message: "You must agree to the Privacy Policy and Terms and Conditions to continue.",
    }),
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
    control,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { accepted_disclaimer: false, accepted_terms: false },
  });

  const password = watch("password", "");

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      authApi.register({
        email: values.email,
        password: values.password,
        full_name: values.full_name,
        accepted_disclaimer: values.accepted_disclaimer,
        accepted_terms: values.accepted_terms,
      }),
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
            can take a minute to arrive, so check your spam folder too. The link expires in 3 days.
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
        {rateLimited && <RateLimitBanner message="Too many registration attempts. Try again in about an hour." />}

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

        <div className="flex flex-col gap-1.5">
          <div className="flex items-start gap-2">
            <Controller
              name="accepted_disclaimer"
              control={control}
              render={({ field }) => (
                <Checkbox
                  id="accepted_disclaimer"
                  checked={field.value}
                  onCheckedChange={(checked) => field.onChange(checked === true)}
                  className="mt-0.5"
                />
              )}
            />
            <Label htmlFor="accepted_disclaimer" className="text-xs font-normal leading-snug text-muted-foreground">
              I understand that NextWise provides independent NCLEX-RN® preparation materials and does not provide or
              guarantee actual NCLEX examination questions. I understand that NextWise does not guarantee that any
              specific question, topic, or concept will appear on my examination or guarantee a passing result.
            </Label>
          </div>
          <LegalLinkModal
            label="Read the full NCLEX Examination Disclaimer"
            title="NCLEX Examination Disclaimer"
            className="text-xs font-medium"
          >
            <NclexDisclaimerBody />
          </LegalLinkModal>
          {errors.accepted_disclaimer && (
            <p className="text-xs text-destructive">{errors.accepted_disclaimer.message}</p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <div className="flex items-start gap-2">
            <Controller
              name="accepted_terms"
              control={control}
              render={({ field }) => (
                <Checkbox
                  id="accepted_terms"
                  checked={field.value}
                  onCheckedChange={(checked) => field.onChange(checked === true)}
                  className="mt-0.5"
                />
              )}
            />
            <Label htmlFor="accepted_terms" className="text-xs font-normal leading-snug text-muted-foreground">
              I agree to the{" "}
              <LegalLinkModal label="Privacy Policy" title="Privacy Policy" className="text-xs font-medium">
                <PrivacyPolicyBody />
              </LegalLinkModal>{" "}
              and{" "}
              <LegalLinkModal label="Terms and Conditions" title="Terms and Conditions" className="text-xs font-medium">
                <TermsAndConditionsBody />
              </LegalLinkModal>
              .
            </Label>
          </div>
          {errors.accepted_terms && <p className="text-xs text-destructive">{errors.accepted_terms.message}</p>}
        </div>

        <Button type="submit" className="mt-2 w-full" size="lg" disabled={mutation.isPending}>
          {mutation.isPending ? "Creating account..." : "Create account"}
        </Button>
      </form>
    </AuthCard>
  );
}
