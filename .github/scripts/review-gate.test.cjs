const test = require('node:test');
const assert = require('node:assert/strict');
const { assess } = require('./review-gate.cjs');
const head = 'a'.repeat(40);
const fixed = 'b'.repeat(40);
const reviewer = 'chatgpt-codex-connector';
const baseline = () => ({ head, reviewer, resolver: 'maintainer', protectedDefinitions: {'.github/scripts/review-gate.cjs': true, '.github/workflows/review-gate.yml': true, '.github/workflows/review-evidence-signal.yml': true, '.github/scripts/merge-reviewed-pr.cjs': true, '.github/review-gate-policy.json': true}, trustedWorkflows: {CI: {id: 1, definitionMatches: true, path: '.github/workflows/ci.yml'}, Security: {id: 2, definitionMatches: true, path: '.github/workflows/security.yml'}}, commits: [head, fixed], runs: ['CI', 'Security'].map((name, index) => ({name, workflow_id: index + 1, path: `.github/workflows/${name === 'CI' ? 'ci' : 'security'}.yml`, head_sha: head, event: 'pull_request', id: 1, status: 'completed', conclusion: 'success'})), reviews: [{ user: { login: reviewer }, commit_id: head, state: 'COMMENTED', submitted_at: '2026-02-01T00:00:00Z' }], comments: [], threads: [] });
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
  await assert.rejects(preparePullRequests({github, context}), /synthetic discovery failure/);
});

test('all workflow-associated PRs are discovered and duplicate numbers are removed', async () => {
  const { preparePullRequests } = require('./review-gate.cjs');
  const github = {rest: {pulls: {get: async ({pull_number}) => ({data: {state: pull_number === 13 ? 'closed' : 'open', head: {sha: head}}})},
    checks: {create: async () => ({data: {id: 1}})}}};
  const targets = await preparePullRequests({github, context: {repo: {owner: 'test', repo: 'test'},
    eventName: 'workflow_run', payload: {workflow_run: {pull_requests: [{number: 11}, {number: 12}, {number: 11}, {number: 13}]}}}});
  assert.deepEqual(targets.map(target => target.number), [11, 12]);
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
  const github = {rest: {actions: {listWorkflowRuns: async ({page, per_page, head_sha}) => {
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
  const github = {rest: {actions: {listWorkflowRuns: async ({workflow_id}) => {
    requested.push(workflow_id); return {data: {workflow_runs: baseline().runs.filter(run => run.workflow_id === workflow_id)}};
  }}}};
  const {data} = await fetchWorkflowRuns({github, owner: 'test', repo: 'test', head, workflows: [{id: 1}, {id: 2}]});
  assert.deepEqual(requested, [1, 2]); assert.deepEqual(data.workflow_runs, baseline().runs);
});

test('bulk validation of 257 PRs stays below the installation REST budget', async () => {
  const {preparePullRequests, bucketTargets, runBucket} = require('./review-gate.cjs');
  let requests = 0;
  const prs = Array.from({length: 257}, (_, i) => ({number: i + 1}));
  const methods = {list: Symbol('list'), reviews: Symbol('reviews'), comments: Symbol('comments'), commits: Symbol('commits')};
  const github = {rest: {
    pulls: {list: methods.list, listReviews: methods.reviews, get: async () => {requests++; return {data: {state: 'open', head: {sha: head}}};}},
    issues: {listComments: methods.comments},
    repos: {compareCommitsWithBasehead: async ({basehead}) => {requests++; const sha = basehead.startsWith(head.slice(0, 10)) ? head : fixed; return {data: {status: sha === head ? 'identical' : 'ahead', base_commit: {sha}, merge_base_commit: {sha}}};}, listCommits: methods.commits, get: async () => {requests++; return {data: {default_branch: 'main'}};}},
    actions: {getWorkflow: async ({workflow_id}) => {requests++; return {data: {id: workflow_id === 'ci.yml' ? 1 : 2}};},
      listWorkflowRuns: async ({workflow_id}) => {requests++; return {data: {workflow_runs: baseline().runs.filter(run => run.workflow_id === workflow_id)}};}},
    checks: {create: async () => {requests++; return {data: {id: 42}};}, update: async () => {requests++;}}
  }, paginate: async method => {
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

const mergerPolicy = {publisher_app_id: 5218906, trusted_mergers_ruleset_id: 24627093};
const nativePolicy = () => ({policy: mergerPolicy, repository: {permissions: {admin: true}},
  protection: {enforce_admins: {enabled: true}, required_conversation_resolution: {enabled: true}, required_status_checks: {checks: [{context: 'review-evidence', app_id: mergerPolicy.publisher_app_id}]}},
  ruleset: {enforcement: 'active', conditions: {ref_name: {include: ['refs/heads/main'], exclude: []}}, rules: [{type: 'update'}],
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
  const api = async suffix => suffix.includes('protection') ? input.protection : suffix.includes('rulesets') ? input.ruleset
    : [{id: 1, name: 'review-evidence', app: {id: mergerPolicy.publisher_app_id}, status: 'completed', conclusion: 'success'}];
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
    const api = async suffix => suffix.includes('protection') ? input.protection : suffix.includes('rulesets') ? input.ruleset
      : [{id: 1, name: 'review-evidence', app: {id: mergerPolicy.publisher_app_id}, status: 'completed', conclusion: 'success'}];
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
      repos: {get: async () => ({data: {default_branch: 'main'}}), getBranch: async () => ({data: {commit: {sha: ++reads > 1 && moved ? head : fixed}}})},
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
  const api = async suffix => suffix.includes('protection') ? input.protection : suffix.includes('rulesets') ? input.ruleset
    : [{id: 1, name: 'review-evidence', app: {id: mergerPolicy.publisher_app_id}, status: 'completed', conclusion: 'success'}];
  await assert.rejects(mergeReviewedPR({github, context: {repo: {owner: 'test', repo: 'test'}}, number: 1, api, policy: mergerPolicy,
    validate: async ({github: live}) => {
      if (++assessments === 2) throw new Error('Mutable evidence edited during preflight');
      await live.rest.checks.update({conclusion: 'success'});
    }, merge: async () => {merged = true;}}), /Mutable evidence edited/);
  assert.equal(assessments, 2); assert.equal(merged, false);
});
