import { LogOut, User } from "lucide-react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";

import { Logo } from "@/components/common/Logo";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/features/auth/AuthContext";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";

const SUBSCRIPTION_LABELS: Record<string, string> = {
  FREE: "Free plan",
  ACTIVE: "Active",
  PAST_DUE: "Past due",
  CANCELED: "Canceled",
};

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate(ROUTES.home);
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-40 border-b border-border/70 bg-background/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-8">
            <Logo />
            <nav className="hidden items-center gap-1 sm:flex">
              <NavItem to={ROUTES.dashboard}>Dashboard</NavItem>
              <NavItem to={ROUTES.quizSetup}>Practice</NavItem>
            </nav>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger className="flex h-9 w-9 items-center justify-center rounded-full bg-secondary text-secondary-foreground outline-none">
              <User className="h-4 w-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
              <DropdownMenuLabel className="flex flex-col gap-1">
                <span className="truncate text-sm font-medium text-foreground">{user?.full_name || user?.email}</span>
                <span className="truncate text-xs font-normal text-muted-foreground">{user?.email}</span>
              </DropdownMenuLabel>
              <div className="px-2 pb-1.5">
                <Badge variant="secondary">{SUBSCRIPTION_LABELS[user?.subscription_status ?? "FREE"]}</Badge>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem disabled className="justify-between">
                Manage subscription
                <span className="text-xs text-muted-foreground">Coming soon</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} variant="destructive">
                <LogOut className="h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-10">
        <Outlet />
      </main>

      <footer className="mt-auto bg-primary py-6">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-2 px-6 text-xs text-[color:var(--brand-indigo-light)] sm:flex-row sm:justify-between">
          <p>© {new Date().getFullYear()} NextWise Education. All rights reserved.</p>
          <nav className="flex items-center gap-4">
            <Link to={ROUTES.faq} className="hover:text-white">
              FAQ
            </Link>
            <Link to={ROUTES.privacyPolicy} className="hover:text-white">
              Privacy Policy
            </Link>
            <Link to={ROUTES.termsAndConditions} className="hover:text-white">
              Terms and Conditions
            </Link>
            <Link to={ROUTES.accessibility} className="hover:text-white">
              Accessibility
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        cn(
          "rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground",
          isActive && "bg-secondary text-secondary-foreground",
        )
      }
    >
      {children}
    </NavLink>
  );
}
