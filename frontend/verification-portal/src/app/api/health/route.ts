import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json(
    { status: "ok", service: "verification-portal" },
    { headers: { "Cache-Control": "no-store" } },
  );
}
