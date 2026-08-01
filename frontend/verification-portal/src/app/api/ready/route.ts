import { NextResponse } from "next/server";
import { runtimeConfiguration } from "@/lib/bff-session";

export function GET() {
  const configuration = runtimeConfiguration();
  const ready = configuration.errors.length === 0;

  return NextResponse.json(
    {
      status: ready ? "ready" : "not_ready",
      service: "verification-portal",
      version: process.env.DEPLOYMENT_VERSION ?? "unknown",
      checks: { runtime_configuration: ready ? "ok" : "failed" },
    },
    {
      status: ready ? 200 : 503,
      headers: { "Cache-Control": "no-store" },
    },
  );
}
