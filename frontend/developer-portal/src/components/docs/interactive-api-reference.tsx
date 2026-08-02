"use client";

import dynamic from "next/dynamic";
import "swagger-ui-react/swagger-ui.css";

const SwaggerUI = dynamic(() => import("swagger-ui-react"), {
  ssr: false,
  loading: () => (
    <div className="flex min-h-96 items-center justify-center p-8 text-sm text-slate-600">
      Loading the interactive API reference…
    </div>
  ),
});

export function InteractiveApiReference() {
  return (
    <div className="api-explorer overflow-hidden rounded-3xl border border-slate-200 bg-white">
      <SwaggerUI
        url="/api/openapi"
        deepLinking
        displayRequestDuration
        docExpansion="list"
        filter
        persistAuthorization
        tryItOutEnabled
        defaultModelsExpandDepth={1}
        requestInterceptor={(request: { headers: { [x: string]: string; }; }) => {
          request.headers["X-Request-Id"] ??= crypto.randomUUID();
          return request;
        }}
      />
    </div>
  );
}
