const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "[::1]"]);

function configuredReturnOrigins() {
  return new Set(
    (process.env.NEXT_PUBLIC_ALLOWED_RETURN_ORIGINS ?? "")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean)
      .flatMap((value) => {
        try {
          return [new URL(value).origin];
        } catch {
          return [];
        }
      }),
  );
}

function isAllowedReturnUrl(value: string, portalOrigin: string) {
  try {
    const url = new URL(value);
    if (url.username || url.password) return false;

    const isLocalDevelopmentUrl =
      process.env.NODE_ENV !== "production" &&
      url.protocol === "http:" &&
      LOCAL_HOSTS.has(url.hostname);
    if (url.protocol !== "https:" && !isLocalDevelopmentUrl) return false;

    const allowedOrigins = configuredReturnOrigins();
    return (
      url.origin === portalOrigin ||
      allowedOrigins.has(url.origin) ||
      isLocalDevelopmentUrl
    );
  } catch {
    return false;
  }
}

export function resolveReturnUrl({
  requestedUrl,
  fallbackUrl,
  portalOrigin,
}: {
  requestedUrl?: string;
  fallbackUrl?: string;
  portalOrigin: string;
}) {
  if (requestedUrl && isAllowedReturnUrl(requestedUrl, portalOrigin)) {
    return requestedUrl;
  }
  if (fallbackUrl && isAllowedReturnUrl(fallbackUrl, portalOrigin)) {
    return fallbackUrl;
  }
  return portalOrigin;
}

export function resolveOrganizationLogoUrl(value?: string) {
  if (!value) return "";
  try {
    const url = new URL(value);
    return url.protocol === "https:" ||
      (process.env.NODE_ENV !== "production" &&
        url.protocol === "http:" &&
        LOCAL_HOSTS.has(url.hostname))
      ? url.href
      : "";
  } catch {
    return "";
  }
}
