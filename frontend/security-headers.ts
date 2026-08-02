export type CspOptions = {
  apiOrigin?: string;
  camera?: boolean;
  development?: boolean;
};

function sourceOrigin(value?: string) {
  if (!value) return undefined;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:"
      ? url.origin
      : undefined;
  } catch {
    return undefined;
  }
}

export function contentSecurityPolicy(nonce: string, options: CspOptions = {}) {
  const apiOrigin = sourceOrigin(options.apiOrigin);
  const connectSources = [
    "'self'",
    ...(apiOrigin ? [apiOrigin] : []),
    ...(options.development ? ["ws:", "wss:"] : []),
  ];

  return [
    "default-src 'self'",
    "base-uri 'self'",
    `connect-src ${connectSources.join(" ")}`,
    "font-src 'self' data:",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "img-src 'self' data: blob:",
    "media-src 'self' blob:",
    "object-src 'none'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${options.development ? " 'unsafe-eval'" : ""}`,
    `style-src 'self' 'nonce-${nonce}'`,
    "style-src-attr 'none'",
    "worker-src 'self' blob:",
    "report-uri /api/security/csp-report",
  ].join("; ");
}

export function securityHeaders(nonce: string, options: CspOptions = {}) {
  return {
    "Content-Security-Policy": contentSecurityPolicy(nonce, options),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": options.camera
      ? "camera=(self), microphone=(), geolocation=(), payment=()"
      : "camera=(), microphone=(), geolocation=(), payment=()",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-DNS-Prefetch-Control": "off",
    "X-Frame-Options": "DENY",
  } as const;
}
