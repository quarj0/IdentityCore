import assert from "node:assert/strict";
import test from "node:test";
import { checkedCheckoutUrl } from "./billing-checkout.ts";

test("accepts each provider's HTTPS checkout URL", () => {
  for (const provider of ["paystack"] as const) {
    const url = `https://checkout.${provider}.com/pay/synthetic`;
    assert.equal(checkedCheckoutUrl(url, provider), url);
  }
});

test("rejects mismatched hosts, credentials, protocols and ports", () => {
  for (const url of [
    "https://checkout.other-provider.com/pay/synthetic",
    "https://checkout.paystack.com.evil.example/pay",
    "http://checkout.paystack.com/pay",
    "https://user:password@checkout.paystack.com/pay",
    "https://checkout.paystack.com:444/pay",
    "javascript:alert(1)",
  ]) {
    assert.throws(() => checkedCheckoutUrl(url, "paystack"));
  }
});
