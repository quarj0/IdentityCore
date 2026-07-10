"use client";

const ACCESS_TOKEN_KEY = "identitycore.access_token";
const USER_KEY = "identitycore.user";
let accessToken: string | null = null;

export interface AuthUser {
  public_id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  status: string;
  tenant_public_id: string | null;
  is_platform_admin: boolean;
  mfa_enabled: boolean;
  roles: string[];
}

export interface AuthSession {
  accessToken: string;
  user: AuthUser;
}

function canUseStorage() {
  return typeof window !== "undefined";
}

export function saveAuthSession(session: AuthSession) {
  if (!canUseStorage()) {
    return;
  }

  accessToken = session.accessToken;
  window.sessionStorage.setItem(ACCESS_TOKEN_KEY, session.accessToken);
  window.localStorage.setItem(USER_KEY, JSON.stringify(session.user));
}

export function clearAuthSession() {
  if (!canUseStorage()) {
    return;
  }

  accessToken = null;
  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function getAccessToken() {
  if (!canUseStorage()) {
    return null;
  }

  accessToken ??= window.sessionStorage.getItem(ACCESS_TOKEN_KEY);
  return accessToken;
}

export function getStoredUser() {
  if (!canUseStorage()) {
    return null;
  }

  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    clearAuthSession();
    return null;
  }
}
