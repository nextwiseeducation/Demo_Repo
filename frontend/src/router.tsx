import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { MarketingLayout } from "@/components/layout/MarketingLayout";
import { ForgotPasswordPage } from "@/features/auth/pages/ForgotPasswordPage";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { RegisterPage } from "@/features/auth/pages/RegisterPage";
import { ResetPasswordPage } from "@/features/auth/pages/ResetPasswordPage";
import { VerifyEmailPage } from "@/features/auth/pages/VerifyEmailPage";
import { DashboardPage } from "@/features/dashboard/pages/DashboardPage";
import { LandingPage } from "@/features/marketing/pages/LandingPage";
import { QuizResultsPage } from "@/features/quiz/pages/QuizResultsPage";
import { QuizSessionPage } from "@/features/quiz/pages/QuizSessionPage";
import { QuizSetupPage } from "@/features/quiz/pages/QuizSetupPage";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { PublicOnlyRoute } from "@/routes/PublicOnlyRoute";

export const router = createBrowserRouter([
  {
    element: <MarketingLayout />,
    children: [{ path: "/", element: <LandingPage /> }],
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
          { path: "/quiz", element: <QuizSetupPage /> },
          { path: "/quiz/session", element: <QuizSessionPage /> },
          { path: "/quiz/results", element: <QuizResultsPage /> },
        ],
      },
    ],
  },
]);
