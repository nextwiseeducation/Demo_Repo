import { ROUTES } from "@/lib/constants";
import type { UserRole } from "@/types/api";

export const USER_ROLE = {
  STUDENT: "STUDENT",
  CONTENT_ADMIN: "CONTENT_ADMIN",
  SUPERUSER: "SUPERUSER",
} as const satisfies Record<UserRole, UserRole>;

export const USER_ROLE_LABELS: Record<UserRole, string> = {
  STUDENT: "Student",
  CONTENT_ADMIN: "Content admin",
  SUPERUSER: "Superuser",
};

export function isSuperuser(role: UserRole | undefined): boolean {
  return role === USER_ROLE.SUPERUSER;
}

export function isContentAdminOrAbove(role: UserRole | undefined): boolean {
  return role === USER_ROLE.CONTENT_ADMIN || role === USER_ROLE.SUPERUSER;
}

export interface AdminNavItem {
  to: string;
  label: string;
  allow: UserRole[];
}

/**
 * The single source of truth for which admin nav items exist and who may
 * see them. AppShell filters this list to render the nav, and router.tsx's
 * RequireRole guards use the same `allow` arrays — so a nav link can never
 * point at a route the guard would reject. Keep both call sites reading
 * from here rather than restating the role lists locally.
 */
export const ADMIN_NAV_ITEMS: AdminNavItem[] = [
  {
    to: ROUTES.adminAnalytics,
    label: "Business Analytics",
    allow: [USER_ROLE.SUPERUSER],
  },
  {
    to: ROUTES.adminContent,
    label: "Content Team",
    allow: [USER_ROLE.SUPERUSER, USER_ROLE.CONTENT_ADMIN],
  },
  {
    to: ROUTES.adminFeedback,
    label: "Feedback",
    allow: [USER_ROLE.SUPERUSER, USER_ROLE.CONTENT_ADMIN],
  },
];

export function visibleAdminNavItems(role: UserRole | undefined): AdminNavItem[] {
  if (!role) return [];
  return ADMIN_NAV_ITEMS.filter((item) => item.allow.includes(role));
}
