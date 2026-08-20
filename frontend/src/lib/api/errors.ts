import { isAxiosError } from "axios";

import type { NormalizedApiError } from "@/types/api";

/**
 * DRF's error shapes vary by failure type: {detail} for a dead link/bad
 * credentials/throttling, {field: [msg]} for serializer validation. Callers
 * need to branch on which one they got — e.g. reset-password-confirm shows
 * a full-page "link expired" state for {detail} but keeps the form usable
 * for field errors, and 429s get their own distinct messaging everywhere.
 */
export function normalizeApiError(error: unknown): NormalizedApiError {
  if (!isAxiosError(error)) {
    return { status: null, detail: "Something went wrong. Please try again.", fieldErrors: null, isRateLimited: false };
  }

  const status = error.response?.status ?? null;
  const data = error.response?.data as Record<string, unknown> | undefined;
  const isRateLimited = status === 429;

  if (!data) {
    return { status, detail: "Something went wrong. Please try again.", fieldErrors: null, isRateLimited };
  }

  if (typeof data.detail === "string") {
    return { status, detail: data.detail, fieldErrors: null, isRateLimited };
  }

  const fieldErrors: Record<string, string[]> = {};
  for (const [key, value] of Object.entries(data)) {
    if (Array.isArray(value)) {
      fieldErrors[key] = value.map(String);
    }
  }

  if (Object.keys(fieldErrors).length > 0) {
    return { status, detail: null, fieldErrors, isRateLimited };
  }

  return { status, detail: "Something went wrong. Please try again.", fieldErrors: null, isRateLimited };
}
