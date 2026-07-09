export type VerificationProviderStatus =
  | "planned"
  | "sandbox"
  | "active"
  | "disabled"
  | "deprecated";

export type VerificationProvider = {
  id: string;
  name: string;
  status: VerificationProviderStatus;
  category: "Identity verification" | "KYB" | "Document intelligence" | "Biometrics";
  countries: string[];
  capabilities: string[];
  pricingModel: string;
  estimatedCost: string;
  integrationStage: string;
  apiReadiness: string;
  monthlyVolume: number;
  successRate: string;
  latencyMs: number;
  ownerTeam: string;
  lastReviewedAt: string;
};

export const verificationProviders: VerificationProvider[] = [
  {
    id: "vp_jumio",
    name: "Jumio",
    status: "planned",
    category: "Identity verification",
    countries: ["Global"],
    capabilities: ["Document verification", "Face match", "Liveness", "AML screening"],
    pricingModel: "Per verification",
    estimatedCost: "$1.00 - $2.00/check",
    integrationStage: "Research",
    apiReadiness: "Not connected",
    monthlyVolume: 0,
    successRate: "N/A",
    latencyMs: 0,
    ownerTeam: "Integrations",
    lastReviewedAt: "2026-07-02",
  },
  {
    id: "vp_persona",
    name: "Persona",
    status: "sandbox",
    category: "Identity verification",
    countries: ["US", "UK", "EU", "Global"],
    capabilities: ["Document verification", "Database checks", "Workflow builder"],
    pricingModel: "Contract",
    estimatedCost: "Custom",
    integrationStage: "Sandbox evaluation",
    apiReadiness: "Mock adapter",
    monthlyVolume: 420,
    successRate: "96.1%",
    latencyMs: 820,
    ownerTeam: "Integrations",
    lastReviewedAt: "2026-07-06",
  },
  {
    id: "vp_onfido",
    name: "Onfido",
    status: "planned",
    category: "Identity verification",
    countries: ["Global"],
    capabilities: ["Document verification", "Biometrics", "Fraud signals"],
    pricingModel: "Per check",
    estimatedCost: "$0.80 - $1.80/check",
    integrationStage: "Vendor comparison",
    apiReadiness: "Not connected",
    monthlyVolume: 0,
    successRate: "N/A",
    latencyMs: 0,
    ownerTeam: "Integrations",
    lastReviewedAt: "2026-06-30",
  },
  {
    id: "vp_metamap",
    name: "MetaMap",
    status: "planned",
    category: "Identity verification",
    countries: ["Africa", "LATAM", "Global"],
    capabilities: ["KYC", "KYB", "Document checks", "Risk workflows"],
    pricingModel: "Contract",
    estimatedCost: "Custom",
    integrationStage: "Market research",
    apiReadiness: "Not connected",
    monthlyVolume: 0,
    successRate: "N/A",
    latencyMs: 0,
    ownerTeam: "Strategy",
    lastReviewedAt: "2026-07-01",
  },
  {
    id: "vp_smile_identity",
    name: "Smile Identity",
    status: "sandbox",
    category: "Identity verification",
    countries: ["Ghana", "Nigeria", "Kenya", "South Africa"],
    capabilities: ["ID verification", "Biometrics", "AML", "Document verification"],
    pricingModel: "Per verification",
    estimatedCost: "$0.30 - $1.20/check",
    integrationStage: "Sandbox evaluation",
    apiReadiness: "Mock adapter",
    monthlyVolume: 1280,
    successRate: "95.4%",
    latencyMs: 640,
    ownerTeam: "Africa Integrations",
    lastReviewedAt: "2026-07-07",
  },
  {
    id: "vp_verifyme",
    name: "VerifyMe",
    status: "planned",
    category: "Identity verification",
    countries: ["Nigeria"],
    capabilities: ["NIN", "BVN", "Address checks", "Business checks"],
    pricingModel: "Per lookup",
    estimatedCost: "Variable",
    integrationStage: "Research",
    apiReadiness: "Not connected",
    monthlyVolume: 0,
    successRate: "N/A",
    latencyMs: 0,
    ownerTeam: "Africa Integrations",
    lastReviewedAt: "2026-06-28",
  },
  {
    id: "vp_id_analyzer",
    name: "ID Analyzer",
    status: "sandbox",
    category: "Document intelligence",
    countries: ["Global"],
    capabilities: ["Document OCR", "Document authentication", "Face match"],
    pricingModel: "Per scan",
    estimatedCost: "$0.10 - $0.60/check",
    integrationStage: "Sandbox evaluation",
    apiReadiness: "Mock adapter",
    monthlyVolume: 900,
    successRate: "94.9%",
    latencyMs: 710,
    ownerTeam: "Integrations",
    lastReviewedAt: "2026-07-05",
  },
];

export const providerContractNotes = [
  "Data processing agreement required before production use.",
  "Confirm supported countries and fallback behavior.",
  "Review retention, subprocessor and audit export capabilities.",
];

export const providerUsageHistory = [
  {
    month: "May",
    volume: "410",
    spend: "$284",
  },
  {
    month: "June",
    volume: "920",
    spend: "$681",
  },
  {
    month: "July",
    volume: "1,280",
    spend: "$874",
  },
];

export function getVerificationProviderById(providerId: string) {
  return verificationProviders.find((provider) => provider.id === providerId);
}