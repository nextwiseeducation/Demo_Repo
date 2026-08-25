import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { z } from "zod";

import { RateLimitBanner } from "@/components/common/ErrorState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthCard } from "@/features/auth/components/AuthCard";
import { useAuth } from "@/features/auth/AuthContext";
import { normalizeApiError } from "@/lib/api/errors";
import { ROUTES } from "@/lib/constants";

const schema = z.object({
  email: z.email("Enter a valid email"),
  password: z.string().min(1, "Enter your password"),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const mutation = useMutation({
    mutationFn: (values: FormValues) => login(values.email, values.password),
    onSuccess: () => {
      const redirect = searchParams.get("redirect");
      navigate(redirect || ROUTES.dashboard, { replace: true });
    },
  });

  const error = mutation.isError ? normalizeApiError(mutation.error) : null;

  return (
    <AuthCard
      title="Welcome back"
      description="Log in to continue your practice."
      footer={
        <>
          Don't have an account?{" "}
          <Link to={ROUTES.register} className="font-medium text-primary hover:underline">
            Create one
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="flex flex-col gap-4">
        {error?.isRateLimited && <RateLimitBanner message="Too many login attempts. Try again in a minute." />}
        {error && !error.isRateLimited && (
          <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            We couldn't log you in. Double-check your email and password, or if you just registered, make sure
            you've verified your email first.
          </p>
        )}

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" autoComplete="email" {...register("email")} />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link to={ROUTES.forgotPassword} className="text-xs font-medium text-primary hover:underline">
              Forgot password?
            </Link>
          </div>
          <Input id="password" type="password" autoComplete="current-password" {...register("password")} />
          {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        </div>

        <Button type="submit" className="mt-2 w-full" size="lg" disabled={mutation.isPending}>
          {mutation.isPending ? "Logging in..." : "Log in"}
        </Button>
      </form>
    </AuthCard>
  );
}
