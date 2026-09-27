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
  // Additional applicant journey, accessibility, and recovery copy.
  "Step 1 of 5": "الخطوة 1 من 5",
  "Step 2 of 5": "الخطوة 2 من 5",
  "Step 3 of 5": "الخطوة 3 من 5",
  "Step 4 of 5": "الخطوة 4 من 5",
  "Step 5 of 5": "الخطوة 5 من 5",
  "Capture your": "التقط",
  "Capture your National ID": "التقط بطاقة هويتك الوطنية",
  "Choose the identity document you want to use, then capture the original physical document with all four edges visible.": "اختر وثيقة الهوية التي تريد استخدامها، ثم التقط صورة للوثيقة الأصلية مع ظهور حوافها الأربع.",
  "Choose the identity document you want to use, then capture its photo page with all four edges visible.": "اختر وثيقة الهوية التي تريد استخدامها، ثم التقط صفحة الصورة مع ظهور حوافها الأربع.",
  "Checking your": "جارٍ التحقق من",
  "IdentityCore is checking capture quality and reading the supported document evidence.": "يتحقق IdentityCore من جودة الصورة ويقرأ بيانات الوثيقة المدعومة.",
  "Document received": "تم استلام الوثيقة",
  "Your document was uploaded successfully and is now being checked. Keep this page open while processing completes.": "تم رفع وثيقتك بنجاح ويجري التحقق منها الآن. اترك هذه الصفحة مفتوحة حتى يكتمل الفحص.",
  "Uploading and submitting your document…": "جارٍ رفع وثيقتك وإرسالها…",
  "Uploading document securely…": "جارٍ إرسال الوثيقة بأمان…",
  "Document received successfully": "تم استلام الوثيقة بنجاح",
  "Your selfie was uploaded successfully. Continue to the presence check.": "تم رفع صورتك الذاتية بنجاح. تابع إلى فحص الحضور.",
  "Selfie received": "تم استلام الصورة الذاتية",
  "Uploading and submitting your selfie…": "جارٍ رفع صورتك الذاتية وإرسالها…",
  "Your live selfie will be compared with the document portrait.": "ستُقارن صورتك الذاتية المباشرة بصورة الوثيقة.",
  "IdentityCore Verify": "التحقق عبر IdentityCore",
  "Secure identity verification": "تحقق آمن من الهوية",
  "Consent": "الموافقة",
  "Review how your data is used": "راجع كيفية استخدام بياناتك",
  "Capture a clear document image": "التقط صورة واضحة للوثيقة",
  "Confirm the document belongs to you": "أكد أن الوثيقة تخصك",
  "Presence check": "فحص الحضور",
  "Complete passive liveness": "أكمل فحص الحضور السلبي",
  "Decision": "القرار",
  "Secure evidence evaluation": "تقييم الأدلة بأمان",
  "Verification progress": "تقدم التحقق",
  ", current step": "، الخطوة الحالية",
  ", completed": "، مكتملة",
  "Your browser blocks live camera access on this HTTP address. Upload an image below, or use HTTPS or localhost for camera capture.": "يحظر متصفحك الوصول المباشر إلى الكاميرا عبر عنوان HTTP هذا. ارفع صورة أدناه أو استخدم HTTPS أو localhost.",
  "The camera is no longer available. Enable it and try again.": "لم تعد الكاميرا متاحة. فعّلها وحاول مرة أخرى.",
  "Camera permission is blocked. Enable it in your browser settings or upload an image.": "تم حظر إذن الكاميرا. فعّله من إعدادات المتصفح أو ارفع صورة.",
  "We could not start a usable camera. Upload a clear image to continue.": "تعذر تشغيل الكاميرا. ارفع صورة واضحة للمتابعة.",
  "The camera is still preparing. Wait a moment and try again.": "لا تزال الكاميرا قيد التجهيز. انتظر قليلًا ثم حاول مرة أخرى.",
  "Your browser could not capture this image. Upload one instead.": "تعذر على متصفحك التقاط الصورة. ارفع صورة بدلًا من ذلك.",
  "The image could not be created. Please try again.": "تعذر إنشاء الصورة. حاول مرة أخرى.",
  "HTTP testing mode:": "وضع اختبار HTTP:",
  "Live camera access is disabled by the browser on this address. File upload still works. Choose Upload image below, or open the portal through HTTPS or localhost.": "عطّل المتصفح الوصول إلى الكاميرا عبر هذا العنوان. لا يزال رفع الملفات متاحًا. اختر رفع صورة أدناه أو افتح البوابة عبر HTTPS أو localhost.",
  "The live check was interrupted when this page became inactive. Start it again.": "توقف الفحص المباشر عندما أصبحت الصفحة غير نشطة. ابدأه مرة أخرى.",
  "Live liveness requires a secure HTTPS connection and camera access.": "يتطلب فحص الحضور المباشر اتصال HTTPS آمنًا وإمكانية الوصول إلى الكاميرا.",
  "This browser cannot record a live liveness video. Use a current browser on your phone.": "لا يستطيع هذا المتصفح تسجيل فيديو للتحقق المباشر. استخدم متصفحًا حديثًا على هاتفك.",
  "The camera disconnected during the live check. Start it again.": "انقطع اتصال الكاميرا أثناء الفحص المباشر. ابدأه مرة أخرى.",
  "Camera access is required for this live check. Allow camera access and try again.": "يلزم الوصول إلى الكاميرا لإجراء هذا الفحص. اسمح بالوصول وحاول مرة أخرى.",
  "This browser cannot create a supported MP4 or WebM liveness video. Update your browser or use another current device.": "لا يستطيع هذا المتصفح إنشاء فيديو MP4 أو WebM مدعوم للتحقق المباشر. حدّث المتصفح أو استخدم جهازًا حديثًا آخر.",
  "No video was recorded. Please try again.": "لم يتم تسجيل فيديو. حاول مرة أخرى.",
  "The live video is too large to upload. Move closer to a stable connection and try again.": "حجم الفيديو المباشر كبير جدًا للرفع. انتقل إلى اتصال أكثر استقرارًا وحاول مرة أخرى.",
  "Live camera check": "فحص الكاميرا المباشر",
  "A short video is recorded only after you start the challenge.": "لن يتم تسجيل مقطع قصير إلا بعد بدء التحدي.",
  "Hold still while we finish recording": "ابقَ ثابتًا حتى يكتمل التسجيل.",
  "Continue securely on your phone": "تابع بأمان على هاتفك",
  "requested this verification. A phone camera usually gives clearer document and selfie captures.": "طلبت هذه المؤسسة إجراء التحقق. توفر كاميرا الهاتف عادةً صورًا أوضح للوثائق والصور الذاتية.",
  "Scan with your phone camera": "امسح الرمز بكاميرا هاتفك",
  "The one-time code expires shortly and cannot be reused.": "تنتهي صلاحية الرمز لمرة واحدة قريبًا ولا يمكن استخدامه مجددًا.",
  "Copy mobile link": "نسخ رابط الهاتف",
  "Waiting for completion on your phone": "بانتظار إكمال العملية على هاتفك",
  "Show secure QR code": "عرض رمز QR الآمن",
  "or": "أو",
  "Continue on this computer": "المتابعة على هذا الكمبيوتر",
  "Verification unavailable": "التحقق غير متاح",
  "Review and give consent": "راجع الموافقة وقدّمها",
  "Understand what will be processed before you continue. You remain in control of whether to proceed.": "تعرّف على البيانات التي ستُعالج قبل المتابعة. يظل قرار المتابعة بيدك.",
  "Checking your": "جارٍ التحقق من",
  "Step 1 of 5": "الخطوة 1 من 5",
  "Step 2 of 5": "الخطوة 2 من 5",
  "Step 3 of 5": "الخطوة 3 من 5",
  "Step 4 of 5": "الخطوة 4 من 5",
  "Step 5 of 5": "الخطوة 5 من 5",
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
