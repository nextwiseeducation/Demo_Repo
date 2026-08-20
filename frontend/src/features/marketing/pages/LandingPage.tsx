import { BookOpenCheck, Layers, ListChecks, MessageSquareQuote } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MCQChoiceList } from "@/features/quiz/components/MCQChoiceList";
import { QuestionCard } from "@/features/quiz/components/QuestionCard";
import { MOCK_QUESTIONS } from "@/features/quiz/data/mockQuestions";
import { ROUTES } from "@/lib/constants";

const FEATURES = [
  {
    icon: Layers,
    title: "9 NGN-ready question types",
    description:
      "Matrix/Grid, Bow-Tie, Extended Multiple Response, Drag and Drop, Cloze, Enhanced Hot Spot, and full case studies — built into the platform from day one, not bolted on later.",
  },
  {
    icon: BookOpenCheck,
    title: "Built on NCSBN's Clinical Judgment Model",
    description:
      "Every question is tagged to a real step of the clinical judgment process — Recognize Cues, Analyze Cues, Prioritize Hypotheses, Generate Solutions, Take Action, Evaluate Outcomes.",
  },
  {
    icon: MessageSquareQuote,
    title: "A rationale for every answer",
    description: "Understand not just what's correct, but why — and why the other options aren't.",
  },
  {
    icon: ListChecks,
    title: "Organized by NCLEX Client Needs category",
    description: "Practice targeted to the same categories the real exam is actually weighted around.",
  },
];

const STEPS = [
  { title: "Register", description: "Create your account and verify your email in under a minute." },
  { title: "Practice", description: "Work through NGN-style questions filtered to what you need to focus on." },
  { title: "Review", description: "Read the rationale behind every answer and track where you're improving." },
];

export function LandingPage() {
  return (
    <>
      <section className="relative overflow-hidden bg-primary">
        <div
          className="absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "28px 28px",
          }}
        />
        <div className="relative mx-auto grid max-w-6xl gap-12 px-6 py-20 lg:grid-cols-2 lg:items-center lg:py-28">
          <div>
            <Badge variant="secondary" className="mb-5">
              NCLEX-RN &amp; NCLEX-PN prep
            </Badge>
            <h1 className="font-display text-4xl font-semibold tracking-tight text-white sm:text-5xl">
              Smarter Nursing.
              <br />
              Stronger Clinical Judgment.
            </h1>
            <p className="mt-5 max-w-md text-base leading-relaxed text-[color:var(--brand-indigo-light)]">
              NGN-ready practice questions built around how the real exam actually thinks — with a rationale behind
              every answer.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button size="lg" variant="secondary" render={<Link to={ROUTES.register}>Start free</Link>} />
              <Button
                size="lg"
                variant="outline"
                className="border-white/25 bg-transparent text-white hover:bg-white/10"
                render={<Link to={ROUTES.login}>Log in</Link>}
              />
            </div>
          </div>

          <div className="lg:pl-6">
            <QuestionCard question={MOCK_QUESTIONS[0]}>
              <MCQChoiceList
                choices={MOCK_QUESTIONS[0].answer_choices}
                selectedId={MOCK_QUESTIONS[0].answer_choices[0].id}
                submitted={false}
                onSelect={() => {}}
              />
            </QuestionCard>
          </div>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-6xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-semibold text-foreground">Built on the real schema, not a demo</h2>
          <p className="mt-3 text-muted-foreground">
            Everything below reflects how the platform is actually structured — not a marketing simplification.
          </p>
        </div>
        <div className="mt-12 grid gap-6 sm:grid-cols-2">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="rounded-xl border border-border bg-card p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                <feature.icon className="h-5 w-5" />
              </span>
              <h3 className="mt-4 font-display text-lg font-medium text-foreground">{feature.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="how-it-works" className="bg-secondary/30 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center font-display text-3xl font-semibold text-foreground">How it works</h2>
          <div className="mt-12 grid gap-8 sm:grid-cols-3">
            {STEPS.map((step, index) => (
              <div key={step.title} className="text-center">
                <span className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-primary font-display text-lg font-semibold text-primary-foreground">
                  {index + 1}
                </span>
                <h3 className="mt-4 font-display text-lg font-medium text-foreground">{step.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-6 py-20 text-center">
        <h2 className="font-display text-3xl font-semibold text-foreground">Ready to start practicing?</h2>
        <p className="mt-3 text-muted-foreground">Create a free account — no credit card required.</p>
        <Button size="lg" className="mt-6" render={<Link to={ROUTES.register}>Get started</Link>} />
      </section>
    </>
  );
}
