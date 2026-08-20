import { Navigate, Outlet } from "react-router-dom";

import { FullPageSpinner } from "@/components/common/LoadingSpinner";
import { useAuth } from "@/features/auth/AuthContext";
import { ROUTES } from "@/lib/constants";

/** Keeps logged-in users off /login, /register, etc. — redirected to the dashboard instead. */
export function PublicOnlyRoute() {
  const { isAuthenticated, isBootstrapping } = useAuth();

  if (isBootstrapping) return <FullPageSpinner />;
  if (isAuthenticated) return <Navigate to={ROUTES.dashboard} replace />;

  return <Outlet />;
}
