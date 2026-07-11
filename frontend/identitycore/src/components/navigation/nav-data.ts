import {
  BookOpen,
  Building2,
  Code2,
  Contact,
//   FileText,
  FlaskConical,
  Layers3,
  LockKeyhole,
  Network,
  Route,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const DOCS_URL = process.env.NEXT_PUBLIC_DOCS_URL ?? "http://localhost:3003";

export interface NavItem {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
  external?: boolean;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Platform",
    items: [
      {
        href: "/platform",
        label: "Platform overview",
        description: "Identity infrastructure, providers, policies, and data.",
        icon: Layers3,
      },
      {
        href: "/how-it-works",
        label: "How it works",
        description: "See how workflows move from request to decision.",
        icon: Route,
      },
      {
        href: "/templates",
        label: "Workflow templates",
        description: "Start from official identity workflow templates.",
        icon: Workflow,
      },
      {
        href: "/solutions",
        label: "Solutions",
        description: "Use cases for governments, enterprises, and platforms.",
        icon: Building2,
      },
    ],
  },
  {
    label: "Developers",
    items: [
      {
        href: "/developers",
        label: "Developer overview",
        description: "APIs, webhooks, sandbox, and integration paths.",
        icon: Code2,
      },
      {
        href: DOCS_URL,
        label: "Documentation",
        description: "Guides, API reference, examples, and SDKs.",
        icon: BookOpen,
        external: true,
      },
      {
        href: "/verification",
        label: "Sandbox verification",
        description: "Complete the live document, selfie, liveness, and result flow.",
        icon: FlaskConical,
      },
    ],
  },
  {
    label: "Services",
    items: [
      {
        href: "/templates/customer-onboarding",
        label: "Identity workflows",
        description: "Onboarding, verification, review, and trust flows.",
        icon: Network,
      },
      {
        href: "/templates/student-enrollment",
        label: "Verification templates",
        description: "Reusable workflows for common identity use cases.",
        icon: Sparkles,
      },
      {
        href: "/security",
        label: "Security & governance",
        description: "Privacy, consent, audit, retention, and controls.",
        icon: ShieldCheck,
      },
    ],
  },
  {
    label: "Resources",
    items: [
      {
        href: "/security",
        label: "Security",
        description: "How IdentityCore protects sensitive identity data.",
        icon: LockKeyhole,
      },
    //   {
    //     href: "/pricing",
    //     label: "Pricing",
    //     description: "Plans for sandbox, SaaS, and enterprise deployments.",
    //     icon: FileText,
    //   },
      {
        href: "/contact",
        label: "Contact",
        description: "Talk to us about identity infrastructure.",
        icon: Contact,
      },
      {
        href: "/forgot-password",
        label: "Password reset",
        description: "Request a reset link or recover account access.",
        icon: LockKeyhole,
      },
    ],
  },
];
