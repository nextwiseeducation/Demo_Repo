import { lazy, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { FullPageSpinner } from "@/components/common/LoadingSpinner";
import { MarketingLayout } from "@/components/layout/MarketingLayout";
import { AdminContentPage } from "@/features/admin/pages/AdminContentPage";
import { AdminFeedbackPage } from "@/features/admin/pages/AdminFeedbackPage";
import { ForgotPasswordPage } from "@/features/auth/pages/ForgotPasswordPage";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { RegisterPage } from "@/features/auth/pages/RegisterPage";
import { ResetPasswordPage } from "@/features/auth/pages/ResetPasswordPage";
import { VerifyEmailPage } from "@/features/auth/pages/VerifyEmailPage";
import { DashboardPage } from "@/features/dashboard/pages/DashboardPage";
import { SettingsPage } from "@/features/settings/pages/SettingsPage";
import { AccessibilityPage } from "@/features/marketing/pages/AccessibilityPage";
import { FaqPage } from "@/features/marketing/pages/FaqPage";
import { LandingPage } from "@/features/marketing/pages/LandingPage";
import { PrivacyPolicyPage } from "@/features/marketing/pages/PrivacyPolicyPage";
import { TermsAndConditionsPage } from "@/features/marketing/pages/TermsAndConditionsPage";
import { QuizResultsPage } from "@/features/quiz/pages/QuizResultsPage";
import { QuizSessionPage } from "@/features/quiz/pages/QuizSessionPage";
import { QuizSetupPage } from "@/features/quiz/pages/QuizSetupPage";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { PublicOnlyRoute } from "@/routes/PublicOnlyRoute";
import { RequireRole } from "@/routes/RequireRole";
import { USER_ROLE } from "@/types/role";

// Lazy + Suspense: recharts (pulled in only by this page) should never be
// part of a student's bundle, since only a superuser can ever reach this
// route.
const AdminAnalyticsPage = lazy(() =>
  import("@/features/admin/pages/AdminAnalyticsPage").then((m) => ({ default: m.AdminAnalyticsPage })),
);

export const router = createBrowserRouter([
  {
    element: <MarketingLayout />,
    children: [
      { path: "/", element: <LandingPage /> },
      { path: "/privacy-policy", element: <PrivacyPolicyPage /> },
      { path: "/terms-and-conditions", element: <TermsAndConditionsPage /> },
      { path: "/accessibility", element: <AccessibilityPage /> },
      { path: "/faq", element: <FaqPage /> },
    ],
  },
  {
    element: <AuthLayout />,
    children: [
      {
        element: <PublicOnlyRoute />,
        children: [
          { path: "/register", element: <RegisterPage /> },
          { path: "/login", element: <LoginPage /> },
          { path: "/forgot-password", element: <ForgotPasswordPage /> },
          { path: "/reset-password", element: <ResetPasswordPage /> },
        ],
      },
      { path: "/verify-email", element: <VerifyEmailPage /> },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: "/dashboard", element: <DashboardPage /> },
          { path: "/settings", element: <SettingsPage /> },
          { path: "/quiz", element: <QuizSetupPage /> },
          { path: "/quiz/session", element: <QuizSessionPage /> },
          { path: "/quiz/results", element: <QuizResultsPage /> },
          {
            element: <RequireRole allow={[USER_ROLE.SUPERUSER]} />,
            children: [
              {
                path: "/admin/analytics",
                element: (
                  <Suspense fallback={<FullPageSpinner label="Loading analytics..." />}>
                    <AdminAnalyticsPage />
                  </Suspense>
                ),
              },
            ],
          },
          {
            element: <RequireRole allow={[USER_ROLE.SUPERUSER, USER_ROLE.CONTENT_ADMIN]} />,
            children: [
              { path: "/admin/content", element: <AdminContentPage /> },
              { path: "/admin/feedback", element: <AdminFeedbackPage /> },
            ],
          },
        ],
      },
    ],
  },
]);
