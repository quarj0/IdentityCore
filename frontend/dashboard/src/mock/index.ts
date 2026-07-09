export const mockSearchItems = [
  { label: "Default Sandbox", href: "/projects/demo", type: "Project" },
  { label: "Customer onboarding", href: "/workflows/demo", type: "Workflow" },
  {
    label: "Customer onboarding template",
    href: "/templates/demo",
    type: "Template",
  },
  {
    label: "Verification request",
    href: "/verifications/demo",
    type: "Verification",
  },
  { label: "API keys", href: "/api-keys", type: "Settings" },
  { label: "Webhooks", href: "/webhooks", type: "Developers" },
  { label: "Documentation", href: "http://localhost:3003", type: "Docs" },
];

export const mockNotifications = [
  {
    id: "ntf_1",
    title: "Complete organization profile",
    description: "Your workspace still needs organization details.",
    status: "Unread",
    time: "Just now",
  },
  {
    id: "ntf_2",
    title: "Sandbox enabled",
    description: "Your sandbox environment is ready.",
    status: "Read",
    time: "Today",
  },
  {
    id: "ntf_3",
    title: "Create your first workflow",
    description: "Start from a template or build a custom workflow.",
    status: "Unread",
    time: "Today",
  },
];

export const mockTableRows = [
  { id: "1", name: "Default Sandbox", status: "Active", date: "Today" },
  { id: "2", name: "Customer onboarding", status: "Draft", date: "Today" },
  { id: "3", name: "Sandbox API key", status: "Active", date: "Today" },
];
