"use client";

import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";

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
        requestInterceptor={(request) => {
          request.headers["X-Request-Id"] ??= crypto.randomUUID();
          return request;
        }}
      />
    </div>
  );
}
