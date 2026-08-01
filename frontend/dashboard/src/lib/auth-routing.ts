export function getSafeReturnTo(value: string | null) {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return null;
  if (value === "/login" || value.startsWith("/login?")) return null;
  return value;
}
