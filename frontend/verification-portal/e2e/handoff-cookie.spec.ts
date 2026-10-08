import { expect, test } from "@playwright/test";
import { POST } from "../src/app/api/verification/handoff/route";
import { SESSION_COOKIE, SESSION_ID_COOKIE } from "../src/lib/bff-session";

test("handoff BFF persists both HttpOnly credentials before returning the mobile session", async () => {
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
    expect(response.cookies.get(SESSION_COOKIE)).toMatchObject({
      value: "synthetic-private-token",
      httpOnly: true,
      sameSite: "strict",
      path: "/",
    });
    expect(response.cookies.get(SESSION_ID_COOKIE)).toMatchObject({
      value: "ses_mobile",
      httpOnly: true,
      sameSite: "strict",
      path: "/",
    });
    expect(response.headers.get("cache-control")).toContain("no-store");
  } finally {
    globalThis.fetch = originalFetch;
    if (originalOrigin === undefined) delete process.env.API_ORIGIN;
    else process.env.API_ORIGIN = originalOrigin;
  }
});
