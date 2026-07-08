const PUBLIC_EMAIL_DOMAINS = new Set([
  "gmail.com",
  "googlemail.com",
  "outlook.com",
  "hotmail.com",
  "live.com",
  "msn.com",
  "yahoo.com",
  "ymail.com",
  "rocketmail.com",
  "icloud.com",
  "me.com",
  "aol.com",
  "proton.me",
  "protonmail.com",
  "pm.me",
  "zoho.com",
  "gmx.com",
  "mail.com",
  "yandex.com",
]);

const DISPOSABLE_EMAIL_DOMAINS = new Set([
  "mailinator.com",
  "guerrillamail.com",
  "guerrillamailblock.com",
  "sharklasers.com",
  "temp-mail.org",
  "tempmail.com",
  "tempmailo.com",
  "10minutemail.com",
  "10minutemail.net",
  "yopmail.com",
  "dispostable.com",
  "throwawaymail.com",
  "trashmail.com",
  "maildrop.cc",
  "getnada.com",
  "fakeinbox.com",
  "mintemail.com",
]);

const BUSINESS_EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const LETTER_RE = /[A-Za-z]/;
const DIGIT_RE = /\d/;
const SPECIAL_RE = /[^A-Za-z0-9]/;

export const PASSWORD_REQUIREMENTS_MESSAGE =
  "Use at least 8 characters with letters, numbers, and a special character.";

export function getPasswordValidationMessage(password: string) {
  if (!password) {
    return "";
  }
  if (password.length < 8) {
    return PASSWORD_REQUIREMENTS_MESSAGE;
  }
  if (!LETTER_RE.test(password) || !DIGIT_RE.test(password) || !SPECIAL_RE.test(password)) {
    return PASSWORD_REQUIREMENTS_MESSAGE;
  }
  return "";
}

export function getBusinessEmailValidationMessage(email: string) {
  const normalized = email.trim().toLowerCase();
  if (!normalized) {
    return "";
  }
  if (!BUSINESS_EMAIL_RE.test(normalized)) {
    return "Enter a valid work email address.";
  }

  const domain = normalized.split("@")[1] ?? "";
  if (
    domain === "localhost" ||
    domain === "example.com" ||
    domain === "example.org" ||
    domain === "example.net" ||
    domain.endsWith(".local") ||
    domain.endsWith(".invalid") ||
    domain.endsWith(".test")
  ) {
    return "Enter a valid business email domain.";
  }
  if (DISPOSABLE_EMAIL_DOMAINS.has(domain)) {
    return "Disposable email addresses are not allowed.";
  }
  if (PUBLIC_EMAIL_DOMAINS.has(domain)) {
    return "Use your organization email address instead.";
  }

  return "";
}
