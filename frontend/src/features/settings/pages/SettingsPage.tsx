import { useMutation } from "@tanstack/react-query";
import {
  Bell,
  Download,
  FileText,
  KeyRound,
  LogOut,
  MailCheck,
  ScrollText,
  ShieldAlert,
  Trash2,
  type LucideIcon,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/features/auth/AuthContext";
import * as authApi from "@/lib/api/auth";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";

const SUBSCRIPTION_LABELS: Record<string, string> = {
  FREE: "Free plan",
  ACTIVE: "Active",
  PAST_DUE: "Past due",
  CANCELED: "Canceled",
};

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const resetMutation = useMutation({
    mutationFn: () => authApi.requestPasswordReset(user!.email),
  });

  async function handleLogout() {
    await logout();
    navigate(ROUTES.home);
  }

  return (
    <div className="flex max-w-2xl flex-col gap-8">
      <div>
        <h1 className="font-display text-2xl font-semibold text-foreground">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your account, security, and preferences.</p>
      </div>

      <Card id="account" size="sm">
        <CardHeader>
          <CardTitle>Account</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs font-medium text-muted-foreground">Name</span>
            <span className="text-sm text-foreground">{user?.full_name || "Not set"}</span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs font-medium text-muted-foreground">Email</span>
            <span className="text-sm text-foreground">{user?.email}</span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs font-medium text-muted-foreground">Plan</span>
            <Badge variant="secondary" className="w-fit">
              {SUBSCRIPTION_LABELS[user?.subscription_status ?? "FREE"]}
            </Badge>
          </div>
          <div className="mt-1 flex items-center justify-between gap-3 border-t border-border pt-3">
            <p className="text-xs text-muted-foreground">
              You're on the Free plan. Upgrade options will be available soon.
            </p>
            <Button variant="outline" size="sm" className="w-fit shrink-0" disabled>
              Upgrade
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card id="security">
        <CardHeader>
          <CardTitle>Security</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-5">
          <div className="flex flex-col gap-3">
            {resetMutation.isSuccess ? (
              <div className="flex items-center gap-2.5 text-sm text-foreground">
                <MailCheck className="h-4 w-4 shrink-0 text-success" />
                Check your email for a reset link. It can take a minute to arrive.
              </div>
            ) : (
              <>
                <p className="text-sm text-muted-foreground">
                  We'll email a password reset link to {user?.email}.
                </p>
                <Button
                  variant="default"
                  className="w-fit"
                  disabled={resetMutation.isPending}
                  onClick={() => resetMutation.mutate()}
                >
                  <KeyRound className="h-4 w-4" />
                  {resetMutation.isPending ? "Sending..." : "Send reset link"}
                </Button>
              </>
            )}
          </div>

          <div className="flex flex-col gap-2 border-t border-border pt-4">
            <Button variant="destructive" className="w-fit" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
              Log out
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card id="preferences">
        <CardHeader>
          <CardTitle>Preferences</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col divide-y divide-border">
          <PlaceholderRow icon={Bell} label="Notification preferences" />
        </CardContent>
      </Card>

      <Card id="privacy-data">
        <CardHeader>
          <CardTitle>Privacy &amp; Data</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col divide-y divide-border">
          <PlaceholderRow icon={Download} label="Download my data" />
          <PlaceholderRow icon={Trash2} label="Delete account" destructive />
        </CardContent>
      </Card>

      <Card id="legal">
        <CardHeader>
          <CardTitle>Legal</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col divide-y divide-border">
          <LegalRow icon={FileText} label="Privacy Policy" to={ROUTES.privacyPolicy} />
          <LegalRow icon={ScrollText} label="Terms and Conditions" to={ROUTES.termsAndConditions} />
          <LegalRow
            icon={ShieldAlert}
            label="NCLEX Disclaimer"
            to={`${ROUTES.termsAndConditions}#nclex-examination-disclaimer`}
          />
        </CardContent>
      </Card>
    </div>
  );
}

function PlaceholderRow({ icon: Icon, label, destructive }: { icon: LucideIcon; label: string; destructive?: boolean }) {
  return (
    <div className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
      <div className="flex items-center gap-2.5">
        <Icon className={cn("h-4 w-4", destructive ? "text-destructive" : "text-muted-foreground")} />
        <span className={cn("text-sm font-medium", destructive ? "text-destructive" : "text-foreground")}>
          {label}
        </span>
      </div>
      <Badge variant="outline">Coming soon</Badge>
    </div>
  );
}

function LegalRow({ icon: Icon, label, to }: { icon: LucideIcon; label: string; to: string }) {
  return (
    <Link to={to} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
      <div className="flex items-center gap-2.5">
        <Icon className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium text-foreground">{label}</span>
      </div>
    </Link>
  );
}
