import { LegalPageLayout, LegalSection } from "@/features/marketing/components/LegalPageLayout";

const SECTIONS = [
  { id: "our-commitment", title: "Our Commitment" },
  { id: "conformance-target", title: "Conformance Target" },
  { id: "measures-we-take", title: "Measures We Take" },
  { id: "known-limitations", title: "Known Limitations" },
  { id: "feedback", title: "Feedback" },
];

export function AccessibilityPage() {
  return (
    <LegalPageLayout
      title="Accessibility Statement"
      lastUpdated="August 23, 2026"
      sections={SECTIONS}
      intro={
        <p>
          NextWise Education is committed to making our platform usable by as many students as possible, including
          students who use assistive technology such as screen readers or keyboard-only navigation.
        </p>
      }
    >
      <LegalSection id="our-commitment" title="Our Commitment">
        <p>
          Nursing students preparing for the NCLEX come from every kind of background and ability, and we want
          NextWise to work well for all of them. Accessibility is something we actively build for, not an
          afterthought we address after launch.
        </p>
      </LegalSection>

      <LegalSection id="conformance-target" title="Conformance Target">
        <p>
          We aim for our platform to conform to the Web Content Accessibility Guidelines (WCAG) 2.1, Level AA. This
          is an ongoing target we design and test against as the platform grows, rather than a certification we are
          claiming to have already independently audited.
        </p>
      </LegalSection>

      <LegalSection id="measures-we-take" title="Measures We Take">
        <ul>
          <li>Interactive components (menus, dialogs, radio groups, checkboxes, accordions) are built on accessible component primitives with proper keyboard support and ARIA semantics, rather than custom controls built from scratch.</li>
          <li>The site is navigable by keyboard alone, with visible focus indicators on interactive elements.</li>
          <li>Color choices are checked for reasonable contrast against their backgrounds, and status is never conveyed by color alone (for example, correct/incorrect answers are also marked with icons and text, not just green/red coloring).</li>
          <li>Pages use semantic HTML structure (headings, landmarks, labeled form fields) to support screen readers.</li>
        </ul>
      </LegalSection>

      <LegalSection id="known-limitations" title="Known Limitations">
        <p>
          NextWise is under active development. Some Next Generation NCLEX question formats (such as Matrix/Grid,
          Bow-Tie, Drag and Drop, and Enhanced Hot Spot items) are not yet fully interactive in the product and are
          being built out; we are designing their accessibility in from the start rather than retrofitting it later.
          If you encounter a specific barrier, please let us know using the feedback option below so we can
          prioritize it.
        </p>
      </LegalSection>

      <LegalSection id="feedback" title="Feedback">
        <p>
          If you experience an accessibility barrier anywhere on NextWise, we want to hear about it. While signed
          in, you can use the "Report an Issue" option on any question, or you can contact us directly at{" "}
          <a href="mailto:accessibility@nextwiseeducation.com" className="text-primary hover:underline">
            accessibility@nextwiseeducation.com
          </a>
          . Please include the page you were on and, if possible, the assistive technology and browser you were
          using — it helps us reproduce and fix the issue faster.
        </p>
      </LegalSection>
    </LegalPageLayout>
  );
}
