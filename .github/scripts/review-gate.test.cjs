const test = require('node:test');
const assert = require('node:assert/strict');
const { assess } = require('./review-gate.cjs');
const head = 'a'.repeat(40);
const fixed = 'b'.repeat(40);
const reviewer = 'chatgpt-codex-connector';
const baseline = () => ({ head, reviewer, commits: [head, fixed], runs: ['CI', 'Security'].map(name => ({name, head_sha: head, event: 'pull_request', id: 1, status: 'completed', conclusion: 'success'})), reviews: [{ user: { login: reviewer }, commit_id: head, state: 'COMMENTED' }], comments: [], threads: [] });
test('requires completed review of the current head', () => {
  for (const state of ['old', 'dismissed', 'absent']) {
    const input = baseline();
    if (state === 'old') input.reviews[0].commit_id = fixed;
    if (state === 'dismissed') input.reviews[0].state = 'DISMISSED';
    if (state === 'absent') input.reviews = [];
    assert.equal(assess(input).length, 1);
  }
  assert.deepEqual(assess(baseline()), []);
});
test('only the configured reviewer can attest to no findings', () => {
  const input = baseline(); input.reviews = [];
  input.comments = [{ user: { login: 'applicant' }, body: `**Reviewed commit:** \`${head.slice(0, 10)}\`` }];
  assert.equal(assess(input).length, 1);
  input.comments[0].user.login = `${reviewer}[bot]`;
  assert.deepEqual(assess(input), []);
});
test('resolution flags alone cannot satisfy the evidence gate', () => {
  const input = baseline();
  input.threads = [{ id: 'thread', isResolved: false, comments: { nodes: [] } }];
  assert.equal(assess(input).length, 1);
  input.threads[0].isResolved = true;
  assert.equal(assess(input).length, 1);
  input.threads[0].resolvedBy = { login: 'maintainer' };
  input.threads[0].comments.nodes = [{ body: 'Finding' }, { author: { login: 'maintainer' }, body: `Fixed in ${fixed.slice(0, 7)}; regression tests pass.` }];
  assert.deepEqual(assess(input), []);
  input.threads[0].comments.nodes[1].author.login = 'untrusted';
  assert.equal(assess(input).length, 1);
  input.threads[0].comments.nodes[1].author.login = 'maintainer';
  input.threads[0].comments.nodes[1].body = `Fixed in ${'c'.repeat(7)}; tests pass.`;
  assert.equal(assess(input).length, 1);
});

test('pending or failed final-head checks cannot pass the merge gate', () => {
  for (const state of ['queued', 'failure', 'old-head']) {
    const input = baseline();
    if (state === 'queued') input.runs[0].status = 'queued';
    if (state === 'failure') input.runs[0].conclusion = 'failure';
    if (state === 'old-head') input.runs[0].head_sha = fixed;
    assert.equal(assess(input).length, 1);
  }
  const input = baseline();
  input.runs.push({...input.runs[0], id: 2, status: 'queued'});
  assert.equal(assess(input).length, 1);
});
test('a head change during validation fails the check for the inspected SHA', async () => {
  const { run } = require('./review-gate.cjs');
  let reads = 0;
  let published;
  const listReviews = () => {};
  const listComments = () => {};
  const listCommits = () => {};
  const github = {
    rest: {
      pulls: { get: async () => ({data: {state: 'open', head: {sha: ++reads === 1 ? head : fixed}}}), listReviews, listCommits },
      issues: {listComments},
      actions: {listWorkflowRunsForRepo: async () => ({data: {workflow_runs: baseline().runs}})},
      checks: {create: async input => {published = input;}}
    },
    paginate: async method => method === listReviews ? baseline().reviews : method === listCommits ? [{sha: head}] : [],
    graphql: async () => ({repository: {pullRequest: {reviewThreads: {nodes: [], pageInfo: {hasNextPage: false}}}}})
  };
  await assert.rejects(run({github, context: {repo: {owner: 'synthetic', repo: 'test'}, payload: {pull_request: {number: 1}}}}), /head moved/);
  assert.equal(published.head_sha, head);
  assert.equal(published.conclusion, 'failure');
});

test('blocking final-head review cannot be bypassed by a bot comment', () => {
  for (const state of ['CHANGES_REQUESTED', 'PENDING']) {
    const input = baseline(); input.reviews[0].state = state;
    input.comments = [{user: {login: reviewer}, body: `**Reviewed commit:** \`${head.slice(0, 10)}\``}];
    assert.equal(assess(input).length, 1);
  }
});

test('comments do not clear change requests; approval or dismissal does', () => {
  const input = baseline();
  input.reviews = [{user: {login: reviewer}, commit_id: head, state: 'CHANGES_REQUESTED'}, ...input.reviews];
  assert.equal(assess(input).length, 1);
  input.reviews.push({user: {login: reviewer}, commit_id: head, state: 'APPROVED'});
  assert.deepEqual(assess(input), []);
  input.reviews.pop(); input.reviews[0].state = 'DISMISSED';
  assert.deepEqual(assess(input), []);
  input.reviews[0].state = 'CHANGES_REQUESTED'; input.reviews[0].commit_id = fixed;
  assert.equal(assess(input).length, 1);
});
