import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border bg-muted/40 p-10 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
        <Icon className="h-5 w-5" />
      </span>
      <h3 className="font-display text-base font-medium text-foreground">{title}</h3>
      {description && <p className="max-w-sm text-sm text-muted-foreground">{description}</p>}
      {action}
    </div>
  );
}
