"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type PlatformAdmin = {
  publicId: string;
  email: string;
  firstName: string;
  lastName: string;
  phoneNumber: string;
  status: string;
  tenantPublicId: string | null;
  tenantName: string | null;
  tenantStatus: string | null;
  isPlatformAdmin: boolean;
  mfaEnabled: boolean;
  roles: string[];
  notificationPreferences: Record<string, unknown> | null;
  lastLoginAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

type UsersResponse = {
  platformAdmins: PlatformAdmin[];
};

type InvitePlatformAdminResponse = {
  invitePlatformAdmin: {
    invitation: {
      id: string;
      email: string;
      roleName: string;
      status: string;
    };
  };
};

type DeactivatePlatformAdminResponse = { deactivatePlatformAdmin: PlatformAdmin };

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "active") return "success";
  if (status === "invited") return "warning";
  if (status === "disabled") return "danger";
  return "info";
}

function toRecord(user: PlatformAdmin): AdminRecord {
  const fullName = [user.firstName, user.lastName].filter(Boolean).join(" ").trim();
  return {
    id: user.publicId,
    title: fullName || user.email,
    subtitle: user.email,
    status: user.status,
    statusTone: tone(user.status),
    primaryMeta: user.tenantName ?? "Platform",
    secondaryMeta: user.roles[0] ?? "Admin",
    tertiaryMeta: user.mfaEnabled ? "MFA enabled" : "MFA disabled",
    owner: user.tenantStatus ?? "Platform",
    updatedAt: formatDateTime(user.updatedAt ?? user.lastLoginAt ?? user.createdAt ?? undefined),
    href: `/users/${user.publicId}`,
  };
}

export async function fetchPlatformAdminRecords() {
  const data = await graphqlRequest<UsersResponse>(
    `
      query PlatformAdmins {
        platformAdmins {
          publicId
          email
          firstName
          lastName
          phoneNumber
          status
          tenantPublicId
          tenantName
          tenantStatus
          isPlatformAdmin
          mfaEnabled
          roles
          notificationPreferences
          lastLoginAt
          createdAt
          updatedAt
        }
      }
    `,
  );
  return data.platformAdmins.map(toRecord);
}

export async function fetchPlatformAdminRecord(userId: string) {
  const data = await graphqlRequest<UsersResponse>(
    `
      query PlatformAdmin {
        platformAdmins {
          publicId
          email
          firstName
          lastName
          phoneNumber
          status
          tenantPublicId
          tenantName
          tenantStatus
          isPlatformAdmin
          mfaEnabled
          roles
          notificationPreferences
          lastLoginAt
          createdAt
          updatedAt
        }
      }
    `,
  );
  const user = data.platformAdmins.find((item) => item.publicId === userId);
  return user ?? null;
}

export async function invitePlatformAdmin(email: string, roleName: string) {
  const data = await graphqlRequest<InvitePlatformAdminResponse>(
    `
      mutation InvitePlatformAdmin($email: String!, $roleName: String!) {
        invitePlatformAdmin(email: $email, roleName: $roleName) {
          invitation {
            id
            email
            roleName
            status
          }
        }
      }
    `,
    { email: email.trim(), roleName },
  );

  return data.invitePlatformAdmin.invitation;
}

export async function deactivatePlatformAdmin(userId: string, reason: string) {
  const data = await graphqlRequest<DeactivatePlatformAdminResponse>(
    `mutation DeactivatePlatformAdmin($userId: String!, $reason: String!) {
      deactivatePlatformAdmin(userId: $userId, reason: $reason) { publicId status }
    }`,
    { userId, reason: reason.trim() },
  );
  return data.deactivatePlatformAdmin;
}

export function buildPlatformAdminConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Platform access",
    listTitle: "Platform admins",
    listDescription:
      "Manage IdentityCore staff access, roles, invitations and account security from live backend data.",
    detailBreadcrumbLabel: "Platform admins",
    searchPlaceholder: "Search admins...",
    createLabel: "Invite admin",
    exportLabel: "Export",
    filters: ["Role", "Status", "Security"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Role", value: record.secondaryMeta, helper: "primary role" },
      { label: "Tenant", value: record.primaryMeta, helper: "scope" },
      { label: "MFA", value: record.tertiaryMeta, helper: "security" },
      { label: "Updated", value: record.updatedAt, helper: "backend" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Admin profile",
        description: "Identity and access details for the platform admin account.",
        items: [
          { label: "Name", value: record.title },
          { label: "Email", value: record.subtitle },
          { label: "Status", value: record.status },
          { label: "Tenant scope", value: record.primaryMeta },
        ],
      },
      {
        title: "Access controls",
        description: "Current platform access metadata.",
        items: [
          { label: "Primary role", value: record.secondaryMeta },
          { label: "MFA", value: record.tertiaryMeta },
          { label: "Last updated", value: record.updatedAt },
        ],
      },
    ],
  };
}

export function adminUserToAdminRecord(user: PlatformAdmin): AdminRecord {
  return toRecord(user);
}
