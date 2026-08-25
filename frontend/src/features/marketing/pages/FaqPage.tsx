import { Link } from "react-router-dom";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { ROUTES } from "@/lib/constants";

interface FaqItem {
  id: string;
  question: string;
  answer: React.ReactNode;
}

interface FaqCategory {
  title: string;
  items: FaqItem[];
}

const CATEGORIES: FaqCategory[] = [
  {
    title: "General",
    items: [
      {
        id: "what-is-nextwise",
        question: "What is NextWise Education?",
        answer:
          "NextWise is an online practice platform for students preparing for the NCLEX-RN and NCLEX-PN licensure exams, offering practice questions, detailed rationales, and performance tracking, organized around the same Client Needs categories and Clinical Judgment Measurement Model the actual exam uses.",
      },
      {
        id: "ncsbn-affiliation",
        question: "Is NextWise affiliated with NCSBN or the official NCLEX exam?",
        answer:
          "No. NCLEX-RN® and NCLEX-PN® are registered trademarks of the National Council of State Boards of Nursing, Inc. (NCSBN). NextWise Education is an independent exam-preparation resource and is not affiliated with, endorsed by, or sponsored by NCSBN.",
      },
      {
        id: "rn-vs-pn",
        question: "Do you support both NCLEX-RN and NCLEX-PN prep?",
        answer:
          "Our content taxonomy is built to support both tracks. Availability of PN-specific content depends on what's been published to the question bank, so check back as we continue to grow our content library.",
      },
    ],
  },
  {
    title: "Account",
    items: [
      {
        id: "how-to-register",
        question: "How do I create an account?",
        answer: (
          <>
            Select "Get started" from the homepage, enter your name, email, and a password, and submit the form.
            We'll send a verification email to confirm your address, and you'll need to click the link in that email
            before you can log in. See our{" "}
            <Link to={ROUTES.register} className="text-primary hover:underline">
              registration page
            </Link>{" "}
            to begin.
          </>
        ),
      },
      {
        id: "verification-email-missing",
        question: "I didn't receive my verification email. What should I do?",
        answer:
          "Check your spam or junk folder first, since verification emails sometimes land there. If it's genuinely missing after a few minutes, contact support using the details below and we'll help sort it out.",
      },
      {
        id: "forgot-password",
        question: "I forgot my password. How do I reset it?",
        answer: (
          <>
            From the login page, select "Forgot password?" and enter your email address. If an account exists for
            that address, we'll send a link to reset your password. Go to{" "}
            <Link to={ROUTES.forgotPassword} className="text-primary hover:underline">
              Forgot password
            </Link>{" "}
            to start.
          </>
        ),
      },
    ],
  },
  {
    title: "Practice & Content",
    items: [
      {
        id: "question-types-supported",
        question: "Which question types are available right now?",
        answer:
          "Standard multiple-choice (MCQ) and Select All That Apply (SATA) questions are fully interactive today. Additional Next Generation NCLEX formats, including Matrix/Grid, Bow-Tie, Extended Multiple Response, Drag and Drop, Drop-down Cloze, Enhanced Hot Spot, and full NGN Case Studies, are represented in our content schema and are being rolled out to the practice experience next.",
      },
      {
        id: "rationales-included",
        question: "Do practice questions include explanations?",
        answer:
          "Yes. Every question includes a rationale explaining the correct answer, shown immediately after you submit your response, alongside your result.",
      },
      {
        id: "progress-tracking",
        question: "Does NextWise track my progress?",
        answer:
          "Every quiz you complete and every question you answer is recorded to your account, which is what powers performance tracking by category, topic, and difficulty as that dashboard experience continues to expand.",
      },
    ],
  },
  {
    title: "Subscription & Pricing",
    items: [
      {
        id: "is-it-free",
        question: "Is NextWise free to use right now?",
        answer:
          "NextWise is currently in an early-access phase. We'll clearly publish pricing and plan details before any paid subscription goes live, and nothing will be billed to you without that information being available up front.",
      },
      {
        id: "future-trial",
        question: "Will there be a free trial once paid plans launch?",
        answer:
          "Yes. The plan is to offer a limited free trial (a time window and/or a capped number of practice questions) so you can try the full question bank before subscribing. Exact details will be announced alongside pricing.",
      },
    ],
  },
  {
    title: "Feedback & Support",
    items: [
      {
        id: "report-a-question-issue",
        question: "I think a question has an error. How do I report it?",
        answer:
          "While taking a quiz, select the \"🚩 Report an issue\" button on the question and choose what's wrong (an incorrect answer, unclear wording, a rationale that needs work, and so on). You can also flag it from the results review after finishing a quiz.",
      },
      {
        id: "contact-support",
        question: "How do I contact support?",
        answer: (
          <>
            Email us at{" "}
            <a href="mailto:support@nextwiseeducation.com" className="text-primary hover:underline">
              support@nextwiseeducation.com
            </a>{" "}
            and we'll get back to you as soon as we can.
          </>
        ),
      },
    ],
  },
];

export function FaqPage() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-10 px-6 py-16">
      <div className="flex flex-col gap-3">
        <h1 className="font-display text-3xl font-semibold text-foreground sm:text-4xl">
          Frequently Asked Questions
        </h1>
        <p className="text-base leading-relaxed text-muted-foreground">
          Can't find what you're looking for? Reach us at{" "}
          <a href="mailto:support@nextwiseeducation.com" className="text-primary hover:underline">
            support@nextwiseeducation.com
          </a>
          .
        </p>
      </div>

      <div className="flex flex-col gap-8">
        {CATEGORIES.map((category) => (
          <div key={category.title} className="flex flex-col gap-2">
            <h2 className="font-display text-lg font-semibold text-foreground">{category.title}</h2>
            <Accordion className="flex flex-col gap-1 rounded-xl border border-border bg-card px-4">
              {category.items.map((item) => (
                <AccordionItem key={item.id} value={item.id}>
                  <AccordionTrigger>{item.question}</AccordionTrigger>
                  <AccordionContent className="text-muted-foreground">{item.answer}</AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        ))}
      </div>
    </div>
  );
}
