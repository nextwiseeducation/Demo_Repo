import type { ReactNode } from "react";

interface Section {
  id: string;
  title: string;
}

interface LegalPageLayoutProps {
  title: string;
  lastUpdated: string;
  intro?: ReactNode;
  sections: Section[];
  children: ReactNode;
}

/**
 * Shared shell for Privacy Policy / Terms and Conditions / Accessibility —
 * a title block, a jump-to-section nav built from the same `sections` list
 * each page passes to its <LegalSection> blocks, and a reading-width
 * column (legal text is easier to read at ~65ch than the marketing
 * pages' wide 6xl layout).
 */
export function LegalPageLayout({ title, lastUpdated, intro, sections, children }: LegalPageLayoutProps) {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-10 px-6 py-16">
      <div className="flex flex-col gap-3">
        <h1 className="font-display text-3xl font-semibold text-foreground sm:text-4xl">{title}</h1>
        <p className="text-sm text-muted-foreground">Last updated: {lastUpdated}</p>
        {intro && <div className="mt-2 text-base leading-relaxed text-foreground/90">{intro}</div>}
      </div>

      <nav aria-label="Table of contents" className="rounded-xl border border-border bg-card p-5">
        <p className="mb-3 text-xs font-semibold tracking-wide text-muted-foreground uppercase">On this page</p>
        <ol className="grid gap-1.5 sm:grid-cols-2">
          {sections.map((section, index) => (
            <li key={section.id}>
              <a href={`#${section.id}`} className="text-sm text-primary hover:underline">
                {index + 1}. {section.title}
              </a>
            </li>
          ))}
        </ol>
      </nav>

      <div className="flex flex-col gap-10">{children}</div>
    </div>
  );
}

export function LegalSection({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24">
      <h2 className="font-display text-xl font-semibold text-foreground">{title}</h2>
      <div className="mt-3 flex flex-col gap-3 text-sm leading-relaxed text-foreground/90 [&_li]:ml-5 [&_li]:list-disc [&_ul]:flex [&_ul]:flex-col [&_ul]:gap-1.5">
        {children}
      </div>
    </section>
  );
}
