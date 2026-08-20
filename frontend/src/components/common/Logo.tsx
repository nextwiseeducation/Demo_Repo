import { GraduationCap } from "lucide-react";
import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";

/**
 * Text/wordmark placeholder — no real brand logo asset exists yet. Swap the
 * icon+wordmark for a real mark when the client provides one; the layout
 * (icon chip + wordmark) is designed to accept a static SVG drop-in later.
 */
export function Logo({ className, dark = false }: { className?: string; dark?: boolean }) {
  return (
    <Link to={ROUTES.home} className={cn("flex items-center gap-2 font-display font-semibold", className)}>
      <span
        className={cn(
          "flex h-8 w-8 items-center justify-center rounded-lg",
          dark ? "bg-white/15 text-white" : "bg-primary text-primary-foreground",
        )}
      >
        <GraduationCap className="h-4.5 w-4.5" strokeWidth={2.25} />
      </span>
      <span className={cn("text-lg tracking-tight", dark ? "text-white" : "text-foreground")}>NextWise</span>
    </Link>
  );
}
