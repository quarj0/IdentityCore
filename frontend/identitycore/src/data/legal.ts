export const legalPages = {
  privacy: {
    title: "Privacy Policy",
    description:
      "How IdentityCore approaches personal data, identity evidence, consent, storage, and privacy-first infrastructure.",
    updatedAt: "July 2026",
    sections: [
      {
        title: "Overview",
        body: [
          "IdentityCore is designed as digital identity infrastructure for organizations that need secure, privacy-conscious identity workflows.",
          "This Privacy Policy explains how personal data may be collected, processed, stored, and protected when organizations use IdentityCore.",
        ],
      },
      {
        title: "Data we may process",
        body: [
          "Depending on the workflow, IdentityCore may process identity documents, selfies, liveness media, contact details, organization information, verification metadata, audit events, and technical logs.",
          "IdentityCore should collect only the data required for the specific workflow being performed.",
        ],
      },
      {
        title: "Identity evidence",
        body: [
          "Identity documents, biometric media, verification reports, and audit evidence are treated as sensitive by default.",
          "Access to sensitive identity evidence should be controlled through authentication, tenant isolation, role-based permissions, and signed media access.",
        ],
      },
      {
        title: "Consent",
        body: [
          "Verification subjects should be shown clear information about why their identity is being verified and how their data will be used.",
          "Consent records may be stored as part of the verification audit trail.",
        ],
      },
      {
        title: "Retention",
        body: [
          "Organizations should configure retention policies based on their legal, regulatory, and operational requirements.",
          "Temporary uploads should be deleted automatically after a short period where possible.",
        ],
      },
      {
        title: "Security",
        body: [
          "IdentityCore is designed around encryption, private storage, signed URLs, tenant isolation, audit logs, and least-privilege access.",
          "No platform can guarantee absolute security, but IdentityCore should follow privacy-by-design and security-first principles.",
        ],
      },
    ],
  },

  terms: {
    title: "Terms of Service",
    description:
      "The terms governing access to IdentityCore workspaces, sandbox usage, production approval, and acceptable use.",
    updatedAt: "July 2026",
    sections: [
      {
        title: "Overview",
        body: [
          "These Terms describe the conditions under which organizations may access and use IdentityCore.",
          "IdentityCore is intended for legitimate identity, trust, onboarding, verification, access, and governance workflows.",
        ],
      },
      {
        title: "Organization accounts",
        body: [
          "IdentityCore is organization-first. Users register themselves and their organization together.",
          "Organizations may be required to complete email verification, organization verification, administrator identity verification, and platform review before production access is granted.",
        ],
      },
      {
        title: "Sandbox and production access",
        body: [
          "New organizations may start in sandbox mode with limited functionality.",
          "Production access may require approval by IdentityCore administrators to reduce abuse and protect verification subjects.",
        ],
      },
      {
        title: "Acceptable use",
        body: [
          "Organizations must not use IdentityCore to impersonate another organization, collect identity data without lawful basis, mislead verification subjects, or perform unlawful surveillance.",
          "IdentityCore may suspend access where abuse, fraud, or policy violations are suspected.",
        ],
      },
      {
        title: "Customer responsibility",
        body: [
          "Organizations are responsible for configuring workflows, policies, retention rules, provider choices, and legal notices appropriate for their use case.",
          "IdentityCore provides infrastructure, but customers remain responsible for lawful and ethical use.",
        ],
      },
      {
        title: "Changes",
        body: [
          "These Terms may be updated as IdentityCore evolves. Material changes should be communicated where appropriate.",
        ],
      },
    ],
  },

  cookies: {
    title: "Cookie Policy",
    description:
      "How IdentityCore may use cookies and similar technologies across public pages, dashboards, and developer tools.",
    updatedAt: "July 2026",
    sections: [
      {
        title: "Overview",
        body: [
          "IdentityCore may use cookies and similar technologies to provide secure sessions, remember preferences, improve reliability, and understand product usage.",
        ],
      },
      {
        title: "Essential cookies",
        body: [
          "Essential cookies are required for authentication, security, session management, fraud prevention, and basic platform functionality.",
          "These cookies cannot be disabled without affecting core platform behavior.",
        ],
      },
      {
        title: "Preference cookies",
        body: [
          "Preference cookies may be used to remember interface settings such as theme, language, or workspace preferences.",
        ],
      },
      {
        title: "Analytics cookies",
        body: [
          "Analytics cookies may be used in the future to understand public website usage and improve product experience.",
          "IdentityCore should avoid using analytics in ways that expose sensitive identity data.",
        ],
      },
      {
        title: "Managing cookies",
        body: [
          "Users can control cookies through their browser settings.",
          "Disabling some cookies may affect authentication or workspace functionality.",
        ],
      },
    ],
  },
};
