// Auth-specific API calls, built on the generic apiFetch wrapper.

import { apiFetch } from "@/lib/api";
import type {
  AuthResponse,
  LoginPayload,
  RegisterPayload,
  User,
} from "@/lib/types";

export function login(payload: LoginPayload): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: payload,
  });
}

export function register(payload: RegisterPayload): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: payload,
  });
}

export function fetchMe(): Promise<User> {
  return apiFetch<User>("/api/auth/me", { auth: true });
}
