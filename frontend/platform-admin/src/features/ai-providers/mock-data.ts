export type AiProviderType = "face" | "ocr" | "liveness";
export type AiProviderStatus = "operational" | "degraded" | "disabled" | "testing";

export type AiProvider = {
  id: string;
  name: string;
  type: AiProviderType;
  status: AiProviderStatus;
  model: string;
  region: string;
  priority: number;
  failoverEnabled: boolean;
  latencyMs: number;
  p95LatencyMs: number;
  successRate: string;
  errorRate: string;
  costPerCheck: string;
  monthlyCost: string;
  checksToday: number;
  checksThisMonth: number;
  lastHealthCheckAt: string;
  ownerTeam: string;
};

export const aiProviders: AiProvider[] = [
  {
    id: "ai_insightface_primary",
    name: "InsightFace Primary",
    type: "face",
    status: "operational",
    model: "buffalo_l",
    region: "Africa West",
    priority: 1,
    failoverEnabled: true,
    latencyMs: 184,
    p95LatencyMs: 241,
    successRate: "99.1%",
    errorRate: "0.9%",
    costPerCheck: "$0.003",
    monthlyCost: "$4,280",
    checksToday: 18420,
    checksThisMonth: 482100,
    lastHealthCheckAt: "2026-07-09 09:41",
    ownerTeam: "AI Platform",
  },
  {
    id: "ai_paddleocr_primary",
    name: "PaddleOCR Primary",
    type: "ocr",
    status: "degraded",
    model: "PP-OCRv5",
    region: "Africa West",
    priority: 1,
    failoverEnabled: true,
    latencyMs: 418,
    p95LatencyMs: 612,
    successRate: "94.8%",
    errorRate: "5.2%",
    costPerCheck: "$0.002",
    monthlyCost: "$3,140",
    checksToday: 22190,
    checksThisMonth: 621300,
    lastHealthCheckAt: "2026-07-09 09:39",
    ownerTeam: "AI Platform",
  },
  {
    id: "ai_liveness_primary",
    name: "Liveness Engine",
    type: "liveness",
    status: "operational",
    model: "MediaPipe + motion signals",
    region: "Africa West",
    priority: 1,
    failoverEnabled: true,
    latencyMs: 233,
    p95LatencyMs: 318,
    successRate: "97.9%",
    errorRate: "2.1%",
    costPerCheck: "$0.004",
    monthlyCost: "$5,920",
    checksToday: 16310,
    checksThisMonth: 391200,
    lastHealthCheckAt: "2026-07-09 09:40",
    ownerTeam: "AI Platform",
  },
  {
    id: "ai_google_vision_backup",
    name: "Google Vision Backup",
    type: "ocr",
    status: "testing",
    model: "Vision OCR",
    region: "Europe West",
    priority: 2,
    failoverEnabled: false,
    latencyMs: 302,
    p95LatencyMs: 498,
    successRate: "96.2%",
    errorRate: "3.8%",
    costPerCheck: "$0.009",
    monthlyCost: "$840",
    checksToday: 1200,
    checksThisMonth: 28000,
    lastHealthCheckAt: "2026-07-09 09:22",
    ownerTeam: "Integrations",
  },
  {
    id: "ai_custom_face_backup",
    name: "Custom Face Backup",
    type: "face",
    status: "disabled",
    model: "IdentityCore FaceNet",
    region: "US East",
    priority: 3,
    failoverEnabled: false,
    latencyMs: 0,
    p95LatencyMs: 0,
    successRate: "N/A",
    errorRate: "N/A",
    costPerCheck: "$0.001",
    monthlyCost: "$0",
    checksToday: 0,
    checksThisMonth: 0,
    lastHealthCheckAt: "Disabled",
    ownerTeam: "Research",
  },
];

export const aiProviderHealthEvents = [
  {
    title: "Latency threshold exceeded",
    provider: "PaddleOCR Primary",
    severity: "Warning",
    time: "14 minutes ago",
  },
  {
    title: "Failover simulation completed",
    provider: "InsightFace Primary",
    severity: "Success",
    time: "1 hour ago",
  },
  {
    title: "Cost budget check completed",
    provider: "Liveness Engine",
    severity: "Info",
    time: "3 hours ago",
  },
];

export const aiProviderRoutingRules = [
  {
    condition: "Primary OCR latency above 600ms",
    action: "Route 30% of OCR traffic to backup provider",
  },
  {
    condition: "Face match confidence below threshold",
    action: "Queue for manual review with AI evidence",
  },
  {
    condition: "Liveness provider unavailable",
    action: "Pause verification step and retry for 90 seconds",
  },
];

export function getAiProviderById(providerId: string) {
  return aiProviders.find((provider) => provider.id === providerId);
}