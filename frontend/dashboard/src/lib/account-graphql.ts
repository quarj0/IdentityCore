"use client";

import { graphqlRequest } from "@/lib/api-client";

interface ChangePasswordResponse {
  changePassword: {
    ok: boolean;
    message: string;
    nextAction: string | null;
  };
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
) {
  const data = await graphqlRequest<ChangePasswordResponse>(
    `
      mutation ChangePassword(
        $currentPassword: String!
        $newPassword: String!
      ) {
        changePassword(
          currentPassword: $currentPassword
          newPassword: $newPassword
        ) {
          ok
          message
          nextAction
        }
      }
    `,
    { currentPassword, newPassword },
  );

  return data.changePassword;
}
