"use client";

import { restRequest } from "@/lib/api-client";
import { clearAuthSession } from "@/lib/auth";

export async function endAuthSession() {
  try {
    await restRequest<{ logged_out: boolean }>(
      "/auth/logout",
      { method: "POST", body: "{}" },
      { useAuth: false },
    );
  } finally {
    clearAuthSession();
  }
}
