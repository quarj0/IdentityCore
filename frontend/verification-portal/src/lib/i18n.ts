export const supportedLocales = ["en", "ar"] as const;
export type SupportedLocale = (typeof supportedLocales)[number];

const messages = {
  en: {
    skip: "Skip to content",
    consentTitle: "Review and give consent",
    consentDescription: "Understand what will be processed before you continue. You remain in control of whether to proceed.",
    accept: "Accept and continue",
    livenessTitle: "Complete a live camera check",
    activeDescription: "Follow a short, server-issued movement sequence while your camera records.",
    passiveDescription: "Submit your live selfie for a passive presence check. No movement challenge is required.",
    passiveSubmit: "Submit presence check",
  },
  ar: {
    skip: "تخطَّ إلى المحتوى",
    consentTitle: "راجع الموافقة وقدّمها",
    consentDescription: "افهم كيفية معالجة بياناتك قبل المتابعة. يمكنك اختيار عدم المتابعة.",
    accept: "الموافقة والمتابعة",
    livenessTitle: "أكمل فحص الكاميرا المباشر",
    activeDescription: "اتبع تسلسل الحركة القصير الصادر عن الخادم أثناء تسجيل الكاميرا.",
    passiveDescription: "أرسل صورتك الذاتية المباشرة لفحص الحضور السلبي. لا يلزم تحدي حركة.",
    passiveSubmit: "إرسال فحص الحضور",
  },
} as const;

export type MessageKey = keyof typeof messages.en;

export function resolveLocale(value: string | null | undefined): SupportedLocale {
  const language = value?.split(",", 1)[0]?.trim().split("-", 1)[0]?.toLowerCase();
  return supportedLocales.includes(language as SupportedLocale)
    ? (language as SupportedLocale)
    : "en";
}

export function direction(locale: SupportedLocale) {
  return locale === "ar" ? "rtl" : "ltr";
}

export function translate(locale: string, key: MessageKey) {
  return messages[resolveLocale(locale)][key];
}
