import { Link, Outlet } from "react-router-dom";

import logoFull from "@/assets/marketing/logo-full.png";
import logoMark from "@/assets/marketing/logo-mark.png";
import "@/features/marketing/pages/LandingPage.css";
import { ROUTES } from "@/lib/constants";

export function MarketingLayout() {
  return (
    <div className="nw-land flex min-h-screen flex-col">
      <header>
        <div className="wrap hdr">
          <Link to={ROUTES.home} aria-label="NextWise home">
            <img src={logoFull} alt="NextWise" />
          </Link>
          <nav>
            <a href="/#demo">Practice</a>
            <a href="/#ngn">NGN</a>
            <a href="/#features">Features</a>
            <a href="/#pricing">Pricing</a>
            <a href="/#faq">FAQ</a>
          </nav>
          <div className="hdr-act">
            <Link className="btn btn-ghost" to={ROUTES.login}>
              Log In
            </Link>
            <Link className="btn btn-cta" to={ROUTES.register}>
              Start Practicing Free
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer>
        <div className="wrap">
          <div className="foot">
            <div className="foot-brand">
              <img src={logoMark} alt="" /> NextWise
            </div>
            <div className="foot-links foot-links-grouped">
              <div className="foot-col">
                <span className="foot-col-label">Product</span>
                <a href="/#features">Features</a>
                <a href="/#how">How it works</a>
              </div>
              <div className="foot-col">
                <span className="foot-col-label">Support</span>
                <Link to={ROUTES.faq}>FAQ</Link>
                <a href="mailto:support@nextwiseeducation.com">Contact us</a>
              </div>
              <div className="foot-col">
                <span className="foot-col-label">Legal</span>
                <Link to={ROUTES.privacyPolicy}>Privacy Policy</Link>
                <Link to={ROUTES.termsAndConditions}>Terms and Conditions</Link>
                <Link to={ROUTES.accessibility}>Accessibility</Link>
              </div>
            </div>
            <span>© {new Date().getFullYear()} NextWise Education. All rights reserved.</span>
          </div>
          <p className="disclaim">
            NCLEX-RN is a registered trademark of the National Council of State Boards of Nursing (NCSBN). NextWise
            is an independent preparation platform and is not endorsed by, approved by, or affiliated with NCSBN.
            Dashboard and performance figures shown on this page are demo data used to illustrate the interface.
            Features described as in development or coming soon are not yet available.
          </p>
        </div>
      </footer>
    </div>
  );
}
