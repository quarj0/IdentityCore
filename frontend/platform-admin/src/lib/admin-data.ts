export const adminNav = [
  { label: "Overview", href: "/overview" },
  { label: "Onboarding", href: "/onboarding" },
  { label: "Tenants", href: "/tenants" },
  { label: "Abuse signals", href: "/abuse-signals" },
  { label: "Providers", href: "/providers" },
  { label: "Activity", href: "/activity" },
  { label: "Audit logs", href: "/audit-logs" },
  { label: "Settings", href: "/settings" },
];

export const tenants = [
  { id: "org-1", name: "Acme Corporation", tier: "Growth", status: "Active", verifications: 1420, region: "West Africa" },
  { id: "org-2", name: "CyberDyne Systems", tier: "Enterprise", status: "Pending approval", verifications: 0, region: "Europe" },
  { id: "org-3", name: "Globex Corporation", tier: "Developer", status: "Active", verifications: 84, region: "North America" },
  { id: "org-4", name: "Initech", tier: "Growth", status: "Suspended", verifications: 410, region: "East Africa" },
];

export const providers = [
  { name: "Document analysis", status: "Operational", latency: "420ms", note: "Primary OCR and extraction lane healthy." },
  { name: "Face match", status: "Operational", latency: "188ms", note: "Confidence variance stable." },
  { name: "Liveness", status: "Degraded", latency: "1.2s", note: "Regional spike affecting West Africa mobile sessions." },
];

export const abuseSignals = [
  { id: "abuse-102", signal: "Repeated selfie mismatch", tenant: "Initech", severity: "High", state: "Open" },
  { id: "abuse-101", signal: "Burst verification creation", tenant: "Acme Corporation", severity: "Medium", state: "Monitoring" },
  { id: "abuse-099", signal: "Webhook retry storm", tenant: "Globex Corporation", severity: "Medium", state: "Open" },
];
