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

      <footer className="border-t border-border/70 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-3 px-6 text-sm text-muted-foreground sm:flex-row sm:justify-between">
          <Logo className="text-foreground" />
          <p>© {new Date().getFullYear()} NextWise Education. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
