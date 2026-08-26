import { Link, Outlet } from "react-router-dom";

import logoFull from "@/assets/marketing/logo-full.png";
import { ROUTES } from "@/lib/constants";

export function AuthLayout() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="flex flex-col justify-between p-6 sm:p-8">
        <Link to={ROUTES.home} aria-label="NextWise home">
          <img src={logoFull} alt="NextWise" className="h-9 w-auto" />
        </Link>
        <div className="mx-auto w-full max-w-sm py-12">
          <Outlet />
        </div>
        <p className="text-center text-xs text-muted-foreground lg:text-left">
          © {new Date().getFullYear()} NextWise Education
        </p>
      </div>

      <div
        className="relative hidden overflow-hidden lg:flex lg:flex-col lg:justify-center lg:p-16"
        style={{ background: "linear-gradient(135deg,#1e1b52 0%,#3b32a8 46%,#7c3aed 100%)" }}
      >
        <div
          className="absolute inset-0 opacity-[0.16]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "30px 30px",
          }}
        />
        <div
          className="pointer-events-none absolute rounded-full opacity-50"
          style={{ width: 520, height: 520, top: -180, right: -120, background: "#8b5cf6", filter: "blur(70px)" }}
        />
        <div
          className="pointer-events-none absolute rounded-full opacity-50"
          style={{ width: 420, height: 420, bottom: -160, left: -140, background: "#4338ca", filter: "blur(70px)" }}
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
