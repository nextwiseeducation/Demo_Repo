import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";

export function ErrorState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-border bg-card p-8 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <AlertTriangle className="h-5 w-5" />
      </span>
      <h3 className="font-display text-lg font-medium text-foreground">{title}</h3>
      {description && <p className="max-w-sm text-sm text-muted-foreground">{description}</p>}
      {action}
    </div>
  );
}

export function RateLimitBanner({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-accent/30 bg-accent/10 px-4 py-3 text-sm text-accent-foreground">
      <p className="font-medium text-accent">Too many attempts</p>
      <p className="mt-0.5 text-foreground/80">{message}</p>
    </div>
  );
}
