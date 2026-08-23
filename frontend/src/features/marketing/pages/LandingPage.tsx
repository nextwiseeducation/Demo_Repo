import {
  BookOpenCheck,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock,
  FileCheck,
  Layers,
  ListChecks,
  MessageSquareQuote,
  Quote,
  RotateCcw,
  User,
} from "lucide-react";
import { Link } from "react-router-dom";

import heroBgImage from "@/assets/marketing/hero-bg.jpg";
import nurseImage from "@/assets/marketing/nurse-portrait.jpg";
import readyImage from "@/assets/marketing/ready.jpg";
import simLabImage from "@/assets/marketing/sim-lab.jpg";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MCQChoiceList } from "@/features/quiz/components/MCQChoiceList";
import { QuestionCard } from "@/features/quiz/components/QuestionCard";
import { MOCK_QUESTIONS } from "@/features/quiz/data/mockQuestions";
import { ROUTES } from "@/lib/constants";

const STATS = [
  { icon: Layers, value: "9", label: "NGN-ready question types" },
  { icon: BookOpenCheck, value: "6", label: "Clinical Judgment Model steps" },
  { icon: MessageSquareQuote, value: "100%", label: "of answers come with a rationale" },
  { icon: ListChecks, value: "NCLEX", label: "Client Needs-aligned categories" },
];

const FEATURES = [
  {
    icon: Layers,
    title: "9 NGN-ready question types",
    points: ["Matrix/Grid & Bow-Tie", "Extended Multiple Response", "Drag and Drop & Cloze", "Enhanced Hot Spot & Case Studies"],
  },
  {
    icon: BookOpenCheck,
    title: "Built on NCSBN's Clinical Judgment Model",
    points: ["Recognize Cues & Analyze Cues", "Prioritize Hypotheses", "Generate Solutions & Take Action", "Evaluate Outcomes"],
  },
  {
    icon: MessageSquareQuote,
    title: "A rationale for every answer",
    points: ["Rationale for the correct answer", "Rationale for every incorrect option", "Written in plain clinical language", "Shown right after you answer"],
  },
  {
    icon: ListChecks,
    title: "Organized by NCLEX Client Needs category",
    points: ["Filter practice by Client Needs category", "Filter by subcategory", "Matches the real exam's weighting", "Track performance by category over time"],
  },
];

const STEPS = [
  { title: "Register", description: "Create your account and verify your email in under a minute." },
  { title: "Practice", description: "Work through NGN-style questions filtered to what you need to focus on." },
  { title: "Review", description: "Read the rationale behind every answer and track where you're improving." },
];

/**
 * No beta cohort exists yet — Milestone 1 is still auth/schema foundation —
 * so these are placeholders, not real quotes. Swap in real testimonials once
 * students have practiced with NextWise.
 */
const TESTIMONIALS = [
  { role: "NCLEX-RN candidate" },
  { role: "NCLEX-PN candidate" },
  { role: "Nursing program graduate" },
];

const PERKS = [
  { icon: Clock, title: "Configurable timer", description: "Set your own pace, or simulate real exam conditions." },
  { icon: RotateCcw, title: "Resume mid-quiz", description: "Session state is saved automatically — pick up right where you left off." },
  { icon: FileCheck, title: "A rationale for every choice", description: "Not just the correct one — understand why each distractor is wrong." },
];

export function LandingPage() {
  return (
    <>
      <section className="relative overflow-hidden bg-primary">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `url(${heroBgImage})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />
        <div className="absolute inset-0 bg-primary/70" />
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
            <QuestionCard question={MOCK_QUESTIONS[0]} showReportButton={false}>
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

      <div className="relative z-10 mx-auto -mt-10 max-w-6xl px-6">
        <div className="grid gap-6 rounded-xl border border-border/80 bg-card p-7 shadow-[0_20px_40px_-18px_rgba(67,56,202,0.3)] sm:grid-cols-2 lg:flex lg:justify-between">
          {STATS.map((stat) => (
            <div key={stat.label} className="flex items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                <stat.icon className="h-5 w-5" />
              </span>
              <div>
                <div className="font-display text-xl font-semibold leading-tight text-foreground">{stat.value}</div>
                <div className="text-sm text-foreground">{stat.label}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <section id="features" className="mx-auto max-w-6xl px-6 pt-32 pb-20">
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
              <ul className="mt-3 flex flex-col gap-2">
                {feature.points.map((point) => (
                  <li key={point} className="flex items-start gap-2 text-sm leading-relaxed text-foreground">
                    <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                    {point}
                  </li>
                ))}
              </ul>
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
                <p className="mt-2 text-[15px] text-foreground">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-semibold text-foreground">What students are saying</h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Placeholder — real student testimonials will replace this once the beta cohort has practiced with NextWise.
          </p>
        </div>
        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {TESTIMONIALS.map((testimonial) => (
            <div key={testimonial.role} className="flex flex-col gap-4 rounded-xl border border-border bg-card p-6">
              <Quote className="h-6 w-6 text-accent" />
              <p className="text-sm leading-relaxed text-foreground italic">
                "Add a real student quote here once you have beta feedback."
              </p>
              <div className="mt-auto flex items-center gap-2.5 border-t border-border pt-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
                  <User className="h-4 w-4" />
                </span>
                <div>
                  <div className="text-sm font-medium text-foreground">Student name</div>
                  <div className="text-sm text-foreground">{testimonial.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-8 flex justify-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full border border-border text-foreground">
            <ChevronLeft className="h-4 w-4" />
          </span>
          <span className="flex h-10 w-10 items-center justify-center rounded-full border border-border text-foreground">
            <ChevronRight className="h-4 w-4" />
          </span>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="relative">
          <img
            src={simLabImage}
            alt="Nursing student practicing on a clinical simulation mannequin"
            className="aspect-[21/9] w-full rounded-xl object-cover ring-1 ring-foreground/10"
          />
          <div className="absolute -bottom-5 left-6 flex max-w-[280px] items-center gap-3 rounded-xl bg-card p-3.5 shadow-[0_16px_32px_-12px_rgba(17,24,39,0.25)] ring-1 ring-foreground/10">
            <img src={nurseImage} alt="" className="h-10 w-10 shrink-0 rounded-full object-cover" />
            <span className="text-sm leading-tight font-medium text-foreground">
              Content shaped by nursing educators, not generic trivia
            </span>
          </div>
        </div>
        <div className="mt-16 grid gap-12 lg:grid-cols-2">
          <div>
            <p className="font-serif text-lg text-accent italic">Practice like it's the real exam.</p>
            <h2 className="mt-3 font-display text-3xl font-semibold text-foreground">
              Every question grounded in a real clinical picture
            </h2>
            <p className="mt-4 leading-relaxed text-muted-foreground">
              No abstract trivia — every scenario mirrors the assessments, findings, and priority calls you'll
              actually make on the floor. Built to develop judgment, not just recall.
            </p>
          </div>
          <div className="flex flex-col gap-5">
            {PERKS.map((perk) => (
              <div key={perk.title} className="flex items-start gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                  <perk.icon className="h-4 w-4" />
                </span>
                <div>
                  <div className="text-[15px] font-medium text-foreground">{perk.title}</div>
                  <div className="mt-0.5 text-sm text-foreground">{perk.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <div>
            <h2 className="font-display text-3xl font-semibold text-foreground">Ready to start practicing?</h2>
            <p className="mt-3 text-foreground">Create a free account — no credit card required.</p>
            <Button size="lg" className="mt-6" render={<Link to={ROUTES.register}>Get started</Link>} />
          </div>
          <img
            src={readyImage}
            alt="Nurse ready to start practicing with NextWise"
            className="aspect-[4/3] w-full rounded-xl object-cover ring-1 ring-foreground/10"
          />
        </div>
      </section>
    </>
  );
}
