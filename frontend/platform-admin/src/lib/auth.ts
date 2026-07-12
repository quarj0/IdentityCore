"use client";

const ACCESS_TOKEN_KEY = "identitycore.access_token";
let accessToken: string | null = null;

function canUseStorage() {
  return typeof window !== "undefined";
}

export function getAccessToken() {
  if (!canUseStorage()) {
    return null;
  }

  accessToken ??= window.sessionStorage.getItem(ACCESS_TOKEN_KEY);
  return accessToken;
}

export function setAccessToken(token: string | null) {
  if (!canUseStorage()) {
    return;
  }

  accessToken = token;
  if (token) {
    window.sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
  } else {
    window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

