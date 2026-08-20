import { Navigate, Outlet, useLocation } from "react-router-dom";

import { FullPageSpinner } from "@/components/common/LoadingSpinner";
import { useAuth } from "@/features/auth/AuthContext";
import { ROUTES } from "@/lib/constants";

export function ProtectedRoute() {
  const { isAuthenticated, isBootstrapping } = useAuth();
  const location = useLocation();

  if (isBootstrapping) return <FullPageSpinner label="Loading your account..." />;

  if (!isAuthenticated) {
    const redirect = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`${ROUTES.login}?redirect=${redirect}`} replace />;
  }

  return <Outlet />;
}
