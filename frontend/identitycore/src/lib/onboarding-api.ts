"use client";

import { graphqlRequest, restRequest } from "@/lib/api-client";
import type { AuthSession } from "@/lib/auth";

export interface OnboardingState {
  organizationId: string;
  organizationName: string;
  organizationSlug: string;
  organizationType: string;
  organizationCountry: string;
  organizationCountryName: string;
  organizationStatus: string;
  organizationTier: string;
  tenantId: string;
  tenantSlug: string;
  tenantStatus: string;
  administratorUserId: string;
  administratorFullName: string;
  administratorEmail: string;
  administratorCountry: string;
  administratorStatus: string;
  supportEmail: string;
  phoneNumber: string;
  website: string;
  requiresEmailVerification: boolean;
  emailVerifiedAt: string | null;
  onboardingStatus: string;
  currentStep: string;
  organizationVerificationSubmittedAt: string | null;
  organizationVerificationEditable: boolean;
  organizationVerificationReviewStatus: string;
  organizationVerificationReviewNote: string;
  organizationVerificationReviewedAt: string | null;
  businessRegistrationNumber: string;
  taxIdentificationNumber: string;
  registeredAddress: string;
  officialWebsite: string;
  supportingDocuments: Array<{ id: string; filename: string; file_size_bytes: number; status: string; storage_key: string; download_url: string }>;
  administratorIdentityVerificationStatus: string;
  administratorIdentityVerificationId: string;
  administratorIdentitySubmittedAt: string | null;
  platformReviewStatus: string;
  platformReviewNote: string;
  platformReviewedAt: string | null;
}

export interface RegisterPayload {
  onboarding: OnboardingState;
  nextAction: string;
  debugEmailVerificationUrl: string | null;
}

interface OrganizationOnboardingTypesResponse {
  organizationOnboardingTypes: string[];
}

interface RegisterResponse {
  registerOrganizationOnboarding: RegisterPayload;
}

interface VerifyEmailResponse {
  verifyOrganizationOnboardingEmail: {
    onboarding: OnboardingState;
    nextAction: string;
  };
}

interface CurrentOnboardingResponse {
  organizationOnboarding: OnboardingState;
}

interface SubmitOrganizationVerificationResponse {
  submitOrganizationOnboardingVerification: {
    onboarding: OnboardingState;
    nextAction: string;
  };
}

interface SubmitAdministratorIdentityResponse {
  submitAdministratorIdentityOnboardingVerification: {
    onboarding: OnboardingState;
    nextAction: string;
  };
}

interface CreateAdministratorVerificationResponse {
  createAdministratorOnboardingVerification: {
    verificationId: string;
    sessionId: string;
    sessionToken: string;
    verificationUrl: string;
    expiresAt: string;
    action: string;
  };
}

interface LoginResponse {
  tokens: {
    access: string;
  };
  user: AuthSession["user"];
}

export interface RegisterInput {
  fullName: string;
  businessEmail: string;
  password: string;
  organizationName: string;
  organizationType: string;
  organizationCountry: string;
  website: string;
  supportEmail: string;
  phoneNumber: string;
}

export interface OrganizationVerificationInput {
  businessRegistrationNumber: string;
  registeredAddress: string;
  officialWebsite: string;
  taxIdentificationNumber: string;
  supportingDocumentKeys: string[];
}

const MAX_ORGANIZATION_DOCUMENT_BYTES = 10 * 1024 * 1024;
const UPLOAD_TIMEOUT_MS = 60_000;

export async function createOrganizationDocumentUpload(file: File) {
  if (file.type.toLowerCase() !== "application/pdf" || !file.name.toLowerCase().endsWith(".pdf")) {
    throw new Error("Choose a PDF document.");
  }
  if (file.size <= 0) throw new Error("The selected PDF is empty.");
  if (file.size > MAX_ORGANIZATION_DOCUMENT_BYTES) throw new Error("Each PDF must be 10 MB or smaller.");
  const upload = await restRequest<{ document_id: string; filename: string; file_size_bytes: number; status: string; storage_key: string; upload_url: string; download_url: string }>(
    "/organization/me/verification-documents/upload/",
    { method: "POST", body: JSON.stringify({ filename: file.name, mime_type: file.type, file_size_bytes: file.size }) },
  );
  if (!upload.upload_url) throw new Error("Secure document storage is not configured. Contact support.");
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), UPLOAD_TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(upload.upload_url, {
      method: "PUT",
      headers: { "Content-Type": "application/pdf" },
      body: file,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("The document upload took too long. Check your connection and try again.");
    }
    throw new Error("The document could not be uploaded. Check your connection and try again.");
  } finally {
    window.clearTimeout(timeout);
  }
  if (!response.ok) throw new Error("The secure document upload failed. Please try again.");
  await restRequest(`/organization/me/verification-documents/${upload.document_id}/complete/`, { method: "POST", body: "{}" });
  return { id: upload.document_id, ...upload, status: "uploaded" };
}

export async function deleteOrganizationDocument(documentId: string) {
  await restRequest(`/organization/me/verification-documents/${documentId}/`, {
    method: "DELETE",
    body: "{}",
  });
}

export async function fetchOrganizationOnboardingTypes() {
  const data = await graphqlRequest<OrganizationOnboardingTypesResponse>(
    `
      query OrganizationOnboardingTypes {
        organizationOnboardingTypes
      }
    `,
    undefined,
    { useAuth: false },
  );

  return data.organizationOnboardingTypes;
}

export async function registerOrganizationOnboarding(input: RegisterInput) {
  const data = await graphqlRequest<RegisterResponse>(
    `
      mutation RegisterOrganizationOnboarding(
        $input: RegisterOrganizationOnboardingInput!
      ) {
        registerOrganizationOnboarding(input: $input) {
          nextAction
          debugEmailVerificationUrl
          onboarding {
            organizationId
            organizationName
            organizationSlug
            organizationType
            organizationCountry
            organizationStatus
            organizationTier
            tenantId
            tenantSlug
            tenantStatus
            administratorUserId
            administratorFullName
            administratorEmail
            administratorCountry
            administratorStatus
            supportEmail
            phoneNumber
            website
            requiresEmailVerification
            emailVerifiedAt
            onboardingStatus
            currentStep
            organizationVerificationSubmittedAt
            organizationVerificationEditable
            businessRegistrationNumber
            taxIdentificationNumber
            registeredAddress
            officialWebsite
            supportingDocuments
            administratorIdentityVerificationStatus
            administratorIdentityVerificationId
            administratorIdentitySubmittedAt
            platformReviewStatus
            platformReviewNote
            platformReviewedAt
          }
        }
      }
    `,
    { input },
    { useAuth: false },
  );

  return data.registerOrganizationOnboarding;
}

export async function verifyOrganizationOnboardingEmail(token: string) {
  const data = await graphqlRequest<VerifyEmailResponse>(
    `
      mutation VerifyOrganizationOnboardingEmail($token: String!) {
        verifyOrganizationOnboardingEmail(token: $token) {
          nextAction
          onboarding {
            organizationId
            organizationName
            organizationSlug
            organizationType
            organizationCountry
            organizationStatus
            organizationTier
            tenantId
            tenantSlug
            tenantStatus
            administratorUserId
            administratorFullName
            administratorEmail
            administratorCountry
            administratorStatus
            supportEmail
            phoneNumber
            website
            requiresEmailVerification
            emailVerifiedAt
            onboardingStatus
            currentStep
            organizationVerificationSubmittedAt
            organizationVerificationEditable
            businessRegistrationNumber
            taxIdentificationNumber
            registeredAddress
            officialWebsite
            supportingDocuments
            administratorIdentityVerificationStatus
            administratorIdentityVerificationId
            administratorIdentitySubmittedAt
            platformReviewStatus
            platformReviewNote
            platformReviewedAt
          }
        }
      }
    `,
    { token },
    { useAuth: false },
  );

  return data.verifyOrganizationOnboardingEmail;
}

export async function login(email: string, password: string) {
  return restRequest<LoginResponse>(
    "/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
    { useAuth: false },
  );
}

export async function fetchCurrentOnboarding() {
  const data = await graphqlRequest<CurrentOnboardingResponse>(`
    query CurrentOrganizationOnboarding {
      organizationOnboarding {
        organizationId
        organizationName
        organizationSlug
        organizationType
        organizationCountry
        organizationCountryName
        organizationStatus
        organizationTier
        tenantId
        tenantSlug
        tenantStatus
        administratorUserId
        administratorFullName
        administratorEmail
        administratorCountry
        administratorStatus
        supportEmail
        phoneNumber
        website
        requiresEmailVerification
        emailVerifiedAt
        onboardingStatus
        currentStep
        organizationVerificationSubmittedAt
        organizationVerificationEditable
        organizationVerificationReviewStatus
        organizationVerificationReviewNote
        organizationVerificationReviewedAt
        businessRegistrationNumber
        taxIdentificationNumber
        registeredAddress
        officialWebsite
        supportingDocuments
        administratorIdentityVerificationStatus
        administratorIdentityVerificationId
        administratorIdentitySubmittedAt
        platformReviewStatus
        platformReviewNote
        platformReviewedAt
      }
    }
  `);

  return data.organizationOnboarding;
}

export async function createAdministratorOnboardingVerification(reason = "") {
  const data = await graphqlRequest<CreateAdministratorVerificationResponse>(`
    mutation CreateAdministratorOnboardingVerification($reason: String!) {
      createAdministratorOnboardingVerification(reason: $reason) {
        verificationId
        sessionId
        sessionToken
        verificationUrl
        expiresAt
        action
      }
    }
  `, { reason });
  return data.createAdministratorOnboardingVerification;
}

export async function submitOrganizationVerification(
  input: OrganizationVerificationInput,
) {
  const data = await graphqlRequest<SubmitOrganizationVerificationResponse>(
    `
      mutation SubmitOrganizationVerification(
        $input: OrganizationVerificationInput!
      ) {
        submitOrganizationOnboardingVerification(input: $input) {
          nextAction
          onboarding {
            organizationId
            organizationName
            organizationSlug
            organizationType
            organizationCountry
            organizationStatus
            organizationTier
            tenantId
            tenantSlug
            tenantStatus
            administratorUserId
            administratorFullName
            administratorEmail
            administratorCountry
            administratorStatus
            supportEmail
            phoneNumber
            website
            requiresEmailVerification
            emailVerifiedAt
            onboardingStatus
            currentStep
            organizationVerificationSubmittedAt
            organizationVerificationEditable
            businessRegistrationNumber
            taxIdentificationNumber
            registeredAddress
            officialWebsite
            supportingDocuments
            administratorIdentityVerificationStatus
            administratorIdentityVerificationId
            administratorIdentitySubmittedAt
            platformReviewStatus
            platformReviewNote
            platformReviewedAt
          }
        }
      }
    `,
    { input },
  );

  return data.submitOrganizationOnboardingVerification;
}

export async function submitAdministratorIdentityVerification(
  verificationId: string,
) {
  const data = await graphqlRequest<SubmitAdministratorIdentityResponse>(
    `
      mutation SubmitAdministratorIdentityVerification(
        $verificationId: String!
      ) {
        submitAdministratorIdentityOnboardingVerification(
          verificationId: $verificationId
        ) {
          nextAction
          onboarding {
            organizationId
            organizationName
            organizationSlug
            organizationType
            organizationCountry
            organizationStatus
            organizationTier
            tenantId
            tenantSlug
            tenantStatus
            administratorUserId
            administratorFullName
            administratorEmail
            administratorCountry
            administratorStatus
            supportEmail
            phoneNumber
            website
            requiresEmailVerification
            emailVerifiedAt
            onboardingStatus
            currentStep
            organizationVerificationSubmittedAt
            organizationVerificationEditable
            businessRegistrationNumber
            taxIdentificationNumber
            registeredAddress
            officialWebsite
            supportingDocuments
            administratorIdentityVerificationStatus
            administratorIdentityVerificationId
            administratorIdentitySubmittedAt
            platformReviewStatus
            platformReviewNote
            platformReviewedAt
          }
        }
      }
    `,
    { verificationId },
  );

  return data.submitAdministratorIdentityOnboardingVerification;
}
