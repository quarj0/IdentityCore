export const dashboardMetrics = [
  {
    label: "Active organizations",
    value: "1,284",
    change: "+12.4%",
    trend: "up",
    helperText: "30 days",
  },
  {
    label: "Active verifications",
    value: "482,910",
    change: "+18.7%",
    trend: "up",
    helperText: "30 days",
  },
  {
    label: "API requests",
    value: "38.2M",
    change: "+9.1%",
    trend: "up",
    helperText: "30 days",
  },
  {
    label: "Approval rate",
    value: "91.8%",
    change: "-1.3%",
    trend: "down",
    helperText: "7 days",
  },
  {
    label: "AI success rate",
    value: "98.2%",
    change: "+0.6%",
    trend: "up",
    helperText: "24 hours",
  },
  {
    label: "Manual review queue",
    value: "1,742",
    change: "+244",
    trend: "down",
    helperText: "pending",
  },
  {
    label: "Monthly revenue",
    value: "$184.6K",
    change: "+16.2%",
    trend: "up",
    helperText: "MRR",
  },
  {
    label: "Open incidents",
    value: "2",
    change: "1 major",
    trend: "neutral",
    helperText: "live",
  },
] as const;

export const aiProviderHealth = [
  {
    name: "InsightFace Cluster",
    type: "Face matching",
    status: "Operational",
    latency: "214ms",
    successRate: "99.1%",
    cost: "$0.003/check",
    priority: 1,
  },
  {
    name: "PaddleOCR Pool",
    type: "OCR extraction",
    status: "Degraded",
    latency: "487ms",
    successRate: "94.8%",
    cost: "$0.002/check",
    priority: 1,
  },
  {
    name: "Liveness Engine",
    type: "Liveness",
    status: "Operational",
    latency: "331ms",
    successRate: "97.9%",
    cost: "$0.004/check",
    priority: 2,
  },
];

export const systemStatus = [
  {
    name: "API Gateway",
    status: "Operational",
    region: "Global",
  },
  {
    name: "Verification API",
    status: "Operational",
    region: "Africa West",
  },
  {
    name: "Evidence Storage",
    status: "Operational",
    region: "Multi-region",
  },
  {
    name: "Webhook Delivery",
    status: "Degraded",
    region: "Global",
  },
  {
    name: "Manual Review Console",
    status: "Operational",
    region: "Global",
  },
];

export const verificationActivity = [
  {
    country: "Ghana",
    total: "124,302",
    approved: "113,804",
    failed: "7,442",
    manualReview: "3,056",
  },
  {
    country: "Nigeria",
    total: "98,211",
    approved: "87,400",
    failed: "6,122",
    manualReview: "4,689",
  },
  {
    country: "Kenya",
    total: "46,905",
    approved: "42,810",
    failed: "2,611",
    manualReview: "1,484",
  },
  {
    country: "South Africa",
    total: "38,477",
    approved: "34,292",
    failed: "2,019",
    manualReview: "2,166",
  },
];

export const revenueSummary = {
  mrr: "$184.6K",
  usageRevenue: "$72.4K",
  platformFees: "$19.8K",
  overdueInvoices: "$8.2K",
};

export const incident = {
  title: "OCR latency elevated in Africa West",
  description:
    "PaddleOCR workers are processing slower than expected. Failover is active and verification completion remains within SLA.",
  severity: "major" as const,
};
