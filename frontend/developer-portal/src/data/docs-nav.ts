import {
  BookOpen,
  Code2,
  FlaskConical,
  KeyRound,
  Radio,
  ScrollText,
  TerminalSquare,
  Webhook,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface DocsNavItem {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
}

export interface DocsNavGroup {
  title: string;
  items: DocsNavItem[];
}

export const docsNav: DocsNavGroup[] = [
  {
    title: "Get started",
    items: [
      {
        href: "/",
        label: "Overview",
        description: "IdentityCore developer platform",
        icon: BookOpen,
      },
      {
        href: "/quickstart",
        label: "Quickstart",
        description: "Create your first verification",
        icon: TerminalSquare,
      },
      {
        href: "/authentication",
        label: "Authentication",
        description: "API keys and secure access",
        icon: KeyRound,
      },
    ],
  },
  {
    title: "Build",
    items: [
      {
        href: "/api-reference",
        label: "API reference",
        description: "REST endpoints and payloads",
        icon: Code2,
      },
      {
        href: "/webhooks",
        label: "Webhooks",
        description: "Events and delivery behavior",
        icon: Webhook,
      },
      {
        href: "/webhooks/signatures",
        label: "Webhook signatures",
        description: "Verify webhook event authenticity",
        icon: KeyRound,
      },
      {
        href: "/sandbox",
        label: "Sandbox",
        description: "Test the live API safely",
        icon: FlaskConical,
      },
      {
        href: "/examples",
        label: "Examples",
        description: "Common integration patterns",
        icon: Radio,
      },
    ],
  },
  {
    title: "Updates",
    items: [
      {
        href: "/changelog",
        label: "Changelog",
        description: "Product and API updates",
        icon: ScrollText,
      },
      {
        href: "/errors",
        label: "Error codes",
        description: "Common API error responses",
        icon: ScrollText,
      },
      {
        href: "/sdk",
        label: "SDKs",
        description: "Client libraries and SDK plans",
        icon: Code2,
      },
      {
        href: "/cli",
        label: "CLI",
        description: "Command line tooling",
        icon: TerminalSquare,
      },
    ],
  },
];
