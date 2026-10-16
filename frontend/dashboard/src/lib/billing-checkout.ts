import type { PaymentProvider } from "./billing-api";

export function checkedCheckoutUrl(value: string, provider: PaymentProvider) {
  const hosts = {
    paystack: "checkout.paystack.com",
    stripe: "checkout.stripe.com",
  };
  const url = new URL(value);
  if (
    url.protocol !== "https:" ||
    url.hostname !== hosts[provider] ||
    url.username ||
    url.password ||
    (url.port && url.port !== "443")
  ) {
    throw new Error("Unexpected payment checkout URL.");
  }
  return url.href;
}
