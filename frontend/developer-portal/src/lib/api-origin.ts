export type ApiOriginEnvironment = {
  NODE_ENV?: string;
  NEXT_PUBLIC_API_ORIGIN?: string;
  NEXT_PUBLIC_API_URL?: string;
};

export function configuredApiOrigin(
  environment: ApiOriginEnvironment = process.env,
) {
  const configuredApiUrl =
    environment.NEXT_PUBLIC_API_ORIGIN?.trim() ||
    environment.NEXT_PUBLIC_API_URL?.trim();

  if (!configuredApiUrl) {
    if (environment.NODE_ENV === "production") {
      throw new Error(
        "NEXT_PUBLIC_API_ORIGIN must be configured for the developer portal in production.",
      );
    }
    return undefined;
  }

  const parsedApiUrl = new URL(configuredApiUrl);
  if (
    environment.NODE_ENV === "production" &&
    parsedApiUrl.protocol !== "https:"
  ) {
    throw new Error(
      "The developer portal API URL must use HTTPS in production.",
    );
  }

  return parsedApiUrl.origin;
}
