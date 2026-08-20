import { Check, X } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * Mirrors Django's AUTH_PASSWORD_VALIDATORS (config/settings/base.py) as
 * far as is checkable client-side. UserAttributeSimilarityValidator and
 * CommonPasswordValidator still only get enforced server-side (no password
 * dictionary shipped to the client) — this narrows down failures the user
 * would otherwise only discover after a round-trip, it doesn't replace
 * backend validation.
 */
export function PasswordRequirementsHint({ password }: { password: string }) {
  const rules = [
    { label: "At least 8 characters", met: password.length >= 8 },
    { label: "Not entirely numbers", met: password.length > 0 && !/^\d+$/.test(password) },
  ];

  return (
    <ul className="space-y-1 text-xs">
      {rules.map((rule) => (
        <li
          key={rule.label}
          className={cn("flex items-center gap-1.5", rule.met ? "text-success" : "text-muted-foreground")}
        >
          {rule.met ? <Check className="h-3 w-3" /> : <X className="h-3 w-3 opacity-50" />}
          {rule.label}
        </li>
      ))}
      <li className="text-muted-foreground/70">Also avoid common passwords and ones too similar to your name or email</li>
    </ul>
  );
}
