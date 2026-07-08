"use client";

import { graphqlRequest, restRequest } from "@/lib/api-client";
import type { AuthSession } from "@/lib/auth";

export interface OnboardingState {
  organizationId: string;
  organizationName: string;
  organizationSlug: string;
  organizationType: string;
  organizationCountry: string;
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

interface LoginResponse {
  tokens: {
    access: string;
    refresh: string;
  };
  user: AuthSession["user"];
}

export interface RegisterInput {
  fullName: string;
  businessEmail: string;
  password: string;
  country: string;
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
