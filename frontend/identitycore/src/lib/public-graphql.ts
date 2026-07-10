"use client";

import { graphqlRequest } from "@/lib/api-client";
import type { OnboardingState } from "@/lib/onboarding-api";

interface VerifyEmailResponse {
  verifyOrganizationOnboardingEmail: {
    onboarding: OnboardingState;
    nextAction: string;
  };
}

interface ResendResponse {
  resendOrganizationOnboardingEmailVerification: {
    ok: boolean;
    message: string;
    nextAction: string | null;
  };
}

interface PublicCatalogResponse {
  countries: Array<{
    code: string;
    name: string;
  }>;
  documentTypes: Array<{
    code: string;
    name: string;
  }>;
  countryProfiles: Array<{
    code: string;
    name: string;
    supportedDocumentTypes: Array<{
      documentType: string;
      localName: string;
    }>;
  }>;
}

interface ContactInquiryResponse {
  submitContactInquiry: {
    inquiryId: string;
    ok: boolean;
    message: string;
  };
}

interface PasswordResetRequestResponse {
  requestPasswordReset: {
    ok: boolean;
    message: string;
    nextAction: string | null;
  };
}

interface ResetPasswordResponse {
  resetPassword: {
    ok: boolean;
    message: string;
    nextAction: string | null;
  };
}

export async function verifyOrganizationOnboardingEmail(token: string) {
  const data = await graphqlRequest<VerifyEmailResponse>(
    `
      mutation VerifyOrganizationOnboardingEmail($token: String!) {
        verifyOrganizationOnboardingEmail(token: $token) {
          nextAction
          onboarding {
            organizationId
          }
        }
      }
    `,
    { token },
    { useAuth: false },
  );

  return data.verifyOrganizationOnboardingEmail;
}

export async function resendOrganizationOnboardingEmailVerification(
  businessEmail: string,
) {
  const data = await graphqlRequest<ResendResponse>(
    `
      mutation ResendOrganizationOnboardingEmailVerification(
        $businessEmail: String!
      ) {
        resendOrganizationOnboardingEmailVerification(
          businessEmail: $businessEmail
        ) {
          ok
          message
          nextAction
        }
      }
    `,
    { businessEmail },
    { useAuth: false },
  );

  return data.resendOrganizationOnboardingEmailVerification;
}

export async function fetchPublicCatalog() {
  const data = await graphqlRequest<PublicCatalogResponse>(
    `
      query PublicCatalog {
        countries {
          code
          name
        }
        documentTypes {
          code
          name
        }
        countryProfiles {
          code
          name
          supportedDocumentTypes {
            documentType
            localName
          }
        }
      }
    `,
    undefined,
    { useAuth: false },
  );

  return data;
}

export async function submitContactInquiry(input: {
  fullName: string;
  businessEmail: string;
  organizationName: string;
  interest: string;
  message: string;
}) {
  const data = await graphqlRequest<ContactInquiryResponse>(
    `
      mutation SubmitContactInquiry($input: ContactInquiryInput!) {
        submitContactInquiry(input: $input) {
          inquiryId
          ok
          message
        }
      }
    `,
    { input },
    { useAuth: false },
  );

  return data.submitContactInquiry;
}

export async function requestPasswordReset(email: string) {
  const data = await graphqlRequest<PasswordResetRequestResponse>(
    `
      mutation RequestPasswordReset($email: String!) {
        requestPasswordReset(email: $email) {
          ok
          message
          nextAction
        }
      }
    `,
    { email },
    { useAuth: false },
  );

  return data.requestPasswordReset;
}

export async function resetPassword(token: string, newPassword: string) {
  const data = await graphqlRequest<ResetPasswordResponse>(
    `
      mutation ResetPassword($token: String!, $newPassword: String!) {
        resetPassword(token: $token, newPassword: $newPassword) {
          ok
          message
          nextAction
        }
      }
    `,
    { token, newPassword },
    { useAuth: false },
  );

  return data.resetPassword;
}
