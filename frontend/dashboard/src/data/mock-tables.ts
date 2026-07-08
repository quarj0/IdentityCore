export const tableData = {
  projects: {
    columns: [
      { key: "name", label: "Project" },
      { key: "environment", label: "Environment" },
      { key: "status", label: "Status" },
      { key: "updated", label: "Updated" },
    ],
    rows: [
      {
        name: "Default Sandbox",
        environment: "Sandbox",
        status: "Active",
        updated: "Today",
      },
    ],
  },

  templates: {
    columns: [
      { key: "name", label: "Template" },
      { key: "category", label: "Category" },
      { key: "status", label: "Status" },
      { key: "updated", label: "Updated" },
    ],
    rows: [
      {
        name: "Customer onboarding",
        category: "Financial services",
        status: "Available",
        updated: "Today",
      },
      {
        name: "Student enrollment",
        category: "Education",
        status: "Available",
        updated: "Today",
      },
    ],
  },

  requests: {
    columns: [
      { key: "id", label: "Request" },
      { key: "workflow", label: "Workflow" },
      { key: "status", label: "Status" },
      { key: "created", label: "Created" },
    ],
    rows: [],
  },

  subjects: {
    columns: [
      { key: "subject", label: "Subject" },
      { key: "email", label: "Email" },
      { key: "status", label: "Status" },
      { key: "created", label: "Created" },
    ],
    rows: [],
  },

  reviews: {
    columns: [
      { key: "case", label: "Case" },
      { key: "workflow", label: "Workflow" },
      { key: "status", label: "Status" },
      { key: "created", label: "Created" },
    ],
    rows: [],
  },

  apiKeys: {
    columns: [
      { key: "name", label: "Key" },
      { key: "environment", label: "Environment" },
      { key: "status", label: "Status" },
      { key: "created", label: "Created" },
    ],
    rows: [
      {
        name: "Sandbox secret key",
        environment: "Sandbox",
        status: "Active",
        created: "Today",
      },
    ],
  },

  webhooks: {
    columns: [
      { key: "url", label: "Endpoint" },
      { key: "events", label: "Events" },
      { key: "status", label: "Status" },
      { key: "created", label: "Created" },
    ],
    rows: [],
  },

  auditLogs: {
    columns: [
      { key: "event", label: "Event" },
      { key: "actor", label: "Actor" },
      { key: "status", label: "Status" },
      { key: "time", label: "Time" },
    ],
    rows: [
      {
        event: "Workspace created",
        actor: "Workspace admin",
        status: "Complete",
        time: "Just now",
      },
      {
        event: "Sandbox enabled",
        actor: "System",
        status: "Complete",
        time: "Just now",
      },
    ],
  },

  team: {
    columns: [
      { key: "name", label: "Name" },
      { key: "email", label: "Email" },
      { key: "role", label: "Role" },
      { key: "status", label: "Status" },
    ],
    rows: [
      {
        name: "Workspace Admin",
        email: "admin@example.com",
        role: "Tenant Administrator",
        status: "Active",
      },
    ],
  },
};
