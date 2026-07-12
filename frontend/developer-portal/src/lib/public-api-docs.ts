const DEFAULT_API_ORIGIN =
  process.env.NEXT_PUBLIC_API_ORIGIN ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

function trimTrailingSlash(value: string) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

const API_ORIGIN = trimTrailingSlash(DEFAULT_API_ORIGIN);

export type PublicApiDocsResource = {
  slug: string;
  name: string;
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  category: string;
  description: string;
};

export type PublicApiDocsOverview = {
  api_version: string;
  base_urls: {
    production: string;
    development: string;
  };
  authentication: {
    public_rest: {
      headers: string[];
      optional_headers: string[];
    };
  };
  response_envelope: {
    success: boolean;
    data: Record<string, unknown>;
    request_id: string;
  };
  resources: PublicApiDocsResource[];
  sdk_status: Array<{
    language: string;
    path: string;
    status: string;
    notes: string;
  }>;
};

type PublicDocsEnvelope = {
  success: boolean;
  data: PublicApiDocsOverview;
};

export async function fetchPublicApiDocsOverview(): Promise<
  PublicApiDocsOverview | null
> {
  try {
    const response = await fetch(`${API_ORIGIN}/api/v1/docs/overview`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const payload = (await response.json()) as PublicDocsEnvelope;
    return payload.success ? payload.data : null;
  } catch {
    return null;
  }
}
