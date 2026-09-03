import { Navigate, Outlet } from "react-router-dom";

import { FullPageSpinner } from "@/components/common/LoadingSpinner";
import { useAuth } from "@/features/auth/AuthContext";
import { ROUTES } from "@/lib/constants";
import type { UserRole } from "@/types/api";

interface RequireRoleProps {
  allow: UserRole[];
}

/**
 * Sits inside ProtectedRoute (this route tree is only reached once
 * isAuthenticated is already true), so a role mismatch sends the user to
 * /dashboard rather than /login — they are authenticated, just not
 * authorized for this section, and a login redirect would be nonsensical
 * for someone already past it.
 */
export function RequireRole({ allow }: RequireRoleProps) {
  const { user, isBootstrapping } = useAuth();

  if (isBootstrapping) return <FullPageSpinner label="Loading your account..." />;

  if (!user || !allow.includes(user.role)) {
    return <Navigate to={ROUTES.dashboard} replace />;
  }

  return <Outlet />;
}
