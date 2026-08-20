export interface TokenPair {
  access: string;
  refresh: string;
}

export type SubscriptionStatus = "FREE" | "ACTIVE" | "PAST_DUE" | "CANCELED";

export interface Me {
  email: string;
  full_name: string;
  subscription_status: SubscriptionStatus;
}

/**
 * DRF's error shapes vary by endpoint: a page-level failure returns
 * {detail}, a serializer validation failure returns {field: [msg, ...]},
 * and a throttled request returns {detail} too but with a 429 status that
 * callers need to branch on separately from a "real" 400/401.
 */
export interface ApiFieldErrors {
  [field: string]: string[];
}

export interface NormalizedApiError {
  status: number | null;
  detail: string | null;
  fieldErrors: ApiFieldErrors | null;
  isRateLimited: boolean;
}
