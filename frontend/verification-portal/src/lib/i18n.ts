export const supportedLocales = ["en", "ar"] as const;
export type SupportedLocale = (typeof supportedLocales)[number];

const messages = {
  en: {
    skip: "Skip to content",
    languageLabel: "Language",
    english: "English",
    arabic: "Arabic",
    consentTitle: "Review and give consent",
    consentDescription:
      "Understand what will be processed before you continue. You remain in control of whether to proceed.",
    accept: "Accept and continue",
    livenessTitle: "Complete a live camera check",
    activeDescription:
      "Follow a short, server-issued movement sequence while your camera records.",
    passiveDescription:
      "Submit your live selfie for a passive presence check. No movement challenge is required.",
    passiveSubmit: "Submit presence check",
  },
  ar: {
    skip: "تخطَّ إلى المحتوى",
    languageLabel: "اللغة",
    english: "الإنجليزية",
    arabic: "العربية",
    consentTitle: "راجع الموافقة وقدّمها",
    consentDescription:
      "افهم كيفية معالجة بياناتك قبل المتابعة. يمكنك اختيار عدم المتابعة.",
    accept: "الموافقة والمتابعة",
    livenessTitle: "أكمل فحص الكاميرا المباشر",
    activeDescription:
      "اتبع تسلسل الحركة القصير الصادر عن الخادم أثناء تسجيل الكاميرا.",
    passiveDescription:
      "أرسل صورتك الذاتية المباشرة لفحص الحضور السلبي. لا يلزم تحدي حركة.",
    passiveSubmit: "إرسال فحص الحضور",
  },
} as const;

export type MessageKey = keyof typeof messages.en;

export function resolveLocale(
  value: string | null | undefined,
): SupportedLocale {
  const candidates = (value ?? "")
    .split(",")
    .map((part, index) => {
      const [tag, ...parameters] = part.trim().split(";");
      const qualityParameter = parameters.find((parameter) =>
        parameter.trim().startsWith("q="),
      );
      const quality = qualityParameter
        ? Number(qualityParameter.trim().slice(2))
        : 1;
      return { tag: tag.trim().toLowerCase(), quality, index };
    })
    .filter((candidate) => candidate.tag && candidate.quality > 0)
    .sort((left, right) => right.quality - left.quality || left.index - right.index);

  for (const candidate of candidates) {
    const language = candidate.tag.split("-", 1)[0];
    const match = supportedLocales.find(
      (locale) => locale === candidate.tag || locale === language,
    );
    if (match) return match;
  }
  return "en";
}

export function direction(locale: SupportedLocale) {
  return locale === "ar" ? "rtl" : "ltr";
}

export function translate(locale: string, key: MessageKey) {
  return messages[resolveLocale(locale)][key];
}

export function formatNumber(
  locale: string,
  value: number,
  options?: Intl.NumberFormatOptions,
) {
  return new Intl.NumberFormat(resolveLocale(locale), options).format(value);
}

export function formatDate(
  locale: string,
  value: Date | number | string,
  options: Intl.DateTimeFormatOptions = { dateStyle: "medium" },
) {
  return new Intl.DateTimeFormat(resolveLocale(locale), options).format(
    value instanceof Date || typeof value === "number" ? value : new Date(value),
  );
}
