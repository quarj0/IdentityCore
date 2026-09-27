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

const arabicCopy: Record<string, string> = {
  "Opening your secure session": "جارٍ فتح جلستك الآمنة",
  "Verification unavailable": "التحقق غير متاح",
  "Validating your one-time session credential…": "جارٍ التحقق من بيانات اعتماد جلستك لمرة واحدة…",
  "We could not continue": "تعذرت المتابعة",
  "Consent is recorded in the audit trail": "تُسجَّل الموافقة في سجل التدقيق",
  "Identity document": "وثيقة الهوية",
  "Used to read and validate identity details": "تُستخدم لقراءة بيانات الهوية والتحقق منها",
  "Live selfie": "صورة ذاتية مباشرة",
  "Compared with the portrait on your document": "تُقارن بالصورة الموجودة في وثيقتك",
  "Security signals": "إشارات الأمان",
  "Used for liveness, fraud risk, and audit": "تُستخدم للتحقق من الحضور ومخاطر الاحتيال والتدقيق",
  "Issuing country": "بلد الإصدار",
  "Document type": "نوع الوثيقة",
  "Captured — select to review": "تم الالتقاط — اختر للمراجعة",
  "Not captured": "لم يتم الالتقاط",
  "Capture": "التقاط",
  "Retake": "إعادة الالتقاط",
  "Submit document": "إرسال الوثيقة",
  "Uploading document…": "جارٍ رفع الوثيقة…",
  "Secure document check": "فحص آمن للوثيقة",
  "Document processing in progress": "جارٍ التحقق من الوثيقة",
  "Capture quality": "جودة الالتقاط",
  "OCR evidence": "بيانات التعرّف الضوئي",
  "Review signals": "إشارات المراجعة",
  "Take a live selfie": "التقط صورة ذاتية مباشرة",
  "Remove hats or dark glasses, face the camera directly, and use even lighting. Your selfie will be compared with the document portrait.": "انزع القبعات والنظارات الداكنة، وواجه الكاميرا مباشرة مع إضاءة متوازنة. ستُقارن صورتك بصورة الوثيقة.",
  "Submit selfie": "إرسال الصورة الذاتية",
  "Uploading selfie…": "جارٍ رفع الصورة الذاتية…",
  "Prove you are present, live": "أثبت حضورك المباشر",
  "Your challenge is single-use, randomized, and recorded directly from this device in one short video.": "التحدي للاستخدام مرة واحدة، عشوائي، ويُسجَّل مباشرة من هذا الجهاز في مقطع قصير.",
  "Presence check submitted": "تم إرسال فحص الحضور",
  "Your live selfie is being checked.": "جارٍ التحقق من صورتك الذاتية المباشرة.",
  "Checking your live selfie…": "جارٍ فحص صورتك الذاتية المباشرة…",
  "Live challenge ready": "أصبح التحدي المباشر جاهزًا",
  "Enable your camera and follow the on-screen instructions.": "فعّل الكاميرا واتبع التعليمات الظاهرة على الشاشة.",
  "Live recording ready to submit.": "التسجيل المباشر جاهز للإرسال.",
  "Record again": "التسجيل مرة أخرى",
  "Submit live check": "إرسال الفحص المباشر",
  "Your live video is being checked.": "جارٍ التحقق من مقطعك المباشر.",
  "Uploading and checking your live video…": "جارٍ رفع مقطعك المباشر والتحقق منه…",
  "Completing your verification": "جارٍ إكمال التحقق",
  "Secure decision processing": "جارٍ معالجة القرار بأمان",
  "Liveness result": "نتيجة التحقق من الحضور",
  "Face comparison": "مقارنة الوجه",
  "Risk rules": "قواعد المخاطر",
  "Final decision": "القرار النهائي",
  "Finish and return": "إنهاء والعودة",
  "Camera preview": "معاينة الكاميرا",
  "Allow camera access when prompted. Nothing is submitted until you review the image.": "اسمح بالوصول إلى الكاميرا عند الطلب. لن يتم إرسال شيء قبل مراجعة الصورة.",
  "Align the full document inside the frame": "ضع الوثيقة كاملة داخل الإطار",
  "Check focus and lighting before capture": "تحقق من التركيز والإضاءة قبل الالتقاط",
  "Starting camera…": "جارٍ تشغيل الكاميرا…",
  "Use camera": "استخدام الكاميرا",
  "Capture image": "التقاط الصورة",
  "Upload image": "رفع صورة",
  "Enable camera": "تفعيل الكاميرا",
  "Start live challenge": "بدء التحدي المباشر",
  "Finish recording": "إنهاء التسجيل",
  "Restart": "إعادة التشغيل",
  "Keep this page open. This usually takes less than a minute.": "اترك هذه الصفحة مفتوحة. يستغرق ذلك عادةً أقل من دقيقة.",
  "This image cannot be previewed. Retake or choose another file.": "تعذرت معاينة هذه الصورة. أعد التقاطها أو اختر ملفًا آخر.",
  "Captured evidence preview": "معاينة الدليل الملتقط",
  "Verification complete": "اكتمل التحقق",
  "Your identity evidence was verified successfully.": "تم التحقق من دليل هويتك بنجاح.",
  "Submitted for review": "تم الإرسال للمراجعة",
  "Your evidence was received securely. The requesting organization will review it.": "تم استلام دليلك بأمان. ستراجعه المؤسسة الطالبة.",
  "Verification needs attention": "يتطلب التحقق الانتباه",
  "We could not complete this verification with the submitted evidence.": "تعذر إكمال التحقق باستخدام الأدلة المرسلة.",
  "This session has expired": "انتهت صلاحية هذه الجلسة",
  "For your security, verification links are available only for a limited time.": "حفاظًا على أمانك، تتاح روابط التحقق لفترة محدودة فقط.",
  "Verification cancelled": "تم إلغاء التحقق",
  "The requesting organization cancelled this verification session.": "ألغت المؤسسة الطالبة جلسة التحقق هذه.",
  "Your data stays protected": "بياناتك محمية",
  "Evidence is encrypted, access is audited, and it is used only for this verification.": "الأدلة مشفرة، ويُدقَّق في الوصول إليها، ولا تُستخدم إلا لهذا التحقق.",
  "Verification requested by": "طلب التحقق",
  "Encrypted session": "جلسة مشفرة",
  "Reference": "المرجع",
};

export function localizeText(locale: string, text: string): string {
  return resolveLocale(locale) === "ar" ? arabicCopy[text] ?? text : text;
}


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
