import { NextResponse } from "next/server";
import { buildPublicApiUrl } from "@/lib/public-api-docs";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const response = await fetch(
      buildPublicApiUrl("/api/v1/docs/openapi.yaml"),
      { cache: "no-store" },
    );

    if (!response.ok) {
      return NextResponse.json(
        { error: "The API contract is temporarily unavailable." },
        { status: 502 },
      );
    }

    return new NextResponse(await response.text(), {
      headers: {
        "Content-Type": "text/yaml; charset=utf-8",
        "Cache-Control": "public, max-age=300, stale-while-revalidate=3600",
      },
    });
  } catch {
    return NextResponse.json(
      { error: "The API contract is temporarily unavailable." },
      { status: 502 },
    );
  }
}
