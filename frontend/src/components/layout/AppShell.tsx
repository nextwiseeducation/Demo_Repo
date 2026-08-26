import { LogOut, Settings, User } from "lucide-react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";

import "@/components/layout/AppShell.css";
import logoFull from "@/assets/marketing/logo-full.png";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/features/auth/AuthContext";
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
    <div className="nw-app flex min-h-screen flex-col">
      <header>
        <div className="container header-inner">
          <div className="header-left">
            <Link to={ROUTES.dashboard} aria-label="NextWise home">
              <img className="brand" src={logoFull} alt="NextWise" />
            </Link>
            <nav>
              <NavItem to={ROUTES.dashboard}>Dashboard</NavItem>
              <NavItem to={ROUTES.quizSetup}>Practice</NavItem>
            </nav>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger className="avatar">
              <User className="h-4 w-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
              <DropdownMenuGroup>
                <DropdownMenuLabel className="flex flex-col gap-1">
                  <span className="truncate text-sm font-medium text-foreground">{user?.full_name || user?.email}</span>
                  <span className="truncate text-xs font-normal text-muted-foreground">{user?.email}</span>
                </DropdownMenuLabel>
                <div className="px-2 pb-1.5">
                  <Badge variant="secondary">{SUBSCRIPTION_LABELS[user?.subscription_status ?? "FREE"]}</Badge>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem render={<Link to={ROUTES.settings} />}>
                  <Settings className="h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} variant="destructive">
                  <LogOut className="h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuGroup>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main>
        <div className="container">
          <Outlet />
        </div>
      </main>

      <footer>
        <div className="container footer-inner">
          <span>© {new Date().getFullYear()} NextWise Education. All rights reserved.</span>
          <nav className="footer-links">
            <Link to={ROUTES.faq}>FAQ</Link>
            <Link to={ROUTES.privacyPolicy}>Privacy Policy</Link>
            <Link to={ROUTES.termsAndConditions}>Terms and Conditions</Link>
            <Link to={ROUTES.accessibility}>Accessibility</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink to={to} end className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
      {children}
    </NavLink>
  );
}
