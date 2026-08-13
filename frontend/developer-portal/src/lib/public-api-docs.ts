const DEFAULT_API_ORIGIN = "http://localhost:8000";

function configuredApiOrigin() {
  const configuredOrigin = process.env.NEXT_PUBLIC_API_ORIGIN?.trim();
  if (configuredOrigin) {
    try {
      return new URL(configuredOrigin).origin;
    } catch {
      return configuredOrigin;
    }
  }

  // Keep compatibility with the older API_URL setting, which may include
  // /api/v1. The portal always needs the origin when constructing URLs.
  const configuredBase = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configuredBase) {
    try {
      return new URL(configuredBase).origin;
    } catch {
      return configuredBase.replace(/\/api\/v1\/?$/, "");
    }
  }

  return DEFAULT_API_ORIGIN;
}

function trimTrailingSlash(value: string) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

export const PUBLIC_API_ORIGIN = trimTrailingSlash(configuredApiOrigin());

export function buildPublicApiUrl(path: string) {
  return `${PUBLIC_API_ORIGIN}${path.startsWith("/") ? path : `/${path}`}`;
}

export type PublicApiDocsResource = {
  slug: string;
  name: string;
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  category: string;
  description: string;
  security?: Array<Record<string, string[]>>;
  request_body?: {
    required: boolean;
    content_type: string;
    example: unknown;
  } | null;
};

export type PublicApiDocsOverview = {
  api_version: string;
  base_urls: {
    production: string;
    development: string;
  };
  spec_url?: string;
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

export async function fetchPublicApiDocsOverview(): Promise<PublicApiDocsOverview | null> {
  try {
    const response = await fetch(`${PUBLIC_API_ORIGIN}/api/v1/docs/overview`, {
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
