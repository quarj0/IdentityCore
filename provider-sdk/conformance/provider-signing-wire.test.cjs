const assert = require('node:assert/strict');
const { createHmac, createHash } = require('node:crypto');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const test = require('node:test');

const fixture = JSON.parse(readFileSync(resolve(__dirname, '../../docs/fixtures/provider-signing-wire-v1.json'), 'utf8'));
const secret = createHmac('sha256', Buffer.from(fixture.api_credential, 'ascii'))
  .update('identitycore-provider-hmac-v1', 'ascii').digest('hex');
function signature(item, body = item.raw_body) {
  const canonical = ['ic-provider-v1', item.method, item.path, String(item.timestamp),
    item.nonce, createHash('sha256').update(body, 'utf8').digest('hex')].join('\n');
  return createHmac('sha256', Buffer.from(secret, 'utf8')).update(canonical, 'utf8').digest('hex');
}
for (const item of fixture.cases) {
  test(`verifies exact ${item.name} wire bytes across numeric and Unicode boundaries`, () => {
    assert.equal(secret, fixture.derived_signing_secret);
    assert.doesNotThrow(() => JSON.parse(item.raw_body));
    assert.equal(signature(item), item.signature);
  });
}
test('reserializing a received body cannot preserve its wire signature', () => {
  const item = fixture.cases.find((item) => item.name === 'python-json');
  assert.notEqual(signature(item, JSON.stringify(JSON.parse(item.raw_body))), item.signature);
});
