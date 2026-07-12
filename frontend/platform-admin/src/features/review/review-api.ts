"use client";

import { graphqlRequest } from "@/lib/admin-api";

export interface OrganizationReviewDocument {
  id: string;
  filename: string;
  file_size_bytes: number;
  status: string;
  storage_key: string;
  download_url: string;
}

export interface OrganizationReviewItem {
  organizationId: string;
  organizationName: string;
  organizationSlug: string;
  organizationType: string;
  organizationCountry: string;
  organizationCountryName: string;
  organizationStatus: string;
  tenantStatus: string;
  administratorFullName: string;
  administratorEmail: string;
  supportEmail: string;
  website: string;
  onboardingStatus: string;
  currentStep: string;
  organizationVerificationSubmittedAt: string | null;
  organizationVerificationEditable: boolean;
  organizationVerificationReviewStatus: string;
  organizationVerificationChangedAfterApproval: boolean;
  organizationVerificationReviewedAt: string | null;
  organizationVerificationReviewNote: string;
  platformReviewStatus: string;
  platformReviewNote: string;
  platformReviewedAt: string | null;
  businessRegistrationNumber: string;
  taxIdentificationNumber: string;
  registeredAddress: string;
  officialWebsite: string;
  reviewPriority?: string | null;
  reviewSummary?: string | null;
  supportingDocuments: OrganizationReviewDocument[];
}

interface ReviewQueueResponse {
  organizationReviewQueue: OrganizationReviewItem[];
}

interface ReviewItemResponse {
  organizationReview: OrganizationReviewItem | null;
}

interface ReviewMutationResponse {
  reviewOrganizationOnboarding: {
    nextAction: string;
    onboarding: OrganizationReviewItem;
  };
}

const REVIEW_FIELDS = `
  organizationId
  organizationName
  organizationSlug
  organizationType
  organizationCountry
  organizationCountryName
  organizationStatus
  tenantStatus
  administratorFullName
  administratorEmail
  supportEmail
  website
  onboardingStatus
  currentStep
  organizationVerificationSubmittedAt
  organizationVerificationEditable
  organizationVerificationReviewStatus
  organizationVerificationChangedAfterApproval
  organizationVerificationReviewedAt
  organizationVerificationReviewNote
  platformReviewStatus
  platformReviewNote
  platformReviewedAt
  businessRegistrationNumber
  taxIdentificationNumber
  registeredAddress
  officialWebsite
  reviewPriority
  reviewSummary
  supportingDocuments {
    id
    filename
    file_size_bytes
    status
    storage_key
    download_url
  }
`;

export async function fetchOrganizationReviewQueue(pageSize = 50) {
  const data = await graphqlRequest<ReviewQueueResponse>(
    `
      query OrganizationReviewQueue($page: Int!, $pageSize: Int!) {
        organizationReviewQueue(page: $page, pageSize: $pageSize) {
          ${REVIEW_FIELDS}
        }
      }
    `,
    { page: 1, pageSize },
  );

  return data.organizationReviewQueue;
}

export async function fetchOrganizationReview(organizationId: string) {
  const data = await graphqlRequest<ReviewItemResponse>(
    `
      query OrganizationReview($organizationId: String!) {
        organizationReview(organizationId: $organizationId) {
          ${REVIEW_FIELDS}
        }
      }
    `,
    { organizationId },
  );

  return data.organizationReview;
}

export async function reviewOrganization(
  organizationId: string,
  decision: "approved" | "rejected" | "needs_information",
  note = "",
) {
  const data = await graphqlRequest<ReviewMutationResponse>(
    `
      mutation ReviewOrganization(
        $organizationId: String!
        $decision: String!
        $note: String!
      ) {
        reviewOrganizationOnboarding(
          organizationId: $organizationId
          decision: $decision
          note: $note
        ) {
          nextAction
          onboarding {
            ${REVIEW_FIELDS}
          }
        }
      }
    `,
    { organizationId, decision, note },
  );

  return data.reviewOrganizationOnboarding;
}
