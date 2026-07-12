"use client";

import { graphqlRequest } from "@/lib/admin-api";

type DashboardSummary = {
  organizationsTotal: number;
  organizationsPendingReview: number;
  organizationsActive: number;
  tenantsTotal: number;
  tenantsPendingReview: number;
  usersTotal: number;
  platformAdminsTotal: number;
  apiClientsTotal: number;
  webhookEndpointsTotal: number;
  providersTotal: number;
  auditEventsTotal: number;
  workflowsTotal: number;
  workflowVersionsTotal: number;
  billingRecordsTotal: number;
  analyticsDashboardsTotal: number;
  incidentsTotal: number;
  securityCasesTotal: number;
  supportTicketsTotal: number;
  templatesTotal: number;
  featureFlagsTotal: number;
};

type DashboardResponse = {
  platformDashboardSummary: DashboardSummary;
};

export async function fetchPlatformDashboardSummary() {
  const data = await graphqlRequest<DashboardResponse>(
    `
      query PlatformDashboardSummary {
        platformDashboardSummary {
          organizationsTotal
          organizationsPendingReview
          organizationsActive
          tenantsTotal
          tenantsPendingReview
          usersTotal
          platformAdminsTotal
          apiClientsTotal
          webhookEndpointsTotal
          providersTotal
          auditEventsTotal
          workflowsTotal
          workflowVersionsTotal
          billingRecordsTotal
          analyticsDashboardsTotal
          incidentsTotal
          securityCasesTotal
          supportTicketsTotal
          templatesTotal
          featureFlagsTotal
        }
      }
    `,
  );
  return data.platformDashboardSummary;
}
