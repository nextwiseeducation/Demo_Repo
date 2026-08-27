import type { Me, TokenPair } from "@/types/api";

import { apiClient } from "./client";

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  accepted_disclaimer: boolean;
  accepted_terms: boolean;
}

export function register(payload: RegisterPayload) {
  return apiClient.post<{ detail: string }>("/auth/register/", payload).then((r) => r.data);
}

export function verifyEmail(token: string) {
  return apiClient.get<{ detail: string }>(`/auth/verify-email/${token}/`).then((r) => r.data);
}

export function login(payload: { email: string; password: string }) {
  return apiClient.post<TokenPair>("/auth/login/", payload).then((r) => r.data);
}

export function logout(refresh: string) {
  return apiClient.post("/auth/logout/", { refresh });
}

export function requestPasswordReset(email: string) {
  return apiClient.post<{ detail: string }>("/auth/password-reset/", { email }).then((r) => r.data);
}

export function confirmPasswordReset(payload: { uid: string; token: string; new_password: string }) {
  return apiClient.post<{ detail: string }>("/auth/password-reset/confirm/", payload).then((r) => r.data);
}

export function getMe() {
  return apiClient.get<Me>("/auth/me/").then((r) => r.data);
}
