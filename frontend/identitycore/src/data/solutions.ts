import {
  Building2,
  GraduationCap,
  HeartPulse,
  Landmark,
  RadioTower,
  Users,
  Workflow,
} from "lucide-react";

export const solutions = [
  {
    slug: "government",
    title: "Government",
    description:
      "Build citizen verification, service access, permit, licensing, and national identity workflows.",
    icon: Building2,
    useCases: ["Citizen access", "Permits", "National ID"],
    workflows: [
      "Citizen service access",
      "Permit application",
      "Driver licensing",
      "Public benefits verification",
    ],
    capabilities: [
      "Government ID provider routing",
      "Consent records",
      "Audit trails",
      "Policy-controlled access",
      "Private deployment readiness",
    ],
  },
  {
    slug: "financial-services",
    title: "Financial services",
    description:
      "Create identity workflows for onboarding, KYC, merchant checks, loan applications, and risk operations.",
    icon: Landmark,
    useCases: ["KYC", "Merchant checks", "Risk"],
    workflows: [
      "Customer onboarding",
      "Merchant KYC",
      "Loan application",
      "High-risk manual review",
    ],
    capabilities: [
      "Document intelligence",
      "Face matching",
      "Liveness checks",
      "Risk scoring",
      "Webhook results",
    ],
  },
  {
    slug: "education",
    title: "Education",
    description:
      "Verify students for admissions, examinations, online learning, certificates, and campus services.",
    icon: GraduationCap,
    useCases: ["Admissions", "Exams", "Certificates"],
    workflows: [
      "Student enrollment",
      "Exam registration",
      "Certificate issuance",
      "Online learning identity check",
    ],
    capabilities: [
      "Student ID workflows",
      "Document capture",
      "Selfie verification",
      "Manual review",
      "Audit evidence",
    ],
  },
  {
    slug: "healthcare",
    title: "Healthcare",
    description:
      "Support patient registration, telemedicine, insurance checks, and controlled healthcare access.",
    icon: HeartPulse,
    useCases: ["Patients", "Telemedicine", "Insurance"],
    workflows: [
      "Patient registration",
      "Telemedicine identity",
      "Insurance verification",
      "Controlled access workflow",
    ],
    capabilities: [
      "Consent-first workflows",
      "Document verification",
      "Policy decisions",
      "Private media access",
      "Reviewer queues",
    ],
  },
  {
    slug: "telecommunications",
    title: "Telecommunications",
    description:
      "Power SIM registration, eSIM activation, subscriber checks, and customer re-verification workflows.",
    icon: RadioTower,
    useCases: ["SIM KYC", "eSIM", "Subscribers"],
    workflows: [
      "SIM registration",
      "eSIM activation",
      "Subscriber re-verification",
      "Retail agent workflow",
    ],
    capabilities: [
      "KYC templates",
      "Provider routing",
      "API workflows",
      "Webhook events",
      "Policy enforcement",
    ],
  },
  {
    slug: "hr-workforce",
    title: "HR and workforce",
    description:
      "Verify employees, contractors, vendors, and visitors before granting access or onboarding.",
    icon: Users,
    useCases: ["Employees", "Contractors", "Visitors"],
    workflows: [
      "Employee onboarding",
      "Contractor verification",
      "Visitor access",
      "Vendor identity check",
    ],
    capabilities: [
      "Identity documents",
      "Face matching",
      "Review approvals",
      "Audit logs",
      "Access workflow support",
    ],
  },
  {
    slug: "enterprise-platforms",
    title: "Enterprise platforms",
    description:
      "Embed identity workflows into marketplaces, SaaS products, communities, and digital platforms.",
    icon: Workflow,
    useCases: ["Marketplaces", "SaaS", "Platforms"],
    workflows: [
      "User verification",
      "Marketplace trust",
      "Vendor onboarding",
      "Platform access checks",
    ],
    capabilities: [
      "REST APIs",
      "Hosted verification links",
      "Webhooks",
      "Workflow templates",
      "Provider orchestration",
    ],
  },
];

export function getSolution(slug: string) {
  return solutions.find((solution) => solution.slug === slug);
}
