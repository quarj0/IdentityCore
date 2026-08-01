export const DASHBOARD_SESSION_SCOPE = "dashboard";

export function addDashboardSessionScope(headers: Headers) {
  headers.set("X-IdentityCore-Session-Scope", DASHBOARD_SESSION_SCOPE);
  return headers;
}
