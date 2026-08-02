declare module "swagger-ui-react" {
  import type { ComponentType } from "react";

  type SwaggerRequest = {
    headers: Record<string, string>;
  };

  type SwaggerUIProps = {
    url?: string;
    deepLinking?: boolean;
    displayRequestDuration?: boolean;
    docExpansion?: "list" | "full" | "none";
    filter?: boolean;
    persistAuthorization?: boolean;
    tryItOutEnabled?: boolean;
    defaultModelsExpandDepth?: number;
    requestInterceptor?: (request: SwaggerRequest) => SwaggerRequest;
  };

  const SwaggerUI: ComponentType<SwaggerUIProps>;
  export default SwaggerUI;
}
