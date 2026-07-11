export class IdentityCoreError extends Error {
  constructor(message) {
    super(message);
    this.name = "IdentityCoreError";
  }
}

export class IdentityCoreAPIError extends IdentityCoreError {
  constructor(message, { code = "request_failed", status = 500, requestId = "", details = {} } = {}) {
    super(message);
    this.name = "IdentityCoreAPIError";
    this.code = code;
    this.status = status;
    this.requestId = requestId;
    this.details = details;
  }
}

function humanMessage(message) {
  const lower = String(message || "").toLowerCase();
  if (
    lower.includes("unexpected token") ||
    lower.includes("invalidtag") ||
    lower.includes("not valid json") ||
    lower.includes("json.parse") ||
    lower.includes("syntaxerror")
  ) {
    return "The service is temporarily unavailable. Please try again shortly.";
  }
  return message || "Request failed. Please try again.";
}

function compactQuery(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

function subjectToApi(input = {}) {
  return {
    full_name: input.fullName ?? input.full_name ?? "",
    email: input.email ?? "",
    phone_number: input.phoneNumber ?? input.phone_number ?? "",
    date_of_birth: input.dateOfBirth ?? input.date_of_birth ?? undefined,
    metadata: input.metadata ?? {},
  };
}

export class IdentityCoreClient {
  constructor({ apiOrigin, clientId, clientSecret, fetch: fetchImpl = globalThis.fetch, timeout = 30000 }) {
    if (!apiOrigin) throw new IdentityCoreError("apiOrigin is required.");
    if (!clientId) throw new IdentityCoreError("clientId is required.");
    if (!clientSecret) throw new IdentityCoreError("clientSecret is required.");
    if (!fetchImpl) throw new IdentityCoreError("A fetch implementation is required.");

    this.apiOrigin = apiOrigin.replace(/\/$/, "");
    this.clientId = clientId;
    this.clientSecret = clientSecret;
    this.fetch = fetchImpl;
    this.timeout = timeout;

    this.policies = {
      list: () => this.request("GET", "/policies/"),
      retrieve: (policyId) => this.request("GET", `/policies/${policyId}`),
    };

    this.verifications = {
      create: (input) =>
        this.request("POST", "/verifications/", {
          purpose: input.purpose,
          policy_id: input.policyId ?? input.policy_id,
          verification_subject: subjectToApi(input.verificationSubject ?? input.verification_subject),
          external_reference: input.externalReference ?? input.external_reference ?? "",
          redirect_url: input.redirectUrl ?? input.redirect_url ?? "",
          metadata: input.metadata ?? {},
        }),
      list: ({ status = "", externalReference = "", page, pageSize } = {}) =>
        this.request(
          "GET",
          `/verifications/${compactQuery({
            status,
            external_reference: externalReference,
            page,
            page_size: pageSize,
          })}`,
        ),
      retrieve: (verificationId) => this.request("GET", `/verifications/${verificationId}`),
      cancel: (verificationId, { reason = "" } = {}) =>
        this.request("POST", `/verifications/${verificationId}/cancel`, { reason }),
      resendLink: (verificationId, { channel = "email" } = {}) =>
        this.request("POST", `/verifications/${verificationId}/resend-link`, { channel }),
      evidenceReport: (verificationId) =>
        this.request("GET", `/verifications/${verificationId}/evidence-report`),
    };
  }

  health() {
    return this.request("GET", "/health");
  }

  async request(method, path, body) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    const headers = {
      Accept: "application/json",
      "X-Client-Id": this.clientId,
      Authorization: `Bearer ${this.clientSecret}`,
    };
    const init = { method, headers, signal: controller.signal };
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(body);
    }

    try {
      const response = await this.fetch(`${this.apiOrigin}/api/v1${path}`, init);
      return await this.parse(response);
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async parse(response) {
    const text = await response.text();
    let payload;
    try {
      payload = JSON.parse(text);
    } catch (error) {
      throw new IdentityCoreAPIError(
        "The service is temporarily unavailable. Please try again shortly.",
        { code: "invalid_response", status: response.status },
      );
    }

    if (!response.ok || payload.success !== true) {
      const error = payload.error ?? {};
      throw new IdentityCoreAPIError(humanMessage(error.message), {
        code: error.code ?? "request_failed",
        status: response.status,
        requestId: payload.request_id ?? "",
        details: error.details ?? {},
      });
    }

    return payload.data;
  }
}
