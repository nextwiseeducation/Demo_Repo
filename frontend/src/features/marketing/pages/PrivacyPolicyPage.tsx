import { LegalPageLayout, LegalSection } from "@/features/marketing/components/LegalPageLayout";

const SECTIONS = [
  { id: "information-we-collect", title: "Information We Collect" },
  { id: "how-we-use-information", title: "How We Use Your Information" },
  { id: "how-information-is-shared", title: "How Information Is Shared" },
  { id: "cookies-and-local-storage", title: "Cookies and Local Storage" },
  { id: "data-storage-and-security", title: "Data Storage and Security" },
  { id: "your-rights-and-choices", title: "Your Rights and Choices" },
  { id: "childrens-privacy", title: "Children's Privacy" },
  { id: "california-privacy-rights", title: "California Privacy Rights" },
  { id: "changes-to-this-policy", title: "Changes to This Policy" },
  { id: "contact-us", title: "Contact Us" },
];

export function PrivacyPolicyPage() {
  return (
    <LegalPageLayout
      title="Privacy Policy"
      lastUpdated="August 23, 2026"
      sections={SECTIONS}
      intro={
        <p>
          NextWise Education ("NextWise," "we," "us," or "our") provides an online NCLEX-RN and NCLEX-PN exam
          preparation platform. This Privacy Policy explains what personal information we collect, how we use it,
          and the choices you have. By creating an account or otherwise using NextWise, you agree to the practices
          described here.
        </p>
      }
    >
      <LegalSection id="information-we-collect" title="Information We Collect">
        <p>We collect information in the following ways:</p>
        <ul>
          <li>
            <strong>Account information</strong> you provide directly: your name, email address, and password
            (stored only as a one-way cryptographic hash — we never store or have access to your plain-text
            password).
          </li>
          <li>
            <strong>Study activity</strong>: which practice questions you answer, which answer choices you select,
            whether your answers were correct, how long you spend on each question, and the quiz sessions you
            complete. We keep this detail — not just a pass/fail summary — so we can show you meaningful progress
            and, in a future release, explain specifically why an answer was incorrect.
          </li>
          <li>
            <strong>Feedback you submit</strong>, including end-of-quiz survey responses and any "Report an Issue"
            submissions you make about a specific question.
          </li>
          <li>
            <strong>Technical information</strong> collected automatically, such as IP address, browser type, and
            device information, generated as a standard part of operating a secure web application (for example, in
            server request logs).
          </li>
        </ul>
        <p>
          We do not currently use third-party advertising trackers, and we do not sell your personal information.
        </p>
      </LegalSection>

      <LegalSection id="how-we-use-information" title="How We Use Your Information">
        <ul>
          <li>To create and secure your account, including verifying your email address and resetting your password.</li>
          <li>To operate the practice platform: serving questions, scoring your answers, and saving your progress.</li>
          <li>To respond to feedback and issue reports and to improve the quality of our question bank over time.</li>
          <li>To send you service-related email (account verification, password reset, and similar operational messages).</li>
          <li>To maintain the security and integrity of the platform, including detecting abuse of our systems.</li>
        </ul>
        <p>
          NextWise does not currently offer paid subscriptions. If we introduce paid plans in the future, we will
          update this policy to describe how billing information is collected and used before that feature becomes
          active.
        </p>
      </LegalSection>

      <LegalSection id="how-information-is-shared" title="How Information Is Shared">
        <p>
          We do not sell your personal information. We share information only with the following categories of
          third parties, and only as needed to operate the service:
        </p>
        <ul>
          <li>
            <strong>Infrastructure and hosting providers</strong> that run our servers and database.
          </li>
          <li>
            <strong>Email delivery providers</strong> we use to send verification, password-reset, and other
            transactional email.
          </li>
          <li>
            <strong>Legal and safety disclosures</strong>, if required to comply with a valid legal process or to
            protect the rights, safety, or property of NextWise, our users, or others.
          </li>
        </ul>
      </LegalSection>

      <LegalSection id="cookies-and-local-storage" title="Cookies and Local Storage">
        <p>
          NextWise uses browser storage that is necessary to keep you signed in — specifically, your session's
          refresh token is kept in your browser's local storage so you don't need to log in every time you visit.
          We do not currently use cookies for advertising or cross-site tracking.
        </p>
      </LegalSection>

      <LegalSection id="data-storage-and-security" title="Data Storage and Security">
        <p>
          We use industry-standard measures to protect your information, including encrypting data in transit
          (HTTPS/TLS) and storing passwords using a salted, one-way hash rather than plain text. No method of
          transmission or storage is 100% secure, and we cannot guarantee absolute security, but we work to protect
          your information using measures appropriate to its sensitivity.
        </p>
      </LegalSection>

      <LegalSection id="your-rights-and-choices" title="Your Rights and Choices">
        <ul>
          <li>You may review and update your account information at any time while logged in.</li>
          <li>You may request a copy of the personal information we hold about you.</li>
          <li>You may request that we delete your account and associated personal information, subject to any records we are legally required to keep.</li>
          <li>You may unsubscribe from non-essential email communications; we will still send essential account and security messages (such as password-reset emails) when you request them.</li>
        </ul>
        <p>To exercise any of these rights, contact us using the details in "Contact Us" below.</p>
      </LegalSection>

      <LegalSection id="childrens-privacy" title="Children's Privacy">
        <p>
          NextWise is intended for nursing students preparing for a professional licensure exam and is not directed
          to children. We do not knowingly collect personal information from children under 13. If you believe a
          child has provided us with personal information, please contact us so we can delete it.
        </p>
      </LegalSection>

      <LegalSection id="california-privacy-rights" title="California Privacy Rights">
        <p>
          If you are a California resident, you may have additional rights under the California Consumer Privacy
          Act (CCPA), including the right to know what personal information we collect, the right to request
          deletion of your personal information, and the right to non-discrimination for exercising these rights. We
          do not sell personal information. To make a request, contact us using the details below.
        </p>
      </LegalSection>

      <LegalSection id="changes-to-this-policy" title="Changes to This Policy">
        <p>
          We may update this Privacy Policy from time to time, for example as we introduce new features such as
          paid subscriptions. We will update the "Last updated" date at the top of this page when we do, and where
          changes are material, we will provide additional notice.
        </p>
      </LegalSection>

      <LegalSection id="contact-us" title="Contact Us">
        <p>
          If you have questions about this Privacy Policy or want to exercise any of the rights described above,
          contact us at{" "}
          <a href="mailto:privacy@nextwiseeducation.com" className="text-primary hover:underline">
            privacy@nextwiseeducation.com
          </a>
          .
        </p>
      </LegalSection>
    </LegalPageLayout>
  );
}
