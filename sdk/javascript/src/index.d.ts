export const VERSION: string;
export class IdentityCoreError extends Error {}
export class IdentityCoreConnectionError extends IdentityCoreError {}
export class IdentityCoreTimeoutError extends IdentityCoreConnectionError {}
export class IdentityCoreAPIError extends IdentityCoreError { code: string; status: number; requestId: string; details: Record<string, unknown>; }
export interface VerificationSubjectInput { fullName?: string; full_name?: string; email?: string; phoneNumber?: string; phone_number?: string; dateOfBirth?: string; date_of_birth?: string; metadata?: Record<string, unknown>; }
export interface VerificationCreateInput { purpose: string; policyId?: string; policy_id?: string; projectId?: string; project_id?: string; verificationSubject?: VerificationSubjectInput; verification_subject?: VerificationSubjectInput; externalReference?: string; external_reference?: string; redirectUrl?: string; redirect_url?: string; metadata?: Record<string, unknown>; }
export interface RequestOptions { idempotencyKey?: string; requestId?: string; headers?: Record<string, string>; }
export interface IdentityCoreClientOptions { apiOrigin: string; clientId: string; clientSecret: string; fetch?: typeof fetch; timeout?: number; maxRetries?: number; retryBackoff?: number; allowBrowser?: boolean; }
export class IdentityCoreClient {
  constructor(options: IdentityCoreClientOptions);
  policies: { list(): Promise<Record<string, unknown>[]>; retrieve(id: string): Promise<Record<string, unknown>> };
  verifications: {
    create(input: VerificationCreateInput, options?: RequestOptions): Promise<Record<string, unknown>>;
    list(options?: { status?: string; externalReference?: string; page?: number; pageSize?: number }): Promise<any>;
    iterate(options?: { status?: string; externalReference?: string; pageSize?: number }): AsyncIterable<Record<string, unknown>>;
    retrieve(id: string): Promise<Record<string, unknown>>;
    cancel(id: string, options?: { reason?: string; idempotencyKey?: string }): Promise<Record<string, unknown>>;
    resendLink(id: string, options?: { channel?: string; idempotencyKey?: string }): Promise<Record<string, unknown>>;
    evidenceReport(id: string): Promise<Record<string, unknown>>;
  };
  health(): Promise<Record<string, unknown>>;
  request(method: string, path: string, body?: unknown, options?: RequestOptions): Promise<any>;
}
export function verifyWebhookSignature(payload: string | Uint8Array, options: { signature: string; timestamp: string | number; signingKey: string; toleranceSeconds?: number; now?: number }): boolean;

