import { LegalPageLayout, LegalSection } from "@/features/marketing/components/LegalPageLayout";

const SECTIONS = [
  { id: "acceptance-of-terms", title: "Acceptance of Terms" },
  { id: "eligibility", title: "Eligibility" },
  { id: "account-registration", title: "Account Registration and Security" },
  { id: "access-and-subscriptions", title: "Access and Subscriptions" },
  { id: "nclex-examination-disclaimer", title: "NCLEX Examination Disclaimer" },
  { id: "acceptable-use", title: "Acceptable Use" },
  { id: "intellectual-property", title: "Intellectual Property" },
  { id: "user-submitted-content", title: "User-Submitted Content" },
  { id: "no-guarantee-of-results", title: "No Guarantee of Exam Results" },
  { id: "not-medical-advice", title: "Not Medical or Clinical Advice" },
  { id: "termination", title: "Termination" },
  { id: "disclaimer-of-warranties", title: "Disclaimer of Warranties" },
  { id: "limitation-of-liability", title: "Limitation of Liability" },
  { id: "governing-law", title: "Governing Law" },
  { id: "changes-to-these-terms", title: "Changes to These Terms" },
  { id: "contact-us", title: "Contact Us" },
];

/**
 * Just the disclaimer's paragraphs — reused both inside the full T&C
 * section below AND as a standalone modal on the registration page
 * (LegalLinkModal in RegisterPage.tsx), so this exact legal text has one
 * source of truth rather than being duplicated into a second place.
 */
export function NclexDisclaimerBody() {
  return (
    <>
      <p>
        NextWise is an independent NCLEX-RN® preparation platform. NextWise does not provide, possess, have access
        to, or reproduce actual NCLEX examination questions or secure examination content. All practice questions
        and educational materials provided through NextWise are independently developed for educational and
        preparation purposes and are not intended to reproduce or predict questions that may appear on the actual
        NCLEX examination.
      </p>
      <p>
        If a question, concept, topic, clinical scenario, or similar material encountered while using NextWise
        happens to appear on your NCLEX examination, this does not mean that the examination content was obtained
        from, provided by, or disclosed by NextWise. NextWise does not guarantee that any specific question,
        concept, topic, or clinical scenario will appear on the NCLEX examination.
      </p>
      <p>
        NextWise makes no guarantee of examination success, a passing result, or any particular examination
        outcome. Your use of NextWise is solely for educational and examination-preparation purposes. To the
        extent permitted by applicable law, NextWise is not responsible for the content, wording, or occurrence of
        questions presented on an individual's actual examination or for any examination result.
      </p>
      <p>
        Users must not submit, upload, reproduce, or share actual NCLEX examination questions, answer choices,
        screenshots, photographs, or other secure examination content through NextWise.
      </p>
      <p>
        By using NextWise, you acknowledge and agree that NextWise is an independent preparation resource and that
        no specific NextWise question or educational material is promised or represented to appear on your actual
        examination.
      </p>
    </>
  );
}

/** Just the section content, no LegalPageLayout wrapper — see PrivacyPolicyBody's comment for why. */
export function TermsAndConditionsBody() {
  return (
    <>
      <LegalSection id="acceptance-of-terms" title="Acceptance of Terms">
        <p>
          By registering for an account or otherwise accessing NextWise, you confirm that you have read, understood,
          and agree to these Terms, as well as our{" "}
          <a href="/privacy-policy" className="text-primary hover:underline">
            Privacy Policy
          </a>
          .
        </p>
      </LegalSection>

      <LegalSection id="eligibility" title="Eligibility">
        <p>
          NextWise is intended for individuals preparing for the NCLEX-RN or NCLEX-PN licensure examinations. You
          must be able to form a legally binding contract to use the Service. If you are under the age of majority
          in your jurisdiction, you may use NextWise only with the involvement of a parent or legal guardian.
        </p>
      </LegalSection>

      <LegalSection id="account-registration" title="Account Registration and Security">
        <ul>
          <li>You must provide accurate, current information when creating your account and keep it up to date.</li>
          <li>You are responsible for maintaining the confidentiality of your password and for all activity that occurs under your account.</li>
          <li>Accounts are personal to you; you may not share your login credentials with, or transfer your account to, another person.</li>
          <li>Notify us promptly at the contact below if you suspect unauthorized use of your account.</li>
        </ul>
      </LegalSection>

      <LegalSection id="access-and-subscriptions" title="Access and Subscriptions">
        <p>
          NextWise is currently in an early-access phase. Some or all features may be provided free of charge during
          this period, without commitment that they will remain free indefinitely. We plan to introduce paid
          subscription plans in the future. Before any paid plan becomes active, we will publish the applicable
          pricing, billing terms, and refund policy, and those terms will apply going forward from that point. They
          are not part of these Terms today.
        </p>
      </LegalSection>

      <LegalSection id="nclex-examination-disclaimer" title="NCLEX Examination Disclaimer">
        <NclexDisclaimerBody />
      </LegalSection>

      <LegalSection id="acceptable-use" title="Acceptable Use">
        <p>You agree not to:</p>
        <ul>
          <li>Copy, scrape, reproduce, redistribute, or publicly share question content, rationales, or other platform materials outside of your personal use.</li>
          <li>Use automated tools (bots, scrapers, scripts) to access the Service, other than as we explicitly permit.</li>
          <li>Attempt to gain unauthorized access to any account, system, or network connected to NextWise.</li>
          <li>Interfere with or disrupt the integrity or performance of the Service.</li>
          <li>Use the Service for any unlawful purpose or in violation of these Terms.</li>
        </ul>
      </LegalSection>

      <LegalSection id="intellectual-property" title="Intellectual Property">
        <p>
          All question content, rationales, taxonomy, branding, and platform software are owned by NextWise
          Education or its licensors and are protected by intellectual property laws. Subject to your compliance
          with these Terms, we grant you a limited, personal, non-exclusive, non-transferable license to access and
          use the Service for your own exam preparation. No other rights are granted.
        </p>
      </LegalSection>

      <LegalSection id="user-submitted-content" title="User-Submitted Content">
        <p>
          When you submit feedback, survey responses, or "Report an Issue" submissions, you grant NextWise a
          non-exclusive, royalty-free license to use that content to review, correct, and improve our question bank
          and platform. Please don't include sensitive personal or protected health information in feedback
          submissions.
        </p>
      </LegalSection>

      <LegalSection id="no-guarantee-of-results" title="No Guarantee of Exam Results">
        <p>
          NCLEX-RN® and NCLEX-PN® are registered trademarks of the National Council of State Boards of Nursing, Inc.
          ("NCSBN"). NextWise Education is an independent exam-preparation resource and is not affiliated with,
          endorsed by, or sponsored by NCSBN. Practice questions, rationales, and performance analytics are provided
          for study purposes only and do not guarantee any particular score or outcome on the actual licensure
          examination.
        </p>
      </LegalSection>

      <LegalSection id="not-medical-advice" title="Not Medical or Clinical Advice">
        <p>
          Content on NextWise is intended for exam-preparation and educational purposes only. It does not constitute
          medical, clinical, or nursing-practice advice and should not be relied upon for patient care decisions.
        </p>
      </LegalSection>

      <LegalSection id="termination" title="Termination">
        <p>
          You may stop using NextWise and request deletion of your account at any time. We may suspend or terminate
          your access if we reasonably believe you have violated these Terms or used the Service in a way that
          creates risk or legal exposure for NextWise or other users.
        </p>
      </LegalSection>

      <LegalSection id="disclaimer-of-warranties" title="Disclaimer of Warranties">
        <p>
          The Service is provided "as is" and "as available," without warranties of any kind, whether express or
          implied, including implied warranties of merchantability, fitness for a particular purpose, and
          non-infringement, to the fullest extent permitted by law.
        </p>
      </LegalSection>

      <LegalSection id="limitation-of-liability" title="Limitation of Liability">
        <p>
          To the fullest extent permitted by law, NextWise Education will not be liable for any indirect,
          incidental, special, consequential, or punitive damages, or any loss of data, revenue, or profits, arising
          from your use of, or inability to use, the Service.
        </p>
      </LegalSection>

      <LegalSection id="governing-law" title="Governing Law">
        <p>
          These Terms are governed by the laws of [State/Country to be confirmed], without regard to its conflict of
          law principles.
        </p>
      </LegalSection>

      <LegalSection id="changes-to-these-terms" title="Changes to These Terms">
        <p>
          We may update these Terms from time to time, particularly as new features (such as paid subscriptions)
          are introduced. We will update the "Last updated" date above when we do. Continued use of NextWise after
          changes take effect constitutes acceptance of the updated Terms.
        </p>
      </LegalSection>

      <LegalSection id="contact-us" title="Contact Us">
        <p>
          Questions about these Terms can be sent to{" "}
          <a href="mailto:support@nextwiseeducation.com" className="text-primary hover:underline">
            support@nextwiseeducation.com
          </a>
          .
        </p>
      </LegalSection>
    </>
  );
}

export function TermsAndConditionsPage() {
  return (
    <LegalPageLayout
      title="Terms and Conditions"
      lastUpdated="August 23, 2026"
      sections={SECTIONS}
      intro={
        <p>
          These Terms and Conditions ("Terms") govern your access to and use of the NextWise Education website and
          platform (together, "NextWise," "the Service"). By creating an account or using the Service, you agree to
          be bound by these Terms. If you do not agree, please do not use the Service.
        </p>
      }
    >
      <TermsAndConditionsBody />
    </LegalPageLayout>
  );
}
