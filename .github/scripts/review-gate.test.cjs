const test = require('node:test');
const assert = require('node:assert/strict');
const { assess } = require('./review-gate.cjs');
const head = 'a'.repeat(40);
const fixed = 'b'.repeat(40);
const reviewer = 'chatgpt-codex-connector';
const baseline = () => ({ head, reviewer, protectedDefinitions: {'.github/scripts/review-gate.cjs': true, '.github/workflows/review-gate.yml': true}, trustedWorkflows: {CI: {id: 1, definitionMatches: true, path: '.github/workflows/ci.yml'}, Security: {id: 2, definitionMatches: true, path: '.github/workflows/security.yml'}}, commits: [head, fixed], runs: ['CI', 'Security'].map((name, index) => ({name, workflow_id: index + 1, path: `.github/workflows/${name === 'CI' ? 'ci' : 'security'}.yml`, head_sha: head, event: 'pull_request', id: 1, status: 'completed', conclusion: 'success'})), reviews: [{ user: { login: reviewer }, commit_id: head, state: 'COMMENTED', submitted_at: '2026-02-01T00:00:00Z' }], comments: [], threads: [] });
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
  input.threads[0].comments.nodes = [{ body: 'Finding', createdAt: '2026-01-01T00:00:00Z' }, { createdAt: '2026-01-02T00:00:00Z', author: { login: 'maintainer' }, body: `Fixed in ${fixed.slice(0, 7)}; regression tests pass.` }];
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
      repos: {get: async () => ({data: {default_branch: 'main'}}),
        getContent: async () => ({data: {type: 'file', sha: fixed}})},
      actions: {getWorkflow: async ({workflow_id}) => ({data: {id: workflow_id === 'ci.yml' ? 1 : 2}}), listWorkflowRunsForRepo: async () => ({data: {workflow_runs: baseline().runs}})},
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

test('PR-controlled workflow names cannot substitute for trusted checks', () => {
  const input = baseline(); input.runs[0].conclusion = 'failure';
  input.runs.push({...input.runs[0], id: 999, workflow_id: 999, path: '.github/workflows/impostor.yml', conclusion: 'success'});
  assert.equal(assess(input).length, 1);
  input.runs[0].conclusion = 'success'; input.runs[0].path = '.github/workflows/impostor.yml';
  assert.equal(assess(input).length, 1);
  input.runs[0].path = '.github/workflows/ci.yml';
  assert.deepEqual(assess(input), []);
});


test('ref-qualified workflow paths retain trusted identity checks', () => {
  for (const ref of ['main', 'refs/pull/123/merge', 'feature/nested']) {
    const input = baseline();
    input.runs.forEach(run => { run.path += `@${ref}`; });
    assert.deepEqual(assess(input), []);
    input.runs[0].workflow_id = 999;
    assert.equal(assess(input).length, 1);
    input.runs[0].workflow_id = 1;
    input.runs[0].path = `.github/workflows/impostor.yml@${ref}`;
    assert.equal(assess(input).length, 1);
  }
});

test('changed trusted workflow definitions fail even with valid workflow identities', () => {
  for (const name of ['CI', 'Security']) {
    const input = baseline();
    input.trustedWorkflows[name].definitionMatches = false;
    assert.match(assess(input).join(' '), /definition differs/);
  }
  const input = baseline();
  delete input.trustedWorkflows.CI.definitionMatches;
  assert.match(assess(input).join(' '), /definition differs/);
});

test('later reviewer feedback requires a subsequent fixing disposition', () => {
  const input = baseline();
  const nodes = [{author: {login: reviewer}, body: 'Finding', createdAt: '2026-01-01T00:00:00Z'},
    {author: {login: 'maintainer'}, body: `Fixed in ${fixed}; tests pass.`, createdAt: '2026-01-02T00:00:00Z'},
    {author: {login: reviewer}, body: 'The fix remains incomplete.', createdAt: '2026-01-03T00:00:00Z'}];
  input.threads = [{id: 'thread', isResolved: true, resolvedBy: {login: 'maintainer'}, comments: {nodes}}];
  assert.match(assess(input).join(' '), /no fixing-commit/);
  nodes.push({author: {login: 'maintainer'}, body: 'Resolved', createdAt: '2026-01-04T00:00:00Z'});
  assert.equal(assess(input).length, 1);
  nodes.push({author: {login: 'maintainer'}, body: `Fixed in ${head}; regression tests pass.`, createdAt: '2026-01-05T00:00:00Z'});
  assert.deepEqual(assess(input), []);
});


test('the validator and its workflow also require protected definition equality', () => {
  for (const path of Object.keys(baseline().protectedDefinitions)) {
    const input = baseline();
    input.protectedDefinitions[path] = false;
    assert.match(assess(input).join(' '), /Protected review-gate definition differs/);
  }
});

test('edited earlier feedback invalidates older resolver evidence', () => {
  const input = baseline();
  const nodes = [
    {author: {login: reviewer}, body: 'Finding', createdAt: '2026-01-01T00:00:00Z', updatedAt: '2026-01-03T00:00:00Z'},
    {author: {login: 'maintainer'}, body: `Fixed in ${fixed}; tests pass.`, createdAt: '2026-01-02T00:00:00Z'},
  ];
  input.threads = [{id: 'edited-thread', isResolved: true, resolvedBy: {login: 'maintainer'}, comments: {nodes}}];
  assert.match(assess(input).join(' '), /no fixing-commit/);
  nodes.push({author: {login: 'maintainer'}, body: `Fixed in ${head}; regression tests pass.`, createdAt: '2026-01-04T00:00:00Z'});
  assert.deepEqual(assess(input), []);
  nodes[0].updatedAt = 'invalid';
  assert.match(assess(input).join(' '), /no fixing-commit/);
});


test('completed native Codex summaries attest to a unique final-head commit', () => {
  const input = baseline(); input.reviews = [];
  const summary = `<!-- codex-pull-request-review-summary -->\n\n| 📝 **Code Review** | ✅ **Completed** <relative-time datetime="2026-01-01">2026-01-01</relative-time> | \`${head.slice(0, 7)}\` | PR opened |`;
  input.comments = [{user: {login: `${reviewer}[bot]`}, body: summary}];
  assert.deepEqual(assess(input), []);
  input.comments[0].body = summary.replace('Completed', 'In progress');
  assert.equal(assess(input).length, 1);
  input.comments[0].body = summary.replace(head.slice(0, 7), fixed.slice(0, 7));
  assert.equal(assess(input).length, 1);
  input.comments[0].body = summary; input.comments[0].user.login = 'applicant';
  assert.equal(assess(input).length, 1);
  input.comments[0].user.login = `${reviewer}[bot]`; input.commits.push(head.slice(0, 7) + 'c'.repeat(33));
  assert.equal(assess(input).length, 1);
});

test('final review must follow the latest fixing disposition on the same SHA', () => {
  const input = baseline();
  input.threads = [{id: 'thread', isResolved: true, resolvedBy: {login: 'maintainer'}, comments: {nodes: [
    {body: 'Finding', author: {login: reviewer}, createdAt: '2026-01-01T00:00:00Z'},
    {body: `Superseded in ${fixed}; validation passes.`, author: {login: 'maintainer'}, createdAt: '2026-01-02T00:00:00Z'}
  ]}}];
  input.reviews[0].submitted_at = '2026-01-01T01:00:00Z';
  assert.match(assess(input)[0], /after the latest resolver evidence/);
  input.reviews[0].submitted_at = '2026-01-03T00:00:00Z';
  assert.deepEqual(assess(input), []);
  input.reviews = [];
  input.comments = [{user: {login: reviewer}, body: `**Reviewed commit:** \`${head}\``, created_at: '2026-01-01T00:00:00Z'}];
  assert.match(assess(input)[0], /after the latest resolver evidence/);
  input.comments[0].created_at = '2026-01-03T00:00:00Z';
  assert.deepEqual(assess(input), []);
});
