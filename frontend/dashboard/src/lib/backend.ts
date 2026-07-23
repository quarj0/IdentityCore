"use client";

import { createIdentityCoreClient } from "@identitycore/api-client";

let accessToken: string | null = null;
const apiOrigin = process.env.NEXT_PUBLIC_API_ORIGIN ?? "http://localhost:8000";

export const backend = createIdentityCoreClient({
  apiOrigin,
  getAccessToken: () => accessToken,
  setAccessToken: (token) => { accessToken = token; },
});

export async function downloadAuthenticatedFile(path: string, fallbackFilename: string) {
  const response = await fetch(`${apiOrigin}/api/v1${path}`, {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
    credentials: "include",
  });

  if (!response.ok) {
    let message = "Unable to download this evidence file.";
    try {
      const payload = await response.json();
      message = payload?.error?.message ?? payload?.detail ?? message;
    } catch {
      // The API can return a non-JSON upstream error.
    }
    throw new Error(message);
  }

  const blob = await response.blob();
  const disposition = response.headers.get("content-disposition") ?? "";
  const matchedFilename = disposition.match(/filename="?([^";]+)"?/i)?.[1];
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = matchedFilename || fallbackFilename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
