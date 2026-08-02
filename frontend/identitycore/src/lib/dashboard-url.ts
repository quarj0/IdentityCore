const dashboardOrigin = (
  process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3000"
).replace(/\/$/, "");

export function dashboardUrl(path = "/") {
  return `${dashboardOrigin}${path.startsWith("/") ? path : `/${path}`}`;
}
