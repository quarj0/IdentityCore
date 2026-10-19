import { expect, test } from "@playwright/test";
import { POST } from "../src/app/api/verification/handoff/route";
import {
  SESSION_COOKIE,
  SESSION_ID_COOKIE,
  sessionCookieName,
} from "../src/lib/bff-session";

test("handoff BFF persists a scoped HttpOnly credential before returning the mobile session", async () => {
  const originalFetch = globalThis.fetch;
  const originalOrigin = process.env.API_ORIGIN;
  process.env.API_ORIGIN = "https://api.example.test";
  globalThis.fetch = async (_url, init) => {
    expect(JSON.parse(String(init?.body))).toEqual({
      handoff: "synthetic-claim",
      session_id: "ses_source",
    });
    return Response.json({
      success: true,
      data: {
        session_id: "ses_mobile",
        session_token: "synthetic-private-token",
      },
    });
  };
  try {
    const response = await POST(
      new Request("https://verify.example.test/api/verification/handoff", {
        method: "POST",
        headers: {
          Origin: "https://verify.example.test",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          handoff: "synthetic-claim",
          session_id: "ses_source",
        }),
      }),
    );
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      success: true,
      data: { session_id: "ses_mobile" },
    });
    expect(response.cookies.get(sessionCookieName("ses_mobile"))).toMatchObject(
      {
        value: "synthetic-private-token",
        httpOnly: true,
        sameSite: "strict",
        path: "/",
      },
    );
    expect(response.cookies.get(SESSION_ID_COOKIE)).toMatchObject({
      value: "",
      maxAge: 0,
      httpOnly: true,
      sameSite: "strict",
      path: "/",
    });
    expect(response.cookies.get(SESSION_COOKIE)).toMatchObject({
      value: "",
      maxAge: 0,
    });
    expect(response.headers.get("cache-control")).toContain("no-store");
  } finally {
    globalThis.fetch = originalFetch;
    if (originalOrigin === undefined) delete process.env.API_ORIGIN;
    else process.env.API_ORIGIN = originalOrigin;
  }
});

test("handoff BFF rejects malformed upstream credentials without exposing them", async () => {
  const originalFetch = globalThis.fetch;
  const originalOrigin = process.env.API_ORIGIN;
  process.env.API_ORIGIN = "https://api.example.test";
  try {
    for (const payload of [
      { data: { session_id: "ses_mobile", session_token: "a".repeat(4096) } },
      null,
      {
        data: {
          session_id: "bad/id",
          session_token: "synthetic-private-token",
        },
      },
      {
        data: {
          session_id: "ses_mobile",
          session_token: { secret: "synthetic-private-token" },
        },
      },
    ]) {
      globalThis.fetch = async () => Response.json(payload);
      const response = await POST(
        new Request("https://verify.example.test/api/verification/handoff", {
          method: "POST",
          headers: {
            Origin: "https://verify.example.test",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ handoff: "synthetic-claim" }),
        }),
      );
      expect(response.status).toBe(502);
      expect(await response.text()).not.toContain("synthetic-private-token");
      expect(
        response.cookies.get(sessionCookieName("ses_mobile")),
      ).toBeUndefined();
    }
  } finally {
    globalThis.fetch = originalFetch;
    if (originalOrigin === undefined) delete process.env.API_ORIGIN;
    else process.env.API_ORIGIN = originalOrigin;
  }
});
