import type { ReactNode } from "react";

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

/**
 * Renders `label` as an inline text trigger that opens `children` (legal
 * body content — typically a *Body component like PrivacyPolicyBody) in a
 * modal, instead of navigating away. Used on the registration page so
 * reviewing a legal document doesn't lose the student's in-progress form —
 * navigating to a full page would clear whatever they'd already typed.
 */
export function LegalLinkModal({
  label,
  title,
  children,
  className,
}: {
  label: string;
  title: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Dialog>
      <DialogTrigger
        render={<button type="button" className={cn("text-primary underline-offset-2 hover:underline", className)} />}
      >
        {label}
      </DialogTrigger>
      <DialogContent className="max-h-[80vh] max-w-2xl overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-8 text-sm leading-relaxed text-foreground/90 [&_li]:ml-5 [&_li]:list-disc [&_ul]:flex [&_ul]:flex-col [&_ul]:gap-1.5">
          {children}
        </div>
      </DialogContent>
    </Dialog>
  );
}
