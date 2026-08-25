import { Outlet } from "react-router-dom";

import { Logo } from "@/components/common/Logo";

export function AuthLayout() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="flex flex-col justify-between p-8">
        <Logo />
        <div className="mx-auto w-full max-w-sm py-12">
          <Outlet />
        </div>
        <p className="text-center text-xs text-muted-foreground lg:text-left">
          © {new Date().getFullYear()} NextWise Education
        </p>
      </div>

      <div className="relative hidden overflow-hidden bg-primary lg:flex lg:flex-col lg:justify-center lg:p-16">
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "28px 28px",
          }}
        />
        <div className="relative">
          <p className="font-display text-3xl font-medium text-white">
            Smarter Nursing.
            <br />
            Stronger Clinical Judgment.
          </p>
          <p className="mt-4 max-w-sm text-[15px] leading-relaxed text-[color:var(--brand-indigo-light)]">
            NGN-ready practice questions, built around NCSBN's Clinical Judgment Model, with a rationale behind
            every answer.
          </p>
        </div>
      </div>
    </div>
  );
}
