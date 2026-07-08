function trimTrailingSlash(value: string) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

const marketingSiteUrl = trimTrailingSlash(
  process.env.NEXT_PUBLIC_MARKETING_URL || "https://identitycore.dev",
);

export const siteConfig = {
  marketingSiteUrl,
  createWorkspaceUrl: `${marketingSiteUrl}/register`,
};
