/// <reference types="node" />
export type JsonValue =
  | null
  | boolean
  | number
  | string
  | JsonValue[]
  | { [key: string]: JsonValue };
export interface JsonObject {
  [key: string]: JsonValue;
}
export class ProtocolError extends Error {}
export class StorageUnavailable extends Error {}
export const SIGNATURE_VERSION: "ic-provider-v1";
export const OPERATION_CONTRACT: "ic-provider-operations-v1";
export const MAX_BODY_BYTES: number;
export interface KeyOptions {
  keyId: string;
  secret: string;
  tenantId: string;
  environment: "sandbox" | "production";
  capabilities: readonly string[];
}
export class SigningKey implements KeyOptions {
  constructor(options: KeyOptions);
  readonly keyId: string;
  readonly secret: string;
  readonly tenantId: string;
  readonly environment: "sandbox" | "production";
  readonly capabilities: readonly string[];
}
export interface Binding extends JsonObject {
  operation_contract: "ic-provider-operations-v1";
  operation_id: string;
  configuration_id: string;
  tenant_id: string;
  project_id: string;
  environment: "sandbox" | "production";
  capability: string;
  contract_version: "1";
  request_sha256: string;
  lease_generation: number;
  deadline: string;
  callback_path: string;
  lease_token: string;
}
export interface ProviderResult extends JsonObject {
  contract_version: "1";
  capability: string;
  status: "completed" | "failed" | "inconclusive";
}
export interface OperationResponse {
  binding: Binding;
  status:
    | "pending"
    | "completed"
    | "failed"
    | "cancelled"
    | "deleted"
    | "expired";
  result?: ProviderResult;
  retry_after_seconds?: number;
}
export interface WireResponse {
  status: number;
  body: Buffer;
  headers: Record<string, string>;
}
export type MaybePromise<T> = T | Promise<T>;
export interface WorkerLeaseData {
  readonly operationId: string;
  readonly generation: number;
  readonly owner: string;
  readonly binding: Binding;
  readonly inputs: JsonObject;
}
export class WorkerLease implements WorkerLeaseData {
  constructor(
    id: string,
    generation: number,
    owner: string,
    binding: Binding,
    inputs: JsonObject,
  );
  readonly operationId: string;
  readonly generation: number;
  readonly owner: string;
  readonly binding: Binding;
  readonly inputs: JsonObject;
  toJSON(): { operationId: string; generation: number };
}
export interface OperationStore {
  claimNonce(digest: string, expires: number): MaybePromise<boolean>;
  admit(
    binding: Binding,
    inputs: JsonObject,
    deadline: Date,
  ): MaybePromise<OperationResponse>;
  poll(binding: Binding): MaybePromise<OperationResponse>;
  claimJob(options?: {
    leaseSeconds?: number;
  }): MaybePromise<WorkerLeaseData | null>;
  renew(
    lease: WorkerLeaseData,
    options?: { leaseSeconds?: number },
  ): MaybePromise<boolean>;
  complete(
    lease: WorkerLeaseData,
    result: ProviderResult,
  ): MaybePromise<OperationResponse>;
  control(
    binding: Binding,
    action: "cancel" | "delete",
  ): MaybePromise<OperationResponse>;
}
export class SQLiteStore implements OperationStore {
  constructor(
    path: string,
    options: { encryptionKey: Buffer; clock?: () => number },
  );
  clock: () => number;
  close(): void;
  claimNonce(digest: string, expires: number): boolean;
  admit(
    binding: Binding,
    inputs: JsonObject,
    deadline: Date,
  ): OperationResponse;
  poll(binding: Binding): OperationResponse;
  claimJob(options?: { leaseSeconds?: number }): WorkerLease | null;
  renew(lease: WorkerLeaseData, options?: { leaseSeconds?: number }): boolean;
  complete(lease: WorkerLeaseData, result: ProviderResult): OperationResponse;
  control(binding: Binding, action: "cancel" | "delete"): OperationResponse;
  expire(options?: { limit?: number }): number;
}
export type CapabilityHandler = (
  operationId: string | null,
  inputs: JsonObject,
) => MaybePromise<ProviderResult>;
export class ProviderRuntime {
  constructor(options: {
    keys: Record<string, SigningKey | KeyOptions>;
    store: OperationStore;
    handlers: Record<string, CapabilityHandler>;
    cancelHandler: (binding: Binding) => MaybePromise<boolean>;
    deleteHandler: (binding: Binding) => MaybePromise<boolean>;
  });
  handle(input: {
    method: string;
    path: string;
    body: Buffer;
    headers: Record<string, string>;
    now?: number;
  }): Promise<WireResponse>;
  workOnce(options?: {
    leaseSeconds?: number;
  }): Promise<OperationResponse | null>;
  callback(
    binding: Binding,
    options?: { timestamp?: number },
  ): Promise<{ body: Buffer; headers: Record<string, string> }>;
}
export function deriveSigningSecret(apiKey: string): string;
export function jsonBytes(value: unknown): Buffer;
export function parseJson(body: Buffer): JsonObject;
export function canonicalMessage(
  method: string,
  path: string,
  timestamp: number,
  nonce: string,
  body: Buffer,
): Buffer;
export function sign(input: {
  method: string;
  path: string;
  body: Buffer;
  key: KeyOptions;
  timestamp?: number;
  nonce?: string;
}): Record<string, string>;
export function verify(input: {
  method: string;
  path: string;
  body: Buffer;
  headers: Record<string, string>;
  keys: Record<string, KeyOptions>;
  claimNonce: (digest: string, expires: number) => MaybePromise<boolean>;
  now?: number;
  maxAgeSeconds?: number;
  expectedNonce?: string;
  replayNamespace?: string;
}): Promise<{ key: KeyOptions; nonce: string }>;
export function validateBinding(
  binding: Binding,
  key: KeyOptions,
  options?: { now?: Date; completion?: boolean },
): Date;
export function validateResult(
  capability: string,
  result: ProviderResult,
): ProviderResult;
export function bindingDigest(binding: Binding): string;
