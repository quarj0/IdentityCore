import assert from "node:assert/strict";
import { test } from "node:test";
import { countryLabel, localizeText } from "../src/lib/i18n.ts";

test("known document retry messages translate without changing document identity", () => {
  for (const message of [
    "We couldn't process your previous National ID just now. Please capture it again to continue.",
    "Your previous National ID image did not meet the capture quality requirements. Use good lighting, avoid glare and blur, and try again.",
    "That image appears to be Passport, not National ID. Please capture the physical National ID and try again.",
    "We could not read enough information to confirm this as National ID. Capture the full physical document in clear, even lighting and try again.",
    "Your previous National ID image could not be verified. Please capture the physical National ID and try again.",
  ]) {
    const translated = localizeText("ar", message);
    assert.match(translated, /بطاقة الهوية الوطنية/);
    assert.doesNotMatch(translated, /National ID|Passport/);
    assert.equal(localizeText("en", message), message);
  }
  const branded =
    "We couldn't process your previous Tenant Document Name just now. Please capture it again to continue.";
  assert.match(localizeText("ar", branded), /Tenant Document Name/);
});

test("supported labels, outcomes and controls have Arabic copy", () => {
  for (const text of [
    "Begin live camera check",
    "Submit live check",
    "Continue on another device",
    "Switch to dark theme",
    "Consent template version",
    "Your verification was submitted and requires additional review.",
    "Verification session is not authenticated.",
  ]) {
    assert.match(localizeText("ar", text), /[\u0600-\u06ff]/);
  }
  assert.equal(
    localizeText("ar", "Unrecognized organization content"),
    "Unrecognized organization content",
  );
});

test("country names follow the selected locale and preserve unknown supplied labels", () => {
  assert.equal(countryLabel("ar", "GH", "Ghana"), "غانا");
  assert.equal(countryLabel("en", "GH", "Ghana"), "Ghana");
  assert.equal(
    countryLabel("ar", "ZZ", "Synthetic country"),
    "Synthetic country",
  );
  assert.equal(countryLabel("ar", "invalid", "Supplied name"), "Supplied name");
});
