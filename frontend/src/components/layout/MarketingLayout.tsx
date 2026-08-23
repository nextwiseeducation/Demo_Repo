import { Link, Outlet } from "react-router-dom";

import { Logo } from "@/components/common/Logo";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/constants";

export function MarketingLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-40 border-b border-border/70 bg-background/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Logo />
          <nav className="hidden items-center gap-8 text-sm font-medium text-muted-foreground md:flex">
            <a href="#features" className="hover:text-foreground">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-foreground">
              How it works
            </a>
          </nav>
          <div className="flex items-center gap-2">
            <Button variant="ghost" render={<Link to={ROUTES.login}>Log in</Link>} />
            <Button render={<Link to={ROUTES.register}>Get started</Link>} />
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="bg-primary py-12">
        <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6">
          <div className="flex flex-col gap-8 sm:flex-row sm:justify-between">
            <div className="flex flex-col gap-3">
              <Logo dark />
              <p className="max-w-xs text-sm text-[color:var(--brand-indigo-light)]">
                Practice questions, rationales, and progress tracking for NCLEX-RN and NCLEX-PN exam preparation.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-8 sm:grid-cols-3">
              <div className="flex flex-col gap-2.5">
                <p className="text-xs font-semibold tracking-wide text-[color:var(--brand-indigo-light)] uppercase">
                  Product
                </p>
                <a href="#features" className="text-sm text-white/80 hover:text-white">
                  Features
                </a>
                <a href="#how-it-works" className="text-sm text-white/80 hover:text-white">
                  How it works
                </a>
              </div>

              <div className="flex flex-col gap-2.5">
                <p className="text-xs font-semibold tracking-wide text-[color:var(--brand-indigo-light)] uppercase">
                  Support
                </p>
                <Link to={ROUTES.faq} className="text-sm text-white/80 hover:text-white">
                  FAQ
                </Link>
                <a href="mailto:support@nextwiseeducation.com" className="text-sm text-white/80 hover:text-white">
                  Contact us
                </a>
              </div>

              <div className="flex flex-col gap-2.5">
                <p className="text-xs font-semibold tracking-wide text-[color:var(--brand-indigo-light)] uppercase">
                  Legal
                </p>
                <Link to={ROUTES.privacyPolicy} className="text-sm text-white/80 hover:text-white">
                  Privacy Policy
                </Link>
                <Link to={ROUTES.termsAndConditions} className="text-sm text-white/80 hover:text-white">
                  Terms and Conditions
                </Link>
                <Link to={ROUTES.accessibility} className="text-sm text-white/80 hover:text-white">
                  Accessibility
                </Link>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-2 border-t border-white/15 pt-6 text-xs text-[color:var(--brand-indigo-light)]">
            <p>© {new Date().getFullYear()} NextWise Education. All rights reserved.</p>
            <p>
              NCLEX-RN® and NCLEX-PN® are registered trademarks of the National Council of State Boards of Nursing,
              Inc. (NCSBN). NextWise Education is not affiliated with, endorsed by, or sponsored by NCSBN.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
