function mockGuardAPI(original) {
  let guard;
  return async (suffix, field, options) => {
    if (suffix === 'rulesets' && options?.method === 'POST') return guard = {...options.body, id: 999};
    if (suffix === 'rulesets/999') {if (options?.method === 'DELETE') {guard = undefined; return;} return guard;}
    return original(suffix, field, options);
  };
}
const test = require('node:test');
const assert = require('node:assert/strict');
const { assess } = require('./review-gate.cjs');
const head = 'a'.repeat(40);
const fixed = 'b'.repeat(40);
const reviewer = 'chatgpt-codex-connector';
const baseline = () => ({ pullNumber: 1, baseRef: 'main', head, reviewer, resolver: 'maintainer', protectedDefinitions: {'.github/scripts/review-gate.cjs': true, '.github/workflows/review-gate.yml': true, '.github/workflows/review-evidence-signal.yml': true, '.github/scripts/merge-reviewed-pr.cjs': true, '.github/review-gate-policy.json': true}, trustedWorkflows: {CI: {id: 1, definitionMatches: true, path: '.github/workflows/ci.yml'}, Security: {id: 2, definitionMatches: true, path: '.github/workflows/security.yml'}}, commits: [head, fixed], runs: ['CI', 'Security'].map((name, index) => ({name, workflow_id: index + 1, path: `.github/workflows/${name === 'CI' ? 'ci' : 'security'}.yml`, head_sha: head, event: 'pull_request', pull_requests: [{number: 1, base: {ref: 'main'}, head: {sha: head}}], id: 1, status: 'completed', conclusion: 'success'})), reviews: [{ user: { login: reviewer }, commit_id: head, state: 'COMMENTED', submitted_at: '2026-02-01T00:00:00Z' }], comments: [], threads: [] });
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
  let started;
  const listReviews = () => {};
  const listComments = () => {};
  const listCommits = () => {};
  const github = {
    rest: {
      pulls: { get: async () => ({data: {state: 'open', head: {sha: ++reads === 1 ? head : fixed}}}), listReviews },
      issues: {listComments},
      repos: {listCommits, get: async () => ({data: {default_branch: 'main'}}),
        getContent: async () => ({data: {type: 'file', sha: fixed}})},
      actions: {getWorkflow: async ({workflow_id}) => ({data: {id: workflow_id === 'ci.yml' ? 1 : 2}}), listWorkflowRuns: async () => ({data: {workflow_runs: baseline().runs}})},
      checks: {
        create: async input => { started = input; return {data: {id: 42}}; },
        update: async input => { published = input; }
      }
    },
    paginate: async method => {
      assert.equal(started.status, 'in_progress');
      return method === listReviews ? baseline().reviews : method === listCommits ? [{sha: head}] : [];
    },
    graphql: async () => ({repository: {pullRequest: {reviewThreads: {nodes: [], pageInfo: {hasNextPage: false}}}, ...Object.fromEntries(Array.from({length: 7}, (_, i) => [[`trusted${i}`, {__typename: 'Blob', oid: fixed}], [`proposed${i}`, {__typename: 'Blob', oid: fixed}]]).flat())}})
  };
  await assert.rejects(run({github, context: {repo: {owner: 'synthetic', repo: 'test'}, payload: {pull_request: {number: 1}}}}), /head moved/);
  assert.equal(started.head_sha, head);
  assert.equal(started.status, 'in_progress');
  assert.equal(published.check_run_id, 42);
  assert.equal(published.conclusion, 'failure');
  let reviewReads = 0;
  github.rest.pulls.get = async () => ({data: {state: 'open', head: {sha: head}}});
  github.paginate = async method => method === listReviews
    ? (++reviewReads === 1 ? baseline().reviews : [{...baseline().reviews[0], state: 'CHANGES_REQUESTED'}])
    : method === listCommits ? [{sha: head}] : [];
  await assert.rejects(run({github, context: {repo: {owner: 'synthetic', repo: 'test'}, payload: {pull_request: {number: 1}}}}), /evidence changed/);
  assert.equal(published.conclusion, 'failure');
  github.paginate = async method => method === listReviews ? baseline().reviews
    : method === listCommits ? [{sha: head}] : [];
  for (const state of ['queued', 'in_progress', 'failure']) {
    let runReads = 0;
    github.rest.actions.listWorkflowRuns = async () => {
      const runs = baseline().runs;
      if (++runReads > 2) {
        runs[0].status = state === 'failure' ? 'completed' : state;
        runs[0].conclusion = state === 'failure' ? 'failure' : null;
        runs[0].run_attempt = 2;
      }
      return {data: {workflow_runs: runs}};
    };
    await assert.rejects(run({github, context: {repo: {owner: 'synthetic', repo: 'test'}, payload: {pull_request: {number: 1}}}}), /CI/);
    assert.equal(runReads, 4);
    assert.equal(published.conclusion, 'failure');
  }
  reads = 0;
  started = undefined;
  github.paginate = async () => {
    assert.equal(started.status, 'in_progress');
    throw new Error('Synthetic evidence API failure');
  };
  await assert.rejects(run({github, context: {repo: {owner: 'synthetic', repo: 'test'}, payload: {pull_request: {number: 1}}}}), /Synthetic evidence API failure/);
  assert.equal(published.check_run_id, 42);
  assert.equal(published.status, 'completed');
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

test('resolver evidence edits require a later final-head review', () => {
  const input = baseline();
  input.threads = [{id: 'edited-evidence', isResolved: true, resolvedBy: {login: 'maintainer'}, comments: {nodes: [
    {author: {login: reviewer}, body: 'Finding', createdAt: '2026-01-01T00:00:00Z'},
    {author: {login: 'maintainer'}, body: `Inapplicable in ${fixed}; validation passes.`, createdAt: '2026-01-02T00:00:00Z', updatedAt: '2026-03-01T00:00:00Z'},
  ]}}];
  assert.match(assess(input).join(' '), /after the latest resolver evidence/);
  input.reviews[0].submitted_at = '2026-03-02T00:00:00Z';
  assert.deepEqual(assess(input), []);
  input.threads[0].comments.nodes[1].updatedAt = 'invalid';
  assert.match(assess(input).join(' '), /no fixing-commit/);
});

test('latest resolver disposition must still attest to a tested fixing commit', () => {
  const input = baseline();
  const nodes = [
    {author: {login: reviewer}, body: 'Finding', createdAt: '2026-01-01T00:00:00Z'},
    {author: {login: 'maintainer'}, body: `Fixed in ${fixed}; tests pass.`, createdAt: '2026-01-02T00:00:00Z'},
    {author: {login: 'maintainer'}, body: 'The fix is still incomplete.', createdAt: '2026-01-03T00:00:00Z', updatedAt: '2026-02-02T00:00:00Z'}
  ];
  input.threads = [{id: 'retracted', isResolved: true, resolvedBy: {login: 'maintainer'}, comments: {nodes}}];
  assert.match(assess(input).join(' '), /no fixing-commit and validation evidence/);
  nodes[2].body = `Fixed in ${fixed}; regression tests pass.`;
  assert.match(assess(input).join(' '), /after the latest resolver evidence/);
  input.reviews[0].submitted_at = '2026-02-03T00:00:00Z';
  assert.deepEqual(assess(input), []);
  nodes[2].updatedAt = 'invalid';
  assert.match(assess(input).join(' '), /no fixing-commit and validation evidence/);
});

test('bulk discovery never publishes checks outside the per-PR lock', async () => {
  const { preparePullRequests } = require('./review-gate.cjs');
  const github = {
    rest: {pulls: {list: Symbol('list'), get: async () => ({data: {state: 'open'}})},
      checks: {create: async () => assert.fail('discovery must not publish checks')}},
    paginate: async () => [{number: 11}, {number: 12}]
  };
  const context = {eventName: 'push', repo: {owner: 'synthetic', repo: 'test'}, payload: {}};
  assert.deepEqual(await preparePullRequests({github, context}), [{number: 11}, {number: 12}]);
  github.rest.pulls.get = async ({pull_number}) => {
    if (pull_number === 11) throw new Error('synthetic discovery failure');
    return {data: {state: 'open'}};
  };
  assert.deepEqual(await preparePullRequests({github, context}), [{number: 11}, {number: 12}]);
});

test('all workflow-associated PRs are discovered and duplicate numbers are removed', async () => {
  const { preparePullRequests } = require('./review-gate.cjs');
  const github = {rest: {pulls: {get: async ({pull_number}) => ({data: {state: pull_number === 13 ? 'closed' : 'open', head: {sha: head}}})},
    checks: {create: async () => ({data: {id: 1}})}}};
  const targets = await preparePullRequests({github, context: {repo: {owner: 'test', repo: 'test'},
    eventName: 'workflow_run', payload: {workflow_run: {pull_requests: [{number: 11}, {number: 12}, {number: 11}, {number: 13}]}}}});
  assert.deepEqual(targets.map(target => target.number), [11, 12, 13]);
});

test('bulk and individual assessments use the same per-PR concurrency group', () => {
  const workflow = require('node:fs').readFileSync(require('node:path').join(__dirname, '../workflows/review-gate.yml'), 'utf8');
  assert.match(workflow, /group: review-evidence-bucket-\$\{\{ matrix.bucket \}\}/);
  assert.doesNotMatch(workflow, /github.run_id/);
  assert.match(workflow, /needs: discover/);
  assert.match(workflow, /cancel-in-progress: false/);
  assert.doesNotMatch(workflow, /cancel-in-progress: true/);
});

test('assessment reads the current head and creates its own check under the lock', async () => {
  const { run } = require('./review-gate.cjs');
  const updates = [];
  const github = {rest: {pulls: {get: async () => ({data: {state: 'open', head: {sha: fixed}}})},
    checks: {create: async input => { assert.equal(input.head_sha, fixed); return {data: {id: 222}}; },
      update: async update => updates.push(update)}},
    paginate: async () => { throw new Error('synthetic collection failure'); }};
  await assert.rejects(run({github, context: {repo: {owner: 'test', repo: 'test'}, payload: {pull_request: {number: 11}}},
    prepared: {number: 11, head, check_id: 111}}), /synthetic collection failure/);
  assert.equal(updates[0].check_run_id, 222);
  assert.equal(updates[0].conclusion, 'failure');
});

test('publisher credentials are limited to default-branch environment jobs', () => {
  const fs = require('node:fs');
  const path = require('node:path');
  const gate = fs.readFileSync(path.join(__dirname, '../workflows/review-gate.yml'), 'utf8');
  const signal = fs.readFileSync(path.join(__dirname, '../workflows/review-evidence-signal.yml'), 'utf8');
  assert.match(gate, /github.ref == format\('refs\/heads\/\{0\}', github.event.repository.default_branch\)/);
  assert.equal((gate.match(/environment: review-evidence-publisher/g) || []).length, 2);
  assert.equal((gate.match(/github-token: \$\{\{ steps.publisher.outputs.token \}\}/g) || []).length, 2);
  assert.equal((gate.match(/permission-checks: write/g) || []).length, 2);
  assert.doesNotMatch(gate, /^  checks: write$/m);
  assert.doesNotMatch(signal, /secrets\.|environment:|checkout@|github-token:|checks: write/);
  assert.match(signal, /permissions: \{\}/);
  assert.doesNotMatch(gate, /^  pull_request_review:/m);
  assert.match(gate, /workflows: \[CI, Security, Review evidence signal\]/);
});

for (const workflow of ['CI', 'Security', 'Review evidence signal']) {
  test(`${workflow} without PR association invalidates all open heads`, async () => {
    const { preparePullRequests } = require('./review-gate.cjs');
    const github = {rest: {pulls: {list: Symbol('list'), get: async ({pull_number}) => ({data: {state: 'open', head: {sha: String(pull_number)}}})},
      checks: {create: async () => ({data: {id: 111}})}}, paginate: async () => [{number: 11}, {number: 12}]};
    const targets = await preparePullRequests({github, context: {repo: {owner: 'test', repo: 'test'}, eventName: 'workflow_run',
      payload: {workflow_run: {name: workflow, pull_requests: []}}}});
    assert.deepEqual(targets.map(target => target.number), [11, 12]);
  });
}

test('workflow completion discovery does not require PR association metadata', () => {
  const workflow = require('node:fs').readFileSync(require('node:path').join(__dirname, '../workflows/review-gate.yml'), 'utf8');
  const condition = workflow.split('\n').find(line => line.trimStart().startsWith('if:'));
  assert.doesNotMatch(condition, /workflow_run\.pull_requests|workflow_run\.name/);
  assert.match(condition, /github.ref ==/);
});

test('resolution metadata cannot replace the configured trusted disposition author', () => {
  const input = baseline();
  input.threads = [{id: 'trusted', isResolved: true, resolvedBy: {login: 'maintainer'}, comments: {nodes: [
    {author: {login: reviewer}, body: 'Finding', createdAt: '2026-01-01T00:00:00Z'},
    {author: {login: 'maintainer'}, body: `Fixed in ${fixed}; regression tests pass.`, createdAt: '2026-01-02T00:00:00Z'},
  ]}}];
  assert.deepEqual(assess(input), []);
  input.threads[0].isResolved = false;
  assert.match(assess(input).join(' '), /Unresolved thread/);
  input.threads[0].isResolved = true;
  input.threads[0].resolvedBy = {login: 'untrusted'};
  assert.deepEqual(assess(input), []);
  input.threads[0].comments.nodes[1].author.login = 'untrusted';
  assert.match(assess(input).join(' '), /no fixing-commit and validation evidence/);
  input.threads[0].resolvedBy = {login: 'maintainer'};
  assert.match(assess(input).join(' '), /no fixing-commit and validation evidence/);
});

for (const state of ['queued', 'in_progress', 'failure', 'success']) {
  test(`older workflow rerun with ${state} uses current-attempt activity`, () => {
    const input = baseline();
    input.runs[0] = {...input.runs[0], id: 20, updated_at: '2026-01-02T00:00:00Z'};
    input.runs.push({...input.runs[0], id: 10, run_attempt: 2,
      updated_at: '2026-01-03T00:00:00Z', status: ['queued', 'in_progress'].includes(state) ? state : 'completed',
      conclusion: ['queued', 'in_progress'].includes(state) ? null : state});
    assert.equal(assess(input).length, state === 'success' ? 0 : 1);
    if (state === 'in_progress') {
      input.runs[0].updated_at = '2026-01-04T00:00:00Z';
      assert.equal(assess(input).length, 1);
    }
  });
}

test('both evidence snapshots paginate beyond the first workflow-run page', async () => {
  const { fetchWorkflowRuns } = require('./review-gate.cjs');
  const pages = [];
  const github = {rest: {actions: {listWorkflowRuns: async ({page, per_page, head_sha, event}) => {
    if (event === 'push') return {data: {workflow_runs: []}};
    pages.push(page); assert.equal(per_page, 100); assert.equal(head_sha, head);
    return {data: {workflow_runs: page === 1 ? Array.from({length: 100}, (_, id) => ({id, name: 'Signal'})) : baseline().runs}};
  }}}};
  for (let snapshot = 0; snapshot < 2; snapshot++) {
    const {data} = await fetchWorkflowRuns({github, owner: 'test', repo: 'test', head, workflows: [{id: 1}]});
    assert.equal(data.workflow_runs.length, 102);
    assert.deepEqual(data.workflow_runs.slice(100), baseline().runs);
  }
  assert.deepEqual(pages, [1, 2, 1, 2]);
});

test('arbitrarily large discovery stays within eight stable concurrency buckets', () => {
  const { bucketTargets } = require('./review-gate.cjs');
  const targets = Array.from({length: 1025}, (_, index) => ({number: index + 1}));
  const buckets = bucketTargets(targets);
  assert.equal(buckets.length, 8);
  assert.deepEqual(buckets, Array.from({length: 8}, (_, index) => index));
  assert.deepEqual(bucketTargets([{number: 11}, {number: 267}]), [3]);
});

test('a replacement bucket job refreshes every open PR sharing its lock', async () => {
  const { runBucket } = require('./review-gate.cjs');
  const visited = [];
  const github = {rest: {pulls: {list: Symbol('list'), get: async ({pull_number}) => {
    visited.push(pull_number); return {data: {state: 'closed'}};
  }}}, paginate: async () => [{number: 11}, {number: 267}, {number: 12}]};
  await runBucket({github, context: {repo: {owner: 'test', repo: 'test'}}, bucket: 3});
  assert.deepEqual(visited, [11, 267]);
  await assert.rejects(runBucket({github, context: {repo: {owner: 'test', repo: 'test'}}, bucket: 256}), /Invalid review bucket/);
});

test('embedded discovery and bucket scripts execute their configured entry points', async () => {
  const fs = require('node:fs');
  const path = require('node:path');
  const lines = fs.readFileSync(path.join(__dirname, '../workflows/review-gate.yml'), 'utf8').split('\n');
  const scripts = [];
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() !== 'script: |') continue;
    const body = [];
    while (++i < lines.length && (lines[i].startsWith('            ') || !lines[i].trim())) body.push(lines[i].slice(12));
    i--; scripts.push(body.join('\n'));
  }
  assert.equal(scripts.length, 2);
  const {bucketTargets} = require('./review-gate.cjs');
  const calls = [];
  const exports = {preparePullRequests: async () => [{number: 11}, {number: 267}, {number: 12}], bucketTargets,
    runBucket: async args => calls.push(args)};
  const loader = name => name === 'node:fs' ? {existsSync: () => true} : exports;
  const output = {};
  const core = {setOutput: (key, value) => {output[key] = value;}};
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
  const context = {repo: {owner: 'test', repo: 'test'}};
  for (const script of scripts) await new AsyncFunction('require', 'github', 'context', 'core', 'process', script)(loader, {}, context, core, {env: {REVIEW_BUCKET: '3'}});
  assert.deepEqual(JSON.parse(output.targets), [3, 4]);
  assert.equal(calls.length, 1); assert.equal(calls[0].bucket, 3); assert.equal(calls[0].context, context);
});

for (const body of ['tests fail', 'validation did not pass', 'tests not passed', 'validation unsuccessful', 'tests failed but passed earlier']) {
  test(`negative validation statement is rejected: ${body}`, () => {
    const {affirmativeValidation} = require('./review-gate.cjs');
    assert.equal(affirmativeValidation(`Fixed in ${fixed}; ${body}.`), false);
  });
}
test('affirmative validation requires a result, not a subject word', () => {
  const {affirmativeValidation} = require('./review-gate.cjs');
  assert.equal(affirmativeValidation('Tests pending.'), false);
  assert.equal(affirmativeValidation('All 35 regression tests passed.'), true);
  assert.equal(affirmativeValidation('Validation passes.'), true);
});
test('unrelated issue comments and formal reviews cannot change evidence snapshots', () => {
  const {relevantComments, relevantReviews} = require('./review-gate.cjs');
  const trusted = {user: {login: `${reviewer}[bot]`}, body: 'Summary'};
  assert.deepEqual(relevantComments([trusted, {user: {login: 'outsider'}, body: 'Churn'}]), [trusted]);
  assert.deepEqual(relevantComments([trusted, {user: {login: 'outsider'}, body: 'Edited churn'}]), [trusted]);
  assert.deepEqual(relevantReviews([trusted, {user: {login: 'outsider'}, state: 'COMMENTED'}]), [trusted]);
});
test('ancestry comparison verifies evidence beyond 250 PR commits without listing history', async () => {
  const {fetchCommitEvidence} = require('./review-gate.cjs');
  const github = {rest: {repos: {compareCommitsWithBasehead: async ({basehead}) => {
    assert.equal(basehead, `${fixed.slice(0, 7)}...${head}`);
    return {data: {status: 'ahead', ahead_by: 300, base_commit: {sha: fixed}, merge_base_commit: {sha: fixed}}};
  }}}};
  const evidence = await fetchCommitEvidence({github, owner: 'test', repo: 'test', head, resolver: 'maintainer', threads: [],
    comments: [{body: `Validation passed for ${fixed.slice(0, 7)}.`}]});
  assert.deepEqual(evidence.commits, [head, fixed]); assert.equal(evidence.commitProof[fixed.slice(0, 7)], fixed);
});
test('ambiguous abbreviations and non-ancestor commits cannot be evidence', async () => {
  const {fetchCommitEvidence} = require('./review-gate.cjs');
  const github = {rest: {repos: {compareCommitsWithBasehead: async ({basehead}) => {
    if (basehead.startsWith('ccccccc')) throw Object.assign(new Error('ambiguous'), {status: 422});
    return {data: {status: 'diverged', base_commit: {sha: fixed}, merge_base_commit: {sha: 'd'.repeat(40)}}};
  }}}};
  const evidence = await fetchCommitEvidence({github, owner: 'test', repo: 'test', head, resolver: 'maintainer', threads: [],
    comments: [{body: `Validation passed for ccccccc and ${fixed.slice(0, 7)}.`}]});
  assert.deepEqual(evidence.commits, [head]);
  assert.equal(evidence.commitProof.ccccccc, undefined);
  const input = baseline(); input.reviews = []; input.commits = [head]; input.commitProof = evidence.commitProof;
  input.comments = [{user: {login: reviewer}, body: `**Reviewed commit:** \`${head.slice(0, 10)}\``}];
  assert.match(assess(input).join(' '), /Configured review/);
});

test('trusted workflow searches are separate from unrelated repository runs', async () => {
  const {fetchWorkflowRuns} = require('./review-gate.cjs');
  const requested = [];
  const github = {rest: {actions: {listWorkflowRuns: async ({workflow_id, event}) => {
    requested.push([workflow_id, event]); return {data: {workflow_runs: baseline().runs.filter(run => run.workflow_id === workflow_id && run.event === event)}};
  }}}};
  const {data} = await fetchWorkflowRuns({github, owner: 'test', repo: 'test', head, workflows: [{id: 1}, {id: 2}]});
  assert.deepEqual(requested, [[1, 'pull_request'], [1, 'push'], [2, 'pull_request'], [2, 'push']]); assert.deepEqual(data.workflow_runs, baseline().runs);
});

for (const fork of [false, true]) test(`bulk validation of 257 ${fork ? 'fork' : 'associated'} PRs stays below the installation REST budget`, async () => {
  const {preparePullRequests, bucketTargets, runBucket} = require('./review-gate.cjs');
  let requests = 0; let currentNumber = 1;
  const prs = Array.from({length: 257}, (_, i) => ({number: i + 1}));
  const methods = {list: Symbol('list'), reviews: Symbol('reviews'), comments: Symbol('comments'), commits: Symbol('commits')};
  const github = {rest: {
    pulls: {list: methods.list, listReviews: methods.reviews, get: async ({pull_number}) => {currentNumber = pull_number; requests++; return {data: {state: 'open', head: {sha: head}}};}},
    issues: {listComments: methods.comments},
    repos: {compareCommitsWithBasehead: async ({basehead}) => {requests++; const sha = basehead.startsWith(head.slice(0, 10)) ? head : fixed; return {data: {status: sha === head ? 'identical' : 'ahead', base_commit: {sha}, merge_base_commit: {sha}}};}, listCommits: methods.commits, get: async () => {requests++; return {data: {default_branch: 'main'}};}},
    actions: {getWorkflow: async ({workflow_id}) => {requests++; return {data: {id: workflow_id === 'ci.yml' ? 1 : 2}};},
      downloadWorkflowRunAttemptLogs: async ({run_id}) => {requests++; const number = Math.floor(run_id / 10); const label = run_id % 10 === 1 ? 'CI' : 'Security'; return {data: proofArchive({number, head, base: 'main', run_id, run_attempt: 1}, {label})};},
      listWorkflowRuns: async ({workflow_id, event}) => {requests++; return {data: {workflow_runs: baseline().runs.filter(run => run.workflow_id === workflow_id && run.event === event).map(run => ({...run, id: currentNumber * 10 + workflow_id, run_attempt: 1, pull_requests: fork ? [] : [{number: currentNumber, base: {ref: 'main'}, head: {sha: head}}]}))}};}},
    checks: {create: async () => {requests++; return {data: {id: 42}};}, update: async () => {requests++;}}
  }, paginate: async (method, params) => {
    if (params.pull_number) currentNumber = params.pull_number;
    requests += method === methods.list ? 3 : 1;
    if (method === methods.list) return prs;
    if (method === methods.reviews) return baseline().reviews;
    if (method === methods.comments) return [{user: {login: reviewer}, body: `**Reviewed commit:** \`${head.slice(0, 10)}\``}];
    if (method === methods.commits) return [{sha: head}];
    assert.fail('Unexpected pagination');
  }, graphql: async () => ({repository: {pullRequest: {reviewThreads: {nodes: [], pageInfo: {hasNextPage: false}}},
    ...Object.fromEntries(Array.from({length: 7}, (_, i) => [[`trusted${i}`, {__typename: 'Blob', oid: fixed}], [`proposed${i}`, {__typename: 'Blob', oid: fixed}]]).flat())}})};
  const context = {repo: {owner: 'test', repo: 'test'}, eventName: 'push', payload: {}};
  const targets = await preparePullRequests({github, context});
  const buckets = bucketTargets(targets); assert.equal(buckets.length, 8);
  for (const bucket of buckets) await runBucket({github: {...github}, context, bucket});
  assert.ok(requests < 5000, `${requests} requests exceed the installation budget`);
});

const mergerPolicy = require('../review-gate-policy.json');
const nativePolicy = () => ({policy: mergerPolicy, repository: {permissions: {admin: true}},
  protection: {enforce_admins: {enabled: true}, required_conversation_resolution: {enabled: true}, required_status_checks: {strict: true, checks: [{context: 'review-evidence', app_id: mergerPolicy.publisher_app_id}, ...mergerPolicy.required_ci_checks.map(check => ({...check}))]}},
  ruleset: {target: 'branch', enforcement: 'active', conditions: {ref_name: {include: ['refs/heads/main'], exclude: []}}, rules: [{type: 'update'}],
    bypass_actors: [{actor_type: 'RepositoryRole', actor_id: 5, bypass_mode: 'pull_request'}]}});

test('trusted merger requires native administrator-only PR update restriction', () => {
  const {assertTrustedPolicy} = require('./merge-reviewed-pr.cjs');
  assert.doesNotThrow(() => assertTrustedPolicy(nativePolicy()));
  for (const mutation of [input => {input.repository.permissions.admin = false;}, input => {input.protection.enforce_admins.enabled = false;},
    input => {input.protection.required_conversation_resolution.enabled = false;}, input => {input.protection.required_status_checks.checks[0].app_id = 15368;},
    input => {input.ruleset.bypass_actors.push({actor_type: 'RepositoryRole', actor_id: 3, bypass_mode: 'pull_request'});},
    input => {input.ruleset.bypass_actors[0].bypass_mode = 'always';}, input => {input.ruleset.enforcement = 'disabled';}]) {
    const input = nativePolicy(); mutation(input); assert.throws(() => assertTrustedPolicy(input));
  }
});
test('a same-named Actions check cannot satisfy the trusted merger', () => {
  const {assertAppCheck} = require('./merge-reviewed-pr.cjs');
  const genuine = {id: 1, name: 'review-evidence', app: {id: mergerPolicy.publisher_app_id}, status: 'completed', conclusion: 'success'};
  const spoof = {...genuine, id: 10, app: {id: 15368}};
  assert.throws(() => assertAppCheck([spoof], mergerPolicy.publisher_app_id));
  assert.doesNotThrow(() => assertAppCheck([genuine, spoof], mergerPolicy.publisher_app_id));
  assert.throws(() => assertAppCheck([genuine, {...genuine, id: 11, status: 'in_progress', conclusion: null}], mergerPolicy.publisher_app_id));
});
test('trusted merger rejects queued failed or missing final-head CI', () => {
  const {assertCI} = require('./merge-reviewed-pr.cjs');
  const workflows = baseline().trustedWorkflows;
  assert.doesNotThrow(() => assertCI(baseline().runs, workflows, head));
  for (const state of ['queued', 'failure']) {
    const runs = baseline().runs; runs[0] = {...runs[0], status: state === 'queued' ? state : 'completed', conclusion: state};
    assert.throws(() => assertCI(runs, workflows, head));
  }
  assert.throws(() => assertCI([], workflows, head));
});
test('cached success cannot skip live pre-merge assessment', async () => {
  const {mergeReviewedPR} = require('./merge-reviewed-pr.cjs');
  const input = nativePolicy(); let merged = false;
  const github = {rest: {repos: {get: async () => ({data: input.repository})}, pulls: {get: async () => ({data: {state: 'open', base: {ref: 'main'}, head: {sha: head}}})}}};
  const api = mockGuardAPI(async suffix => suffix.includes('protection') ? input.protection : suffix.includes('rulesets') ? input.ruleset
    : [{id: 1, name: 'review-evidence', app: {id: mergerPolicy.publisher_app_id}, status: 'completed', conclusion: 'success'}]);
  await assert.rejects(mergeReviewedPR({github, context: {repo: {owner: 'test', repo: 'test'}}, number: 1, api, policy: mergerPolicy,
    validate: async () => {throw new Error('Evidence was edited after cached success');}, merge: async () => {merged = true;}}), /Evidence was edited/);
  assert.equal(merged, false);
});

test('mixed failed and passed validation statements remain blocking', () => {
  const {affirmativeValidation} = require('./review-gate.cjs');
  assert.equal(affirmativeValidation('Tests failed. Other regression tests passed.'), false);
  assert.equal(affirmativeValidation('Validation did not pass. Unit tests passed.'), false);
});

test('gh adapter resolves commit ancestry using the comparison endpoint', async () => {
  const {createGhAdapter} = require('./merge-reviewed-pr.cjs');
  const calls = [];
  const {github} = createGhAdapter('test/project', args => {calls.push(args); return {status: 'ahead'};});
  await github.rest.repos.compareCommitsWithBasehead({basehead: `${fixed}...${head}`});
  assert.deepEqual(calls, [['api', `repos/test/project/compare/${fixed}...${head}`]]);
});

for (const moved of [false, true]) {
  test(`live merger ${moved ? 'rejects a moved head' : 'validates before merging the exact head'}`, async () => {
    const {mergeReviewedPR} = require('./merge-reviewed-pr.cjs');
    const input = nativePolicy(); let reads = 0; let validated = false; let merged = null;
    const github = {rest: {
      repos: {get: async () => ({data: input.repository})},
      pulls: {get: async () => ({data: {state: 'open', base: {ref: 'main'}, head: {sha: ++reads > 1 && moved ? fixed : head}}})},
      actions: {getWorkflow: async ({workflow_id}) => ({data: {id: workflow_id === 'ci.yml' ? 1 : 2}}),
        listWorkflowRuns: async ({workflow_id}) => ({data: {workflow_runs: baseline().runs.filter(run => run.workflow_id === workflow_id)}})}
    }};
    const api = mockGuardAPI(async suffix => suffix.includes('protection') ? input.protection : suffix.includes('rulesets') ? input.ruleset
      : [{id: 1, name: 'review-evidence', app: {id: mergerPolicy.publisher_app_id}, status: 'completed', conclusion: 'success'}]);
    const operation = mergeReviewedPR({github, context: {repo: {owner: 'test', repo: 'test'}}, number: 1, api, policy: mergerPolicy,
      validate: async ({github: live}) => {validated = true; await live.rest.checks.update({conclusion: 'success'});},
      merge: async sha => {assert.equal(validated, true); merged = sha;}});
    if (moved) {await assert.rejects(operation, /head moved/); assert.equal(merged, null);}
    else {assert.equal(await operation, head); assert.equal(merged, head);}
  });
}


test('gh adapter repository lookup omits a trailing slash', async () => {
  const {createGhAdapter} = require('./merge-reviewed-pr.cjs');
  const calls = [];
  const {github} = createGhAdapter('test/project', args => {calls.push(args); return {permissions: {admin: true}};});
  await github.rest.repos.get({owner: 'test', repo: 'project'});
  assert.deepEqual(calls, [['api', 'repos/test/project']]);
});

for (const negative of ["tests weren't successful", "Tests aren't successful", "Validation couldn’t pass", "Tests haven’t passed", "Tests won't pass"]) {
  test(`contracted negative validation is rejected: ${negative}`, () => {
    const {affirmativeValidation} = require('./review-gate.cjs');
    assert.equal(affirmativeValidation(negative), false);
    assert.equal(affirmativeValidation(`${negative}. Other tests passed.`), false);
  });
}
test('live CI excludes superseded failures and unrelated events', () => {
  const {assertCI} = require('./merge-reviewed-pr.cjs');
  const workflows = baseline().trustedWorkflows;
  const runs = baseline().runs.map(run => ({...run, id: 20, updated_at: '2026-10-07T02:00:00Z'}));
  runs.push({...runs[0], id: 10, conclusion: 'cancelled', updated_at: '2026-10-07T01:00:00Z'},
    {...runs[1], id: 99, event: 'workflow_dispatch', conclusion: 'failure'});
  assert.doesNotThrow(() => assertCI(runs, workflows, head));
  runs.push({...runs[0], id: 21, conclusion: 'failure', updated_at: '2026-10-07T03:00:00Z'});
  assert.throws(() => assertCI(runs, workflows, head));
});
test('live CI verifies workflow paths head and any present push run', () => {
  const {assertCI} = require('./merge-reviewed-pr.cjs');
  const workflows = baseline().trustedWorkflows;
  for (const mutation of [runs => {runs[0].path = 'spoof.yml';}, runs => {runs[0].head_sha = fixed;},
    runs => {runs.push({...runs[0], event: 'push', conclusion: 'failure'});},
    runs => {runs.push({...runs[0], id: 0, status: 'queued', conclusion: null});}]) {
    const runs = baseline().runs; mutation(runs); assert.throws(() => assertCI(runs, workflows, head));
  }
});

test('protected update approval is exact scoped expiring and based on trusted main', () => {
  const {approvedDefinitionPaths} = require('./review-gate.cjs');
  const now = Date.parse('2026-10-07T00:00:00Z');
  const approval = {base: fixed, expires_at: '2026-10-07T01:00:00Z', heads: {[head]: ['.github/scripts/review-gate.cjs']}};
  const check = (value, target = head, base = fixed) => approvedDefinitionPaths({manifest: JSON.stringify(value), head: target, base, now});
  assert.deepEqual([...check(approval)], ['.github/scripts/review-gate.cjs']);
  assert.equal(check(approval, fixed).size, 0);
  assert.equal(check(approval, head, head).size, 0);
  assert.throws(() => check({...approval, expires_at: '2026-10-06T23:00:00Z'}));
  assert.throws(() => check({...approval, expires_at: '2026-10-09T00:00:00Z'}));
  assert.throws(() => check({...approval, heads: {[head]: ['unrelated-file']}}));
});

for (const moved of [false, true]) {
  test(`governed protected update ${moved ? 'rejects a moving base' : 'still requires live review and CI'}`, async () => {
    const {run} = require('./review-gate.cjs');
    const approval = JSON.stringify({base: fixed, expires_at: new Date(Date.now() + 3600000).toISOString(), heads: {[head]: ['.github/scripts/review-gate.cjs']}});
    let reads = 0; let conclusion;
    const methods = {reviews: Symbol(), comments: Symbol()};
    const github = {rest: {
      pulls: {get: async () => ({data: {state: 'open', head: {sha: head}}}), listReviews: methods.reviews},
      issues: {listComments: methods.comments},
      repos: {compareCommitsWithBasehead: async () => ({data: {status: 'ahead', base_commit: {sha: fixed}, merge_base_commit: {sha: fixed}}}), get: async () => ({data: {default_branch: 'main'}}), getBranch: async () => ({data: {commit: {sha: ++reads > 1 && moved ? head : fixed}}})},
      actions: {getWorkflow: async ({workflow_id}) => ({data: {id: workflow_id === 'ci.yml' ? 1 : 2}}),
        listWorkflowRuns: async ({workflow_id}) => ({data: {workflow_runs: baseline().runs.filter(run => run.workflow_id === workflow_id)}})},
      checks: {create: async () => ({data: {id: 1}}), update: async result => {conclusion = result.conclusion;}}
    }, paginate: async method => method === methods.reviews ? baseline().reviews : [],
    graphql: async () => ({repository: {pullRequest: {reviewThreads: {nodes: [], pageInfo: {hasNextPage: false}}},
      ...Object.fromEntries(Array.from({length: 7}, (_, i) => [[`trusted${i}`, {__typename: 'Blob', oid: fixed}], [`proposed${i}`, {__typename: 'Blob', oid: i === 2 ? head : fixed}]]).flat())}})};
    const args = {github, context: {repo: {owner: 'maintainer', repo: 'test'}, payload: {pull_request: {number: 1}}}, approvedUpdates: approval};
    if (moved) {await assert.rejects(run(args), /approval base moved/); assert.equal(conclusion, 'failure');}
    else {await run(args); assert.equal(conclusion, 'success'); await assert.rejects(run({...args, approvedUpdates: ''}), /Protected review-gate definition differs/);}
  });
}

test('evidence edited during other merge preflights is collected again', async () => {
  const {mergeReviewedPR} = require('./merge-reviewed-pr.cjs');
  const input = nativePolicy(); let assessments = 0; let merged = false;
  const github = {rest: {
    repos: {get: async () => ({data: input.repository})},
    pulls: {get: async () => ({data: {state: 'open', base: {ref: 'main'}, head: {sha: head}}})},
    actions: {getWorkflow: async ({workflow_id}) => ({data: {id: workflow_id === 'ci.yml' ? 1 : 2}}),
      listWorkflowRuns: async ({workflow_id}) => ({data: {workflow_runs: baseline().runs.filter(run => run.workflow_id === workflow_id)}})}
  }};
  const api = mockGuardAPI(async suffix => suffix.includes('protection') ? input.protection : suffix.includes('rulesets') ? input.ruleset
    : [{id: 1, name: 'review-evidence', app: {id: mergerPolicy.publisher_app_id}, status: 'completed', conclusion: 'success'}]);
  await assert.rejects(mergeReviewedPR({github, context: {repo: {owner: 'test', repo: 'test'}}, number: 1, api, policy: mergerPolicy,
    validate: async ({github: live}) => {
      if (++assessments === 2) throw new Error('Mutable evidence edited during preflight');
      await live.rest.checks.update({conclusion: 'success'});
    }, merge: async () => {merged = true;}}), /Mutable evidence edited/);
  assert.equal(assessments, 2); assert.equal(merged, false);
});

for (const negative of ['No tests passed.', 'Zero tests passed.', '0 tests passed.', 'None of the tests passed.', 'Not all tests passed.', 'Some tests passed.', 'Tests would have passed.']) {
  test(`nonaffirmative validation cannot be inferred: ${negative}`, () => {
    const {affirmativeValidation} = require('./review-gate.cjs');
    assert.equal(affirmativeValidation(`Fixed in ${fixed}; ${negative}`), false);
  });
}
test('documented affirmative validation clauses remain accepted', () => {
  const {affirmativeValidation} = require('./review-gate.cjs');
  assert.equal(affirmativeValidation('Validation: all 66 gate regression tests passed.'), true);
  assert.equal(affirmativeValidation('Fixed in abc1234; targeted smoke tests passed.'), true);
});

test('live merger reads the configured resolver from the protected environment', async () => {
  const {mergeReviewedPR} = require('./merge-reviewed-pr.cjs');
  const input = nativePolicy(); const resolvers = [];
  const github = {rest: {
    repos: {get: async () => ({data: input.repository})},
    pulls: {get: async () => ({data: {state: 'open', base: {ref: 'main'}, head: {sha: head}}})},
    actions: {getWorkflow: async ({workflow_id}) => ({data: {id: workflow_id === 'ci.yml' ? 1 : 2}}),
      listWorkflowRuns: async ({workflow_id}) => ({data: {workflow_runs: baseline().runs.filter(run => run.workflow_id === workflow_id)}})}
  }};
  const api = mockGuardAPI(async suffix => suffix.includes('protection') ? input.protection : suffix.includes('rulesets') ? input.ruleset
    : suffix.endsWith('/REVIEW_GATE_RESOLVER_LOGIN') ? {value: 'other-maintainer'}
    : [{id: 1, name: 'review-evidence', app: {id: mergerPolicy.publisher_app_id}, status: 'completed', conclusion: 'success'}]);
  await mergeReviewedPR({github, context: {repo: {owner: 'test', repo: 'test'}}, number: 1, api, policy: mergerPolicy,
    validate: async ({github: live, resolverLogin}) => {resolvers.push(resolverLogin); await live.rest.checks.update({conclusion: 'success'});}});
  assert.deepEqual(resolvers, ['other-maintainer', 'other-maintainer']);
});

for (const status of ['ahead', 'identical', 'diverged', 'behind']) {
  test(`governed definition approval verifies base ancestry: ${status}`, async () => {
    const {verifyApprovedDefinitionPaths} = require('./review-gate.cjs');
    const manifest = JSON.stringify({base: fixed, expires_at: new Date(Date.now() + 3600000).toISOString(), heads: {[head]: ['.github/scripts/review-gate.cjs']}});
    const github = {rest: {repos: {compareCommitsWithBasehead: async ({basehead}) => {
      assert.equal(basehead, `${fixed}...${head}`);
      return {data: {status, base_commit: {sha: fixed}, merge_base_commit: {sha: ['ahead', 'identical'].includes(status) ? fixed : head}}};
    }}}};
    const operation = verifyApprovedDefinitionPaths({github, owner: 'test', repo: 'test', manifest, head, base: fixed});
    if (['ahead', 'identical'].includes(status)) assert.equal((await operation).size, 1);
    else await assert.rejects(operation, /must be an ancestor/);
  });
}
for (const state of ['revoked', 'expired', 'base-moved']) {
  test(`final validation rejects a protected approval that is ${state}`, async () => {
    const {mergeReviewedPR} = require('./merge-reviewed-pr.cjs');
    const input = nativePolicy(); let assessments = 0; let merged = false;
    const approval = {base: fixed, expires_at: new Date(Date.now() + 3600000).toISOString(), heads: {[head]: ['.github/scripts/review-gate.cjs']}};
    const manifest = JSON.stringify(approval);
    const github = {rest: {
      repos: {get: async () => ({data: input.repository}), getBranch: async () => ({data: {commit: {sha: state === 'base-moved' ? head : fixed}}})},
      pulls: {get: async () => ({data: {state: 'open', base: {ref: 'main'}, head: {sha: head}}})},
      actions: {getWorkflow: async ({workflow_id}) => ({data: {id: workflow_id === 'ci.yml' ? 1 : 2}}),
        listWorkflowRuns: async ({workflow_id}) => ({data: {workflow_runs: baseline().runs.filter(run => run.workflow_id === workflow_id)}})}
    }};
    const api = mockGuardAPI(async suffix => suffix.includes('protection') ? input.protection : suffix.includes('rulesets') ? input.ruleset
      : suffix.endsWith('/REVIEW_GATE_APPROVED_UPDATES') ? {value: assessments === 2 && state === 'revoked' ? '' : manifest}
      : [{id: 1, name: 'review-evidence', app: {id: mergerPolicy.publisher_app_id}, status: 'completed', conclusion: 'success'}]);
    const originalNow = Date.now;
    try { await assert.rejects(mergeReviewedPR({github, context: {repo: {owner: 'test', repo: 'test'}}, number: 1, api, policy: mergerPolicy,
      validate: async ({github: live}) => {
        if (++assessments === 2 && state === 'expired') {const parsed = JSON.parse(manifest); Date.now = () => Date.parse(parsed.expires_at) + 1;}
        await live.rest.checks.update({conclusion: 'success'});
      }, merge: async () => {merged = true;}})); } finally {Date.now = originalNow;}
    assert.equal(assessments, 2); assert.equal(merged, false);
  });
}

for (const value of ['tag', undefined]) {
  test(`merger rejects a ruleset target of ${value}`, () => {
    const {assertTrustedPolicy} = require('./merge-reviewed-pr.cjs');
    const input = nativePolicy(); input.ruleset.target = value;
    assert.throws(() => assertTrustedPolicy(input));
  });
}
test('merger requires GitHub to enforce an up-to-date base', () => {
  const {assertTrustedPolicy} = require('./merge-reviewed-pr.cjs');
  const input = nativePolicy(); input.protection.required_status_checks.strict = false;
  assert.throws(() => assertTrustedPolicy(input), /up-to-date base/);
});
for (const wording of ['Tests passed partially', 'Tests passed except integration tests', 'Tests passed, except integration tests', 'Tests passed with exceptions', 'Tests passed when mocked', 'Tests passed for only one case']) {
  test(`validation rejects qualified results: ${wording}`, () => {
    const {affirmativeValidation} = require('./review-gate.cjs');
    assert.equal(affirmativeValidation(wording), false);
  });
}
test('a push CI rerun during final live assessment blocks merging', async () => {
  const {mergeReviewedPR} = require('./merge-reviewed-pr.cjs');
  const input = nativePolicy(); let assessments = 0; let merged = false;
  const github = {rest: {
    repos: {get: async () => ({data: input.repository})},
    pulls: {get: async () => ({data: {state: 'open', base: {ref: 'main'}, head: {sha: head}}})},
    actions: {getWorkflow: async ({workflow_id}) => ({data: {id: workflow_id === 'ci.yml' ? 1 : 2}}),
      listWorkflowRuns: async ({workflow_id}) => ({data: {workflow_runs: [
        ...baseline().runs.filter(run => run.workflow_id === workflow_id),
        ...(assessments === 2 ? [{...baseline().runs[workflow_id - 1], id: 99, event: 'push', status: 'queued', conclusion: null}] : [])]}})}
  }};
  const api = mockGuardAPI(async suffix => suffix.includes('protection') ? input.protection : suffix.includes('rulesets') ? input.ruleset
    : [{id: 1, name: 'review-evidence', app: {id: mergerPolicy.publisher_app_id}, status: 'completed', conclusion: 'success'}]);
  await assert.rejects(mergeReviewedPR({github, context: {repo: {owner: 'test', repo: 'test'}}, number: 1, api, policy: mergerPolicy,
    validate: async ({github: live}) => {assessments++; await live.rest.checks.update({conclusion: 'success'});},
    merge: async () => {merged = true;}}), /no active runs/);
  assert.equal(assessments, 2); assert.equal(merged, false);
});

for (const wording of ['Tests passed. Except integration.', 'Tests passed; except integration', 'Tests passed. But integration failed.', 'Tests passed. Only unit coverage.']) {
  test(`validation rejects negative follow-up clauses: ${wording}`, () => {
    const {affirmativeValidation} = require('./review-gate.cjs');
    assert.equal(affirmativeValidation(wording), false);
  });
}
for (const mutation of [run => {run.pull_requests[0].base.ref = 'dev';}, run => {run.pull_requests[0].number = 2;}, run => {run.pull_requests = [];}]) {
  test('publisher and live merger reject CI from another PR base or missing association', () => {
    const {assertCI} = require('./merge-reviewed-pr.cjs');
    const input = baseline(); mutation(input.runs[0]);
    assert.match(assess(input).join(' '), /CI has not passed/);
    assert.throws(() => assertCI(input.runs, input.trustedWorkflows, head, {number: 1, baseRef: 'main'}));
  });
}
test('gate CI and Security respond to PR base edits', () => {
  const fs = require('node:fs'); const path = require('node:path');
  for (const name of ['review-gate.yml', 'ci.yml', 'security.yml']) {
    const source = fs.readFileSync(path.join(__dirname, '../workflows', name), 'utf8');
    assert.match(source, /pull_request(?:_target)?:\n\s+types: \[[^\]]*edited/);
  }
});

for (const wording of ['Tests passed. Integration failed.', 'Tests passed. The rest failed.', 'Tests passed. Results are unverified.', 'Tests passed; remaining coverage is incomplete.']) {
  test(`separate incomplete result blocks evidence: ${wording}`, () => {
    const {affirmativeValidation} = require('./review-gate.cjs');
    assert.equal(affirmativeValidation(wording), false);
  });
}
test('live merger requires native CI and Security summary source identities', () => {
  const {assertTrustedPolicy} = require('./merge-reviewed-pr.cjs');
  for (const index of [1, 2]) {
    const missing = nativePolicy(); missing.protection.required_status_checks.checks.splice(index, 1);
    assert.throws(() => assertTrustedPolicy(missing), /native required checks/);
    const spoof = nativePolicy(); spoof.protection.required_status_checks.checks[index].app_id = 1;
    assert.throws(() => assertTrustedPolicy(spoof), /native required checks/);
  }
});
for (const [file, job, name] of [['ci.yml', 'required-ci', 'CI required'], ['security.yml', 'required-security', 'Security required']]) {
  test(`${name} includes every workflow job and rejects any nonsuccess result`, () => {
    const fs = require('node:fs'); const path = require('node:path'); const {spawnSync} = require('node:child_process');
    const source = fs.readFileSync(path.join(__dirname, '../workflows', file), 'utf8');
    const allJobs = [...source.split('\njobs:\n')[1].matchAll(/^  ([a-z0-9-]+):$/gm)].map(match => match[1]).filter(value => value !== job);
    const summary = source.slice(source.indexOf(`  ${job}:`));
    const needs = summary.match(/needs: \[([^\]]+)\]/)[1].split(',').map(value => value.trim());
    assert.deepEqual(needs.sort(), allJobs.sort()); assert.match(summary, /always\(\)/);
    assert.ok(summary.includes(`name: ${name}`));
    const program = summary.match(/python - <<'PY'\n([\s\S]*?)\n          PY/)[1].replace(/^          /gm, '');
    for (const result of ['success', 'failure', 'cancelled', 'skipped']) {
      const execution = spawnSync('python3', ['-c', program], {env: {...process.env, WORKFLOW_RESULTS: JSON.stringify({example: {result}})}});
      assert.equal(execution.status === 0, result === 'success');
    }
    const empty = spawnSync('python3', ['-c', program], {env: {...process.env, WORKFLOW_RESULTS: '{}'}});
    assert.notEqual(empty.status, 0);
  });
}

function proofArchive(proof, {label = 'CI', folder, duplicate = false, compressed = true} = {}) {
  const script = `import io,json,sys,zipfile
p=json.loads(sys.argv[1]); out=io.BytesIO()
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED if p['compressed'] else zipfile.ZIP_STORED) as z:
 z.writestr(p['folder']+'/2_Record immutable PR target.txt','2026-10-07T00:00:00Z IDENTITYCORE_PR_TARGET '+json.dumps(p['proof'])+'\\n')
 if p['duplicate']: z.writestr(p['folder']+'/3_Record immutable PR target.txt','IDENTITYCORE_PR_TARGET '+json.dumps(p['proof']))
sys.stdout.buffer.write(out.getvalue())`;
  const result = require('node:child_process').spawnSync('python', ['-c', script, JSON.stringify({proof, folder: folder || `${label} target proof`, duplicate, compressed})]);
  assert.equal(result.status, 0, result.stderr.toString()); return result.stdout;
}
const forkProof = () => ({number: 1, head, base: 'main', head_repo: 'fork/repo', head_branch: 'change', run_id: 44, run_attempt: 2});
const forkRun = () => ({...baseline().runs[0], id: 44, run_attempt: 2, pull_requests: []});
test('fork CI proof binds the immutable event to run attempt and current PR target', () => {
  const {targetReceiptFromArchive, isRunForPR} = require('./review-gate.cjs');
  const run = forkRun(); run.pr_target_receipt = targetReceiptFromArchive(proofArchive(forkProof()), run, baseline().trustedWorkflows.CI);
  assert.equal(isRunForPR(run, {number: 1, baseRef: 'main', head}), true);
  assert.equal(isRunForPR(run, {number: 2, baseRef: 'main', head}), false);
  assert.equal(isRunForPR(run, {number: 1, baseRef: 'dev', head}), false);
  assert.equal(isRunForPR(run, {number: 1, baseRef: 'main', head: fixed}), false);
  const input = baseline(); input.runs[0] = run; assert.deepEqual(assess(input), []);
  assert.doesNotThrow(() => require('./merge-reviewed-pr.cjs').assertCI(input.runs, input.trustedWorkflows, head));
});
for (const options of [{folder: 'frontend'}, {duplicate: true}]) {
  test('a receipt in another job or duplicated proof cannot authorize fork CI', () => {
    const {targetReceiptFromArchive} = require('./review-gate.cjs');
    assert.throws(() => targetReceiptFromArchive(proofArchive(forkProof(), options), forkRun(), baseline().trustedWorkflows.CI));
  });
}
test('fork proof rejects altered run head attempt malformed ZIP and corrupt log', () => {
  const {targetReceiptFromArchive} = require('./review-gate.cjs'); const workflow = baseline().trustedWorkflows.CI;
  for (const change of [{head: fixed}, {run_id: 45}, {run_attempt: 1}]) {
    assert.throws(() => targetReceiptFromArchive(proofArchive({...forkProof(), ...change}), forkRun(), workflow));
  }
  const archive = proofArchive(forkProof(), {compressed: false});
  const location = archive.indexOf(Buffer.from('IDENTITYCORE_PR_TARGET')); archive[location] ^= 1;
  assert.throws(() => targetReceiptFromArchive(archive, forkRun(), workflow), /checksum/);
  assert.throws(() => targetReceiptFromArchive(Buffer.alloc(0), forkRun(), workflow));
  assert.throws(() => targetReceiptFromArchive(Buffer.alloc(100), forkRun(), workflow));
});
test('completed fork run receipts are downloaded once across live snapshots and remote receipts are ignored', async () => {
  const {fetchWorkflowRuns} = require('./review-gate.cjs'); let downloads = 0;
  const archive = proofArchive(forkProof());
  const github = {rest: {actions: {
    listWorkflowRuns: async ({event}) => ({data: {workflow_runs: event === 'pull_request' ? [{...forkRun(), pr_target_receipt: {base: 'spoof'}}] : []}}),
    downloadWorkflowRunAttemptLogs: async () => {downloads++; return {data: archive};}
  }}};
  const args = {github, owner: 'owner', repo: 'repo', head, target: {number: 1, baseRef: 'main', head}, workflows: [baseline().trustedWorkflows.CI]};
  const first = await fetchWorkflowRuns(args); const second = await fetchWorkflowRuns(args);
  assert.equal(downloads, 1); assert.equal(first.data.workflow_runs[0].pr_target_receipt.base, 'main'); assert.deepEqual(first, second);
});
test('an active fork run without association blocks older successful CI proof', () => {
  const input = baseline(); input.runs.push({...forkRun(), status: 'queued', conclusion: null});
  assert.match(assess(input).join(' '), /CI has not passed/);
  assert.throws(() => require('./merge-reviewed-pr.cjs').assertCI(input.runs, input.trustedWorkflows, head), /still active/);
});
test('gh adapter downloads binary logs from the immutable run attempt endpoint', async () => {
  const {createGhAdapter} = require('./merge-reviewed-pr.cjs'); const calls = []; const binary = Buffer.from('zip');
  const {github} = createGhAdapter('owner/repo', () => assert.fail('JSON cannot decode logs'), args => {calls.push(args); return binary;});
  assert.equal((await github.rest.actions.downloadWorkflowRunAttemptLogs({run_id: 44, attempt_number: 2})).data, binary);
  assert.deepEqual(calls, [['api', 'repos/owner/repo/actions/runs/44/attempts/2/logs']]);
});
test('main merge guard applies to every nonmain branch with zero bypass actors and cleans up on merge errors', async () => {
  const {withMainMergeGuard} = require('./merge-reviewed-pr.cjs');
  for (const failed of [false, true]) {
    let guard; let removed = false; const records = [];
    const api = async (suffix, field, options) => {
      if (options?.method === 'POST') {guard = {...options.body, id: 999}; return guard;}
      if (options?.method === 'DELETE') {removed = true; return;}
      return guard;
    };
    const task = withMainMergeGuard({api, number: 1, record: value => records.push(value), operation: async verify => {
      assert.equal(removed, false); assert.deepEqual(guard.conditions.ref_name, {include: ['~ALL'], exclude: ['refs/heads/main']}); assert.deepEqual(guard.bypass_actors, []);
      await verify(); if (failed) throw new Error('target retargeted'); return head;
    }});
    if (failed) await assert.rejects(task, /retargeted/); else assert.equal(await task, head);
    assert.equal(removed, true); assert.deepEqual(records.map(record => record.phase), ['creating', 'active', 'removed']);
  }
});
test('main merge guard rejects weakening during assessment and still removes its ruleset', async () => {
  const {withMainMergeGuard} = require('./merge-reviewed-pr.cjs'); let guard; let removed = false;
  const api = async (suffix, field, options) => {
    if (options?.method === 'POST') return guard = {...options.body, id: 999};
    if (options?.method === 'DELETE') {removed = true; return;}
    return guard;
  };
  await assert.rejects(withMainMergeGuard({api, number: 1, operation: async verify => {guard.bypass_actors.push({actor_id: 5}); await verify();}}), /not enforced/);
  assert.equal(removed, true);
});
test('guard cleanup failure reports the exact recovery ruleset', async () => {
  const {withMainMergeGuard} = require('./merge-reviewed-pr.cjs'); let guard;
  const api = async (suffix, field, options) => {
    if (options?.method === 'POST') return guard = {...options.body, id: 999};
    if (options?.method === 'DELETE') throw new Error('API unavailable');
    return guard;
  };
  await assert.rejects(withMainMergeGuard({api, number: 1, operation: async () => head}), /delete repository ruleset 999/);
});
test('guard recovers a successful creation whose API response was lost', async () => {
  const {withMainMergeGuard} = require('./merge-reviewed-pr.cjs'); let guard; let removed = false; let operated = false;
  const api = async (suffix, field, options) => {
    if (options?.method === 'POST') {guard = {...options.body, id: 999}; throw new Error('response lost');}
    if (options?.method === 'DELETE') {removed = true; return;}
    return suffix.startsWith('rulesets?') ? [guard] : guard;
  };
  await assert.rejects(withMainMergeGuard({api, number: 1, operation: async () => {operated = true;}}), /response lost/);
  assert.equal(removed, true); assert.equal(operated, false);
});

test('fork partial reruns preserve proof from the originating attempt of the same run', async () => {
  const {fetchTargetReceipt} = require('./review-gate.cjs'); const attempts = [];
  const run = {...forkRun(), run_attempt: 3};
  const github = {rest: {actions: {downloadWorkflowRunAttemptLogs: async ({attempt_number}) => {
    attempts.push(attempt_number);
    return {data: attempt_number === 1 ? proofArchive({...forkProof(), run_attempt: 1}) : proofArchive(forkProof(), {folder: 'frontend'})};
  }}}};
  const args = {github, owner: 'owner', repo: 'repo', run, workflow: baseline().trustedWorkflows.CI};
  const proof = await fetchTargetReceipt(args); assert.equal(proof.run_attempt, 1); assert.equal(proof.base, 'main');
  assert.deepEqual(attempts, [3, 2, 1]); assert.deepEqual(await fetchTargetReceipt(args), proof); assert.deepEqual(attempts, [3, 2, 1]);
});
test('fork rerun fallback cannot ignore corrupt conflicting or duplicate current proof', async () => {
  const {fetchTargetReceipt} = require('./review-gate.cjs');
  for (const value of ['corrupt', 'conflicting', 'duplicate']) {
    const attempts=[]; const run={...forkRun(),run_attempt:3};
    const github={rest:{actions:{downloadWorkflowRunAttemptLogs:async ({attempt_number})=>{
      attempts.push(attempt_number);return {data:value==='corrupt'?Buffer.alloc(0):proofArchive({...forkProof(),run_attempt:value==='conflicting'?2:3},{duplicate:value==='duplicate'})};
    }}}};
    await assert.rejects(fetchTargetReceipt({github,owner:'owner',repo:'repo',run,workflow:baseline().trustedWorkflows.CI})); assert.deepEqual(attempts,[3]);
  }
});

test('superseded fork runs with unusable proof cannot veto newer verified CI', async () => {
  const {fetchWorkflowRuns}=require('./review-gate.cjs');const args={owner:'owner',repo:'repo',head,target:{number:1,head,baseRef:'main'},workflows:[baseline().trustedWorkflows.CI]};
  const old={...forkRun(),id:43,conclusion:'cancelled',updated_at:'2026-10-07T00:00:00Z'};
  const newest={...forkRun(),updated_at:'2026-10-07T01:00:00Z'};
  const github={rest:{actions:{listWorkflowRuns:async ({event})=>({data:{workflow_runs:event==='pull_request'?[old,newest]:[]}}),downloadWorkflowRunAttemptLogs:async ({run_id})=>({data:run_id===43?proofArchive(forkProof(),{folder:'frontend'}):proofArchive(forkProof())})}}};
  const input=baseline();input.runs=[...(await fetchWorkflowRuns({github,...args})).data.workflow_runs,input.runs[1]];
  assert.deepEqual(assess(input),[]);assert.doesNotThrow(()=>require('./merge-reviewed-pr.cjs').assertCI(input.runs,input.trustedWorkflows,head));
  input.runs[0].updated_at='2026-10-07T02:00:00Z';assert.match(assess(input).join(' '),/CI has not passed/);
  assert.throws(()=>require('./merge-reviewed-pr.cjs').assertCI(input.runs,input.trustedWorkflows,head));
});
test('fork log authorization and collection errors remain blocking', async () => {
  const {fetchWorkflowRuns}=require('./review-gate.cjs');
  for(const status of [403,429,500]) {
    const github={rest:{actions:{listWorkflowRuns:async ({event})=>({data:{workflow_runs:event==='pull_request'?[forkRun()]:[]}}),downloadWorkflowRunAttemptLogs:async ()=>{const error=new Error('collection unavailable');error.status=status;throw error;}}}};
    await assert.rejects(fetchWorkflowRuns({github,owner:'owner',repo:'repo',head,target:{number:1,head,baseRef:'main'},workflows:[baseline().trustedWorkflows.CI]}),/collection unavailable/);
  }
});

for (const followup of ['Integration skipped.', 'Integration omitted.', 'Integration disabled.', 'Integration remains red.', 'Deployment not executed.', 'Integration deferred.', 'Validation outstanding.', 'A component had issues.']) {
  test(`standalone canonical evidence rejects arbitrary follow-up: ${followup}`, () => {
    const {affirmativeValidation}=require('./review-gate.cjs');
    assert.equal(affirmativeValidation(`Fixed in ${fixed}. All 123 gate regression tests passed. ${followup}`),false);
  });
}
test('standalone disposition grammar accepts the current neutral fixing reference',()=>{
 const {affirmativeValidation}=require('./review-gate.cjs');
 assert.equal(affirmativeValidation(`Current fixing code and preceding implementation evidence confirmed at ${head}. Validation: all 123 gate regression tests passed.`),true);
});

test('bucket invalidates all selected current heads before collecting any PR evidence',async()=>{
 const {runBucket}=require('./review-gate.cjs');const list=Symbol('list'),reviews=Symbol('reviews');const events=[];
 const github={rest:{pulls:{list,listReviews:reviews,get:async({pull_number})=>({data:{state:'open',head:{sha:head},number:pull_number}})},checks:{create:async({head_sha})=>{events.push('pending');return {data:{id:events.length}};},update:async()=>events.push('failed')}},paginate:async method=>{
  if(method===list)return [{number:11},{number:267},{number:12}];
  assert.deepEqual(events.slice(0,2),['pending','pending']);events.push('assessed');throw new Error('synthetic assessment error');
 }};
 await assert.rejects(runBucket({github,context:{repo:{owner:'test',repo:'test'}},bucket:3}),/synthetic assessment error/);
 assert.equal(events.filter(event=>event==='pending').length,2);assert.equal(events.filter(event=>event==='failed').length,2);
});
test('bucket initialization errors complete every already-created pending check as failure',async()=>{
 const {runBucket}=require('./review-gate.cjs');const list=Symbol('list');const completed=[];
 const github={rest:{pulls:{list,get:async({pull_number})=>{if(pull_number===267)throw new Error('invalidation failed');return {data:{state:'open',head:{sha:head}}};}},checks:{create:async()=>({data:{id:42}}),update:async update=>completed.push(update)}},paginate:async()=>[{number:11},{number:267}]};
 await assert.rejects(runBucket({github,context:{repo:{owner:'test',repo:'test'}},bucket:3}),/invalidation failed/);
 assert.equal(completed.length,1);assert.equal(completed[0].check_run_id,42);assert.equal(completed[0].conclusion,'failure');
});
test('protected approval revoked during the final CI fetch blocks merge',async()=>{
 const {mergeReviewedPR}=require('./merge-reviewed-pr.cjs');const input=nativePolicy();let assessments=0,revoked=false,merged=false;
 const approval=JSON.stringify({base:fixed,expires_at:new Date(Date.now()+3600000).toISOString(),heads:{[head]:['.github/scripts/review-gate.cjs']}});
 const github={rest:{repos:{get:async()=>({data:input.repository}),getBranch:async()=>({data:{commit:{sha:fixed}}}),compareCommitsWithBasehead:async()=>({data:{status:'ahead',base_commit:{sha:fixed},merge_base_commit:{sha:fixed}}})},pulls:{get:async()=>({data:{state:'open',base:{ref:'main'},head:{sha:head}}})},actions:{getWorkflow:async({workflow_id})=>({data:{id:workflow_id==='ci.yml'?1:2}}),listWorkflowRuns:async({workflow_id,event})=>{if(assessments===2)revoked=true;return {data:{workflow_runs:baseline().runs.filter(run=>run.workflow_id===workflow_id&&run.event===event)}};}}}};
 const api=mockGuardAPI(async suffix=>{
  if(suffix.includes('protection'))return input.protection;if(suffix.includes('rulesets'))return input.ruleset;
  if(suffix.includes('REVIEW_GATE_APPROVED_UPDATES'))return {value:revoked?'':approval};if(suffix.includes('REVIEW_GATE_RESOLVER_LOGIN'))return {value:'test'};
  return [{id:1,name:'review-evidence',app:{id:mergerPolicy.publisher_app_id},status:'completed',conclusion:'success'}];
 });
 await assert.rejects(mergeReviewedPR({github,context:{repo:{owner:'test',repo:'test'}},number:1,api,policy:mergerPolicy,validate:async({github:live})=>{assessments++;await live.rest.checks.update({conclusion:'success'});},merge:async()=>{merged=true;}}),/approval changed during final validation/);
 assert.equal(assessments,2);assert.equal(merged,false);
});

test('six fork workflow activity events schedule only two affected buckets',async()=>{
 const {preparePullRequests,bucketTargets}=require('./review-gate.cjs');let listingCalls=0;const scheduled=[];
 const prs=Array.from({length:257},(_,i)=>({number:i+1,head:{sha:head,repo:{id:101+i},ref:`branch${i+1}`}}));
 const github={rest:{pulls:{list:Symbol()}},paginate:async()=>{listingCalls++;return prs;}};
 for(const name of ['CI','Security'])for(const action of ['requested','in_progress','completed']){
  const targets=await preparePullRequests({github,context:{repo:{owner:'owner',repo:'repo'},eventName:'workflow_run',payload:{action,workflow_run:{name,head_sha:head,head_repository:{id:111},head_branch:'branch11',pull_requests:[]}}}});
  scheduled.push(...bucketTargets(targets));if(action==='completed')assert.deepEqual(targets,[{number:11}]);else assert.deepEqual(targets,[]);
 }
 assert.equal(listingCalls,2);assert.deepEqual(scheduled,[3,3]);
 const yaml=require('node:fs').readFileSync(require('node:path').join(__dirname,'../workflows/review-gate.yml'),'utf8');
 assert.match(yaml,/workflows: \[CI, Security, Review evidence signal\]\s+types: \[completed\]/);
});
test('fork discovery falls back to matching heads when source metadata is missing',async()=>{
 const {preparePullRequests}=require('./review-gate.cjs');const github={rest:{pulls:{list:Symbol()}},paginate:async()=>[{number:1,head:{sha:head}},{number:2,head:{sha:fixed}}]};
 const targets=await preparePullRequests({github,context:{repo:{owner:'owner',repo:'repo'},eventName:'workflow_run',payload:{action:'completed',workflow_run:{name:'CI',head_sha:head,pull_requests:[]}}}});
 assert.deepEqual(targets,[{number:1}]);
});
test('prepared PR movement invalidates the current head before collecting its evidence',async()=>{
 const {run}=require('./review-gate.cjs');const events=[];
 const github={rest:{pulls:{get:async()=>({data:{state:'open',head:{sha:head}}}),listReviews:Symbol()},checks:{create:async request=>{events.push(['pending',request.head_sha]);return {data:{id:42}};},update:async request=>events.push(['completed',request.check_run_id,request.conclusion])}},paginate:async()=>{
  assert.deepEqual(events,[['pending',head],['completed',41,'failure']]);throw new Error('synthetic evidence error');
 }};
 await assert.rejects(run({github,context:{repo:{owner:'owner',repo:'repo'},payload:{pull_request:{number:1}}},prepared:{pr:{state:'open',head:{sha:fixed}},pendingCheck:{id:41}}}),/synthetic evidence error/);
 assert.deepEqual(events.at(-1),['completed',42,'failure']);
});
test('a closed prepared PR completes its old pending check without collecting evidence',async()=>{
 const {run}=require('./review-gate.cjs');let completion;
 const github={rest:{pulls:{get:async()=>({data:{state:'closed',head:{sha:head}}})},checks:{update:async request=>completion=request,create:async()=>assert.fail('closed PR must not create a check')}},paginate:async()=>assert.fail('closed PR must not collect evidence')};
 await run({github,context:{repo:{owner:'owner',repo:'repo'},payload:{pull_request:{number:1}}},prepared:{pr:{state:'open',head:{sha:head}},pendingCheck:{id:41}}});
 assert.equal(completion.check_run_id,41);assert.equal(completion.conclusion,'failure');
});

test('live merger rechecks its native guard after final policy reads',async()=>{
 const {mergeReviewedPR}=require('./merge-reviewed-pr.cjs');const input=nativePolicy();let assessments=0,captured,merged=false;
 const github={rest:{repos:{get:async()=>({data:input.repository})},pulls:{get:async()=>({data:{state:'open',base:{ref:'main'},head:{sha:head}}})},actions:{getWorkflow:async({workflow_id})=>({data:{id:workflow_id==='ci.yml'?1:2}}),listWorkflowRuns:async({workflow_id,event})=>({data:{workflow_runs:baseline().runs.filter(run=>run.workflow_id===workflow_id&&run.event===event)}})}}};
 const original=mockGuardAPI(async suffix=>suffix.includes('protection')?input.protection:suffix.includes('rulesets')?input.ruleset:[{id:1,name:'review-evidence',app:{id:mergerPolicy.publisher_app_id},status:'completed',conclusion:'success'}]);
 const api=async(suffix,field,options)=>{
  const value=await original(suffix,field,options);if(suffix==='rulesets/999'&&!options)captured=value;
  if(assessments===2&&suffix.includes('REVIEW_GATE_RESOLVER_LOGIN'))captured.bypass_actors.push({actor_id:5});
  return value;
 };
 await assert.rejects(mergeReviewedPR({github,context:{repo:{owner:'test',repo:'test'}},number:1,api,policy:mergerPolicy,validate:async({github:live})=>{assessments++;await live.rest.checks.update({conclusion:'success'});},merge:async()=>{merged=true;}}),/not enforced/);
 assert.equal(merged,false);assert.equal(assessments,2);
});

test('same-timestamp resolver retraction supersedes an earlier passing disposition',()=>{
 const input=baseline();const time='2026-01-02T00:00:00Z';
 input.threads=[{id:'tie',isResolved:true,comments:{nodes:[{author:{login:reviewer},body:'Finding',createdAt:'2026-01-01T00:00:00Z'},
  {author:{login:'maintainer'},body:`Fixed in ${fixed}; tests passed.`,createdAt:time},
  {author:{login:'maintainer'},body:'Disposition withdrawn.',createdAt:time}]}}];
 assert.match(assess(input).join(' '),/no fixing-commit/);
 input.threads[0].comments.nodes.reverse(); // Use a separate explicit restoration sequence in API order.
 input.threads[0].comments.nodes=[{author:{login:reviewer},body:'Finding',createdAt:'2026-01-01T00:00:00Z'},
  {author:{login:'maintainer'},body:'Disposition withdrawn.',createdAt:time},
  {author:{login:'maintainer'},body:`Fixed in ${fixed}; tests passed.`,createdAt:time}];
 assert.match(assess(input).join(' '),/no fixing-commit/);
 input.threads[0].comments.nodes[2].updatedAt='2026-01-02T00:00:01Z';
 assert.deepEqual(assess(input),[]);
});
test('a disposition cannot mix a nonexistent fixing reference with a valid one',()=>{
 const {affirmativeValidation}=require('./review-gate.cjs');const input=baseline();
 const body=`Fixed in ${'c'.repeat(40)}. Current fixing code and preceding implementation evidence confirmed at ${fixed}. Validation: all 140 gate regression tests passed.`;
 assert.equal(affirmativeValidation(body),false);
 input.threads=[{id:'references',isResolved:true,comments:{nodes:[{author:{login:reviewer},body:'Finding',createdAt:'2026-01-01T00:00:00Z'},
 {author:{login:'maintainer'},body,createdAt:'2026-01-02T00:00:00Z'}]}}];
 assert.match(assess(input).join(' '),/no fixing-commit/);
});
test('a test count cannot supply the required fixing commit',()=>{
 const input=baseline();input.commits.push('1234567'+'a'.repeat(33));
 input.threads=[{id:'count',isResolved:true,comments:{nodes:[{author:{login:reviewer},body:'Finding',createdAt:'2026-01-01T00:00:00Z'},
 {author:{login:'maintainer'},body:'Validation: all 1234567 tests passed.',createdAt:'2026-01-02T00:00:00Z'}]}}];
 assert.match(assess(input).join(' '),/no fixing-commit/);
});
test('capped history fails closed even if sequential status searches would omit a transition',async()=>{
 const {fetchWorkflowRuns}=require('./review-gate.cjs');const calls=[];
 const github={rest:{actions:{listWorkflowRuns:async params=>{
  calls.push(params);return {data:{total_count:1001,workflow_runs:[baseline().runs[0]]}};
 }}}};
 await assert.rejects(fetchWorkflowRuns({github,owner:'owner',repo:'repo',head,events:['pull_request'],workflows:[{id:1}]}),/ceiling/);
 assert.equal(calls.length,1);assert.equal(calls[0].status,undefined);
});
test('a full tenth history page without a count cannot imply complete history',async()=>{
 const {fetchWorkflowRuns}=require('./review-gate.cjs');
 const github={rest:{actions:{listWorkflowRuns:async()=>({data:{workflow_runs:Array.from({length:100},()=>({...baseline().runs[0]}))}})}}};
 await assert.rejects(fetchWorkflowRuns({github,owner:'owner',repo:'repo',head,events:['pull_request'],workflows:[{id:1}]}),/ceiling/);
});
test('gh adapter preserves independent active-status queries',async()=>{
 const calls=[];const {github}=require('./merge-reviewed-pr.cjs').createGhAdapter('owner/repo',args=>{calls.push(args);return {workflow_runs:[]};});
 await github.rest.actions.listWorkflowRuns({workflow_id:1,status:'queued',per_page:100,page:1});
 assert.equal(calls[0][1],'repos/owner/repo/actions/workflows/1/runs?status=queued&page=1&per_page=100');
});

test('an older edited retraction tied with a later-created valid disposition fails closed',()=>{
 const input=baseline();input.threads=[{id:'edited',isResolved:true,comments:{nodes:[
  {author:{login:reviewer},body:'Finding',createdAt:'2026-01-01T00:00:00Z'},
  {author:{login:'maintainer'},body:'Withdrawn.',createdAt:'2026-01-02T00:00:00Z',updatedAt:'2026-01-03T00:00:00Z'},
  {author:{login:'maintainer'},body:`Fixed in ${fixed}. Tests passed.`,createdAt:'2026-01-03T00:00:00Z'}]}}];
 assert.match(assess(input).join(' '),/no fixing-commit/);
 input.threads[0].comments.nodes[1].body=`Fixed in ${fixed}. Tests passed.`;
 assert.deepEqual(assess(input),[]);
});
for(const status of ['ahead','identical','behind','diverged'])test(`fixing references exclude base history: ${status}`,async()=>{
 const {fetchCommitEvidence}=require('./review-gate.cjs');const base='c'.repeat(40);const calls=[];
 const github={rest:{repos:{compareCommitsWithBasehead:async({basehead})=>{
  calls.push(basehead);if(basehead.endsWith(head))return {data:{status:'ahead',base_commit:{sha:fixed},merge_base_commit:{sha:fixed}}};
  return {data:{status,base_commit:{sha:fixed},merge_base_commit:{sha:['ahead','identical'].includes(status)?fixed:base}}};
 }}}};
 const args={github,owner:'owner',repo:'repo',head,base,resolver:'maintainer',comments:[],threads:[{comments:{nodes:[{author:{login:'maintainer'},body:`Fixed in ${fixed}. Tests passed.`,createdAt:'2026-01-02T00:00:00Z'}]}}]};
 const proof=await fetchCommitEvidence(args);assert.equal(proof.fixingCommitProof[fixed],['behind','diverged'].includes(status)?fixed:undefined);
 const input=baseline();input.commitProof=proof.commitProof;input.fixingCommitProof=proof.fixingCommitProof;
 input.threads=[{id:'range',isResolved:true,comments:{nodes:[{author:{login:reviewer},body:'Finding',createdAt:'2026-01-01T00:00:00Z'},{author:{login:'maintainer'},body:`Fixed in ${fixed}. Tests passed.`,createdAt:'2026-01-02T00:00:00Z'}]}}];
 assert.equal(assess(input).length,['behind','diverged'].includes(status)?0:1);
 await fetchCommitEvidence(args);assert.equal(calls.filter(call=>call===`${fixed}...${base}`).length,1);
});

for(const base of [undefined,head])test(`fixing references require a distinct current base: ${base?'same head':'absent'}`,async()=>{
 const {fetchCommitEvidence}=require('./review-gate.cjs');
 const github={rest:{repos:{compareCommitsWithBasehead:async()=>assert.fail('No comparison is needed')}}};
 const args={github,owner:'owner',repo:'repo',head,base,resolver:'maintainer',comments:[],threads:[{comments:{nodes:[{author:{login:'maintainer'},body:`Fixed in ${head}. Tests passed.`,createdAt:'2026-01-02T00:00:00Z'}]}}]};
 if(!base)await assert.rejects(fetchCommitEvidence(args),/base SHA/);
 else assert.deepEqual((await fetchCommitEvidence(args)).fixingCommitProof,{});
});
