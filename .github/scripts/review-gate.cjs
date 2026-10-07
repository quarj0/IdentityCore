const PROTECTED_PATHS = ['.github/scripts/review-gate.cjs', '.github/workflows/review-gate.yml', '.github/workflows/review-evidence-signal.yml', '.github/scripts/merge-reviewed-pr.cjs', '.github/review-gate-policy.json'];
const REVIEWER = 'chatgpt-codex-connector';
const BUCKET_COUNT = 8;
const trustedMetadata = new WeakMap();
const isEvidenceReviewer = author => [REVIEWER, `${REVIEWER}[bot]`].includes(author?.login);
const relevantComments = comments => comments.filter(comment => isEvidenceReviewer(comment.user));
const relevantReviews = reviews => reviews.filter(review => isEvidenceReviewer(review.user));

function affirmativeValidation(body) {
  body = body.replace(/\b(\w+)n['’]t\b/gi, '$1 not');
  const clauses = body.split(/[.!?\n;:]+/);
  if (clauses.some(clause => /^\s*(?:except|excluding|partial(?:ly)?|incomplete|but|however|only|not|none|no|zero)\b/i.test(clause))) return false;
  if (clauses.some(clause => /\b(fail|fails|failed|failing|failure|failures|not|never|unable|incomplete|pending|unverified|unsuccessful|cannot|no|none|zero|0|partial|partially|except|exception|exceptions)\b/i.test(clause))) return false;
  return clauses.some(clause => /^\s*(?:all\s+)?(?:[1-9]\d*\s+)?(?:(?:gate|regression|unit|integration|e2e|targeted|frontend|backend|sdk|live|smoke|added|new)\s+)*(?:tests?|validation)(?:\s+(?:have|has))?\s+(?:pass(?:ed|es)?|(?:was|were|is|are)\s+successful|successful(?:ly)?)\s*$/i.test(clause));
}

function approvedDefinitionPaths({manifest, head, base, now = Date.now()}) {
  if (!manifest) return new Set();
  const approval = JSON.parse(manifest);
  const expiry = Date.parse(approval.expires_at);
  if (!/^[0-9a-f]{40}$/.test(approval.base || '') || !Number.isFinite(expiry) || expiry <= now || expiry > now + 86400000) throw new Error('Protected update approval requires a full base SHA and an expiry within 24 hours.');
  if (approval.base !== base) return new Set();
  const paths = approval.heads?.[head];
  if (!paths) return new Set();
  if (!/^[0-9a-f]{40}$/.test(head) || !Array.isArray(paths) || !paths.length || paths.some(path => !['.github/workflows/ci.yml', '.github/workflows/security.yml', ...PROTECTED_PATHS].includes(path))) throw new Error('Protected update approval must identify an exact head and known protected paths.');
  return new Set(paths);
}

async function verifyApprovedDefinitionPaths({github, owner, repo, manifest, head, base}) {
  const paths = approvedDefinitionPaths({manifest, head, base});
  if (paths.size) {
    const {data} = await github.rest.repos.compareCommitsWithBasehead({owner, repo, basehead: `${base}...${head}`});
    if (!['ahead', 'identical'].includes(data.status) || data.base_commit?.sha !== base || data.merge_base_commit?.sha !== base) throw new Error('Approved main base must be an ancestor of the reviewed head.');
  }
  return paths;
}

function assess({ pullNumber, baseRef, head, reviewer, resolver, reviews, comments, threads, commits, commitProof, runs, trustedWorkflows, protectedDefinitions }) {
  const provenToken = token => commitProof ? commitProof[token] : commits.find(sha => sha.startsWith(token));
  const isResolver = author => Boolean(resolver) && author?.login === resolver;
  const isReviewer = author => author?.login === reviewer || author?.login === `${reviewer}[bot]`;
  const finalReviews = reviews.filter(r => isReviewer(r.user) && r.commit_id === head);
  let changesRequested = false;
  for (const review of reviews.filter(r => isReviewer(r.user))) {
    // COMMENTED does not clear a review decision. The API replaces the
    // original state with DISMISSED when an authorized dismissal occurs.
    if (review.state === 'CHANGES_REQUESTED') changesRequested = true;
    if (review.state === 'APPROVED') changesRequested = false;
  }
  const blockingReview = changesRequested || finalReviews.some(r => r.state === 'PENDING');
  const reviewed = !blockingReview && (reviews.some(r => isReviewer(r.user) && r.commit_id === head && ['APPROVED', 'COMMENTED'].includes(r.state)) ||
    comments.some(c => isReviewer(c.user) && (
      [...c.body.matchAll(/\*\*Reviewed commit:\*\*\s*`([0-9a-f]{10,40})`/g)].some(m => head.startsWith(m[1]) && provenToken(m[1]) === head) ||
      (c.body.startsWith('<!-- codex-pull-request-review-summary -->') &&
        [...c.body.matchAll(/^\|[^|\n]*\*\*Code Review\*\*[^|\n]*\|\s*✅\s*\*\*Completed\*\*[^|\n]*\|\s*`([0-9a-f]{7,40})`/gm)]
          .some(m => head.startsWith(m[1]) && provenToken(m[1]) === head && commits.filter(sha => sha.startsWith(m[1])).length === 1))
    )));
  const problems = [];
  const evidenceTimes = [];
  for (const name of ['CI', 'Security']) {
    const trusted = trustedWorkflows?.[name];
    if (!trusted?.definitionMatches) problems.push(`${name} workflow definition differs from trusted default-branch content.`);
    const candidates = runs.filter(r => trusted && r.workflow_id === trusted.id && typeof r.path === 'string' && r.path.split('@', 1)[0] === trusted.path && r.head_sha === head && r.event === 'pull_request' && (!baseRef || isRunForPR(r, {number: pullNumber, baseRef, head})));
    const activity = run => Date.parse(run.updated_at || run.run_started_at || run.created_at) || 0;
    const latest = candidates.sort((a, b) => activity(b) - activity(a) || b.id - a.id)[0];
    if (runs.some(r => trusted && r.workflow_id === trusted.id && r.path?.split('@', 1)[0] === trusted.path && r.head_sha === head && r.event === 'pull_request' && !r.pull_requests?.length && r.status !== 'completed') || candidates.some(r => r.status !== 'completed') || !latest || latest.conclusion !== 'success') problems.push(`${name} has not passed for the final head.`);
  }
  for (const path of PROTECTED_PATHS) {
    if (!protectedDefinitions?.[path]) problems.push(`Protected review-gate definition differs: ${path}.`);
  }
  if (!reviewed) problems.push(`Configured review has not completed for ${head}.`);
  for (const thread of threads) {
    if (!thread.isResolved) {
      problems.push(`Unresolved thread ${thread.id}.`);
      continue;
    }
    const nodes = thread.comments.nodes;
    const feedback = nodes.filter(c => !isResolver(c.author));
    const feedbackTimes = feedback.map(c => Date.parse(c.updatedAt || c.createdAt));
    const lastFeedback = Math.max(...feedbackTimes);
    const dispositions = nodes.filter(c => isResolver(c.author));
    const dispositionTimes = dispositions.map(c => Date.parse(c.updatedAt || c.createdAt));
    const latestDisposition = Math.max(...dispositionTimes);
    const evidence = feedbackTimes.length > 0 && feedbackTimes.every(Number.isFinite) &&
      dispositionTimes.every(Number.isFinite) && dispositions.filter(c =>
      Date.parse(c.updatedAt || c.createdAt) === latestDisposition &&
      latestDisposition > lastFeedback &&
      affirmativeValidation(c.body) &&
      [...c.body.matchAll(/\b([0-9a-f]{7,40})\b/g)].some(m => Boolean(provenToken(m[1])))
    );
    if (evidence && evidence.length) evidenceTimes.push(Math.max(...evidence.map(c => Date.parse(c.updatedAt || c.createdAt))));
    if (!evidence || !evidence.length) problems.push(`Resolved thread ${thread.id} has no fixing-commit and validation evidence from the trusted resolver.`);
  }
  if (reviewed && evidenceTimes.length) {
    const completed = [
      ...finalReviews.filter(r => ['APPROVED', 'COMMENTED'].includes(r.state)).map(r => Date.parse(r.submitted_at)),
      ...comments.filter(c => isReviewer(c.user) && (
        [...c.body.matchAll(/\*\*Reviewed commit:\*\*\s*`([0-9a-f]{10,40})`/g)].some(m => head.startsWith(m[1]) && provenToken(m[1]) === head) ||
        (c.body.startsWith('<!-- codex-pull-request-review-summary -->') &&
          [...c.body.matchAll(/^\|[^|\n]*\*\*Code Review\*\*[^|\n]*\|\s*✅\s*\*\*Completed\*\*[^|\n]*\|\s*`([0-9a-f]{7,40})`/gm)]
            .some(m => head.startsWith(m[1]) && provenToken(m[1]) === head && commits.filter(sha => sha.startsWith(m[1])).length === 1))
      )).map(c => Date.parse(c.updated_at || c.created_at))
    ].filter(Number.isFinite);
    if (!completed.some(time => time > Math.max(...evidenceTimes))) {
      problems.push('Final-head review must complete after the latest resolver evidence.');
    }
  }
  return problems;
}

async function fetchThreads(github, owner, repo, number) {
  const threads = [];
  let cursor = null;
  do {
    const data = await github.graphql(`query($owner:String!,$repo:String!,$number:Int!,$cursor:String) {
      repository(owner:$owner,name:$repo) { pullRequest(number:$number) {
        reviewThreads(first:100,after:$cursor) { pageInfo { hasNextPage endCursor }
          nodes { id isResolved comments(first:100) { nodes { body createdAt updatedAt author { login } } pageInfo { hasNextPage } } }
        }
      } }
    }`, { owner, repo, number, cursor });
    const page = data.repository.pullRequest.reviewThreads;
    threads.push(...page.nodes);
    cursor = page.pageInfo.hasNextPage ? page.pageInfo.endCursor : null;
  } while (cursor);
  return threads;
}

const receiptCache = new WeakMap();
function isRunForPR(run, {number, baseRef, head}) {
  return run.pull_requests?.some(pr => pr.number === number && pr.base?.ref === baseRef && pr.head?.sha === head) ||
    (run.pr_target_receipt?.number === number && run.pr_target_receipt?.base === baseRef && run.pr_target_receipt?.head === head);
}

// Read only the fixed proof job's step log. Never extract a PR-controlled ZIP path.
function targetReceiptFromArchive(input, run, workflow) {
  const {inflateRawSync} = require('node:zlib');
  const zip = Buffer.from(input);
  if (zip.length < 22 || zip.length > 64 * 1024 * 1024) throw new Error('Invalid target proof archive size.');
  let end = zip.length - 22;
  while (end >= Math.max(0, zip.length - 65557) && zip.readUInt32LE(end) !== 0x06054b50) end--;
  if (end < 0 || zip.readUInt32LE(end) !== 0x06054b50 || end + 22 + zip.readUInt16LE(end + 20) !== zip.length ||
      zip.readUInt16LE(end + 4) || zip.readUInt16LE(end + 6) || zip.readUInt16LE(end + 8) !== zip.readUInt16LE(end + 10)) throw new Error('Invalid target proof ZIP directory.');
  const count = zip.readUInt16LE(end + 10), directory = zip.readUInt32LE(end + 16), size = zip.readUInt32LE(end + 12);
  if (directory + size !== end || count === 65535) throw new Error('Unsupported target proof ZIP directory.');
  const label = workflow.path === '.github/workflows/ci.yml' ? 'CI' : workflow.path === '.github/workflows/security.yml' ? 'Security' : null;
  if (!label) throw new Error('Unknown target proof workflow.');
  let cursor = directory; const matches = [];
  for (let index = 0; index < count; index++) {
    if (cursor + 46 > end || zip.readUInt32LE(cursor) !== 0x02014b50) throw new Error('Invalid target proof ZIP entry.');
    const nameSize = zip.readUInt16LE(cursor + 28), extra = zip.readUInt16LE(cursor + 30), comment = zip.readUInt16LE(cursor + 32);
    const next = cursor + 46 + nameSize + extra + comment;
    if (next > end) throw new Error('Truncated target proof ZIP entry.');
    const name = zip.subarray(cursor + 46, cursor + 46 + nameSize).toString('utf8');
    if (name.startsWith(`${label} target proof/`) && /^\d+_Record immutable PR target\.txt$/.test(name.slice(`${label} target proof/`.length))) {
      const flags = zip.readUInt16LE(cursor + 8), method = zip.readUInt16LE(cursor + 10), compressed = zip.readUInt32LE(cursor + 20), length = zip.readUInt32LE(cursor + 24), local = zip.readUInt32LE(cursor + 42);
      if (flags & 1 || ![0, 8].includes(method) || length > 65536 || compressed > 65536 || local + 30 > directory || zip.readUInt32LE(local) !== 0x04034b50) throw new Error('Unsupported target proof ZIP entry.');
      const localName = zip.readUInt16LE(local + 26), localExtra = zip.readUInt16LE(local + 28), start = local + 30 + localName + localExtra;
      if (start + compressed > directory || zip.subarray(local + 30, local + 30 + localName).toString('utf8') !== name || zip.readUInt16LE(local + 8) !== method) throw new Error('Invalid target proof local entry.');
      const bytes = zip.subarray(start, start + compressed);
      const text = method === 8 ? inflateRawSync(bytes, {maxOutputLength: 65536}) : bytes;
      if (text.length !== length) throw new Error('Invalid target proof log length.');
      let crc = 0xffffffff;
      for (const byte of text) {crc ^= byte; for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);}
      if (((crc ^ 0xffffffff) >>> 0) !== zip.readUInt32LE(cursor + 16)) throw new Error('Invalid target proof log checksum.');
      for (const line of text.toString('utf8').split('\n')) {
        const match = line.match(/(?:^|\s)IDENTITYCORE_PR_TARGET (\{.*\})\s*$/);
        if (match) matches.push(JSON.parse(match[1]));
      }
    }
    cursor = next;
  }
  if (cursor !== end || matches.length !== 1) throw new Error('A unique immutable PR target proof is required.');
  const proof = matches[0];
  if (!Number.isSafeInteger(proof.number) || proof.number <= 0 || proof.head !== run.head_sha || !proof.base ||
      proof.run_id !== run.id || proof.run_attempt !== run.run_attempt) throw new Error('Target proof does not match its workflow run attempt.');
  return proof;
}

async function fetchTargetReceipt({github, owner, repo, run, workflow}) {
  let cache = receiptCache.get(github);
  if (!cache) {cache = new Map(); receiptCache.set(github, cache);}
  const key = `${owner}/${repo}/${run.id}/${run.run_attempt}`;
  if (!cache.has(key)) cache.set(key, (async () => {
    const {data} = await github.rest.actions.downloadWorkflowRunAttemptLogs({owner, repo, run_id: run.id, attempt_number: run.run_attempt});
    return targetReceiptFromArchive(data, run, workflow);
  })());
  return cache.get(key);
}

async function fetchWorkflowRuns({ github, owner, repo, head, target, workflows = [{id: 'ci.yml'}, {id: 'security.yml'}] }) {
  const runs = [];
  for (const workflow of workflows) {
    for (const event of ['pull_request', 'push']) {
    for (let page = 1; ; page++) {
      const { data } = await github.rest.actions.listWorkflowRuns({ owner, repo, workflow_id: workflow.id, head_sha: head, event, per_page: 100, page });
      for (const candidate of data.workflow_runs) {
        // Ignore any remotely supplied receipt property; only this collector can attest it.
        const run = {...candidate}; delete run.pr_target_receipt;
        if (target && event === 'pull_request' && !run.pull_requests?.length && run.status === 'completed' &&
            run.head_sha === head && run.workflow_id === workflow.id && run.path?.split('@', 1)[0] === workflow.path) {
          run.pr_target_receipt = await fetchTargetReceipt({github, owner, repo, run, workflow});
        }
        runs.push(run);
      }
      if (data.workflow_runs.length < 100) break;
    }
    }
  }
  return { data: { workflow_runs: runs } };
}

async function fetchCommitEvidence({ github, owner, repo, head, resolver, comments, threads }) {
  const bodies = comments.map(comment => comment.body);
  for (const thread of threads) {
    const dispositions = thread.comments.nodes.filter(comment => comment.author?.login === resolver);
    const latest = Math.max(...dispositions.map(comment => Date.parse(comment.updatedAt || comment.createdAt)));
    bodies.push(...dispositions.filter(comment => Date.parse(comment.updatedAt || comment.createdAt) === latest).map(comment => comment.body));
  }
  const tokens = [...new Set(bodies.flatMap(body => [...body.matchAll(/\b([0-9a-f]{7,40})\b/g)].map(match => match[1])))];
  const commitProof = {[head]: head};
  for (const token of tokens) {
    if (token === head) continue;
    try {
      const {data} = await github.rest.repos.compareCommitsWithBasehead({owner, repo, basehead: `${token}...${head}`});
      if (['ahead', 'identical'].includes(data.status) && data.base_commit?.sha?.startsWith(token) && data.merge_base_commit?.sha === data.base_commit.sha) commitProof[token] = data.base_commit.sha;
    } catch (error) {
      // Prose may contain a nonexistent or ambiguous hexadecimal identifier.
      // Missing tokens cannot become evidence; collection/authorization failures fail closed.
      if (![404, 422].includes(error.status)) throw error;
    }
  }
  return {commits: [...new Set(Object.values(commitProof))], commitProof};
}

async function metadata({ github, owner, repo }) {
  let cache = trustedMetadata.get(github);
  if (!cache) { cache = new Map(); trustedMetadata.set(github, cache); }
  const key = `${owner}/${repo}`;
  if (!cache.has(key)) cache.set(key, (async () => {
    const [{data: repository}, {data: ci}, {data: security}] = await Promise.all([
      github.rest.repos.get({owner, repo}),
      github.rest.actions.getWorkflow({owner, repo, workflow_id: 'ci.yml'}),
      github.rest.actions.getWorkflow({owner, repo, workflow_id: 'security.yml'})
    ]);
    return {repository, workflows: {CI: {id: ci.id, path: '.github/workflows/ci.yml'}, Security: {id: security.id, path: '.github/workflows/security.yml'}}};
  })());
  return cache.get(key);
}

async function definitionMatches({ github, owner, repo, head, defaultBranch }) {
  const paths = ['.github/workflows/ci.yml', '.github/workflows/security.yml', ...PROTECTED_PATHS];
  const variables = {owner, repo};
  const declarations = ['$owner:String!', '$repo:String!'];
  const objects = [];
  paths.forEach((path, i) => {
    for (const [kind, ref] of [['trusted', defaultBranch], ['proposed', head]]) {
      const key = `${kind}${i}`;
      variables[key] = `${ref}:${path}`;
      declarations.push(`$${key}:String!`);
      objects.push(`${key}:object(expression:$${key}) { __typename ... on Blob { oid } }`);
    }
  });
  const data = await github.graphql(`query(${declarations.join(',')}) { repository(owner:$owner,name:$repo) { ${objects.join(' ')} } }`, variables);
  return Object.fromEntries(paths.map((path, i) => {
    const trusted = data.repository[`trusted${i}`];
    const proposed = data.repository[`proposed${i}`];
    return [path, trusted?.__typename === 'Blob' && proposed?.__typename === 'Blob' && trusted.oid === proposed.oid];
  }));
}

async function run({ github, context, resolverLogin, approvedUpdates = process.env.REVIEW_GATE_APPROVED_UPDATES || '' }) {
  const { owner, repo } = context.repo;
  const number = context.payload.pull_request?.number ||
    (context.payload.issue?.pull_request ? context.payload.issue.number : undefined) ||
    context.payload.workflow_run?.pull_requests?.[0]?.number ||
    Number(context.payload.inputs?.pr_number);
  if (!number) throw new Error('A pull-request number is required.');
  const { data: pr } = await github.rest.pulls.get({ owner, repo, pull_number: number });
  if (pr.state !== 'open') return;
  // This function runs inside the per-PR workflow lock. Fetch its current head
  // here so discovery ordering cannot leave a newer head check orphaned.
  const head = pr.head.sha;
  const resolver = resolverLogin || process.env.REVIEW_GATE_RESOLVER_LOGIN || owner;
  const pendingCheck = (await github.rest.checks.create({ owner, repo, head_sha: head,
    name: 'review-evidence', status: 'in_progress',
    output: { title: 'Review evidence validation in progress', summary: `Revalidating mutable evidence for ${head}.` }
  })).data;
  let completed = false;
  try {
  const reviews = relevantReviews(await github.paginate(github.rest.pulls.listReviews, { owner, repo, pull_number: number, per_page: 100 }));
  const comments = relevantComments(await github.paginate(github.rest.issues.listComments, { owner, repo, issue_number: number, per_page: 100 }));
  const threads = await fetchThreads(github, owner, repo, number);
  const {commits, commitProof} = await fetchCommitEvidence({github, owner, repo, head, resolver, comments, threads});
  const {repository, workflows} = await metadata({github, owner, repo});
  const matches = await definitionMatches({github, owner, repo, head, defaultBranch: repository.default_branch});
  let approvedBase;
  if (approvedUpdates) {
    approvedBase = (await github.rest.repos.getBranch({owner, repo, branch: repository.default_branch})).data.commit.sha;
    for (const path of await verifyApprovedDefinitionPaths({github, owner, repo, manifest: approvedUpdates, head, base: approvedBase})) matches[path] = true;
  }
  const trustedWorkflows = Object.fromEntries(Object.entries(workflows).map(([name, workflow]) => [name, {...workflow, definitionMatches: matches[workflow.path]}]));
  const protectedDefinitions = Object.fromEntries(PROTECTED_PATHS.map(path => [path, matches[path]]));
  const {data: workflowRuns} = await fetchWorkflowRuns({github, owner, repo, head, target: {number, baseRef: pr.base?.ref || 'main', head}, workflows: Object.values(workflows)});
  const problems = assess({ pullNumber: number, baseRef: pr.base?.ref || 'main', head, resolver, commitProof, trustedWorkflows, protectedDefinitions, runs: workflowRuns.workflow_runs, reviewer: 'chatgpt-codex-connector', reviews, comments, threads, commits });
  if (threads.some(t => t.comments.pageInfo.hasNextPage)) problems.push('A thread exceeds the evidence page limit; review it explicitly.');
  const [currentReviewsRaw, currentCommentsRaw, currentThreads, {data: current}, {data: currentWorkflowRuns}] = await Promise.all([
    github.paginate(github.rest.pulls.listReviews, { owner, repo, pull_number: number, per_page: 100 }),
    github.paginate(github.rest.issues.listComments, { owner, repo, issue_number: number, per_page: 100 }),
    fetchThreads(github, owner, repo, number),
    github.rest.pulls.get({ owner, repo, pull_number: number }),
    fetchWorkflowRuns({ github, owner, repo, head, target: {number, baseRef: pr.base?.ref || 'main', head}, workflows: Object.values(workflows) })
  ]);
  if (approvedBase) {
    if ((await github.rest.repos.getBranch({owner, repo, branch: repository.default_branch})).data.commit.sha !== approvedBase) problems.push('Protected update approval base moved during validation.');
    approvedDefinitionPaths({manifest: approvedUpdates, head, base: approvedBase});
  }
  const currentReviews = relevantReviews(currentReviewsRaw);
  const currentComments = relevantComments(currentCommentsRaw);
  if (JSON.stringify([reviews, comments, threads]) !== JSON.stringify([currentReviews, currentComments, currentThreads])) {
    problems.push('Mutable review evidence changed during validation; rerun against a stable snapshot.');
  }
  problems.push(...assess({ pullNumber: number, baseRef: pr.base?.ref || 'main', head, resolver, commitProof, trustedWorkflows, protectedDefinitions, runs: currentWorkflowRuns.workflow_runs, reviewer: 'chatgpt-codex-connector', reviews: currentReviews, comments: currentComments, threads: currentThreads, commits }));
  if ((current.base?.ref || 'main') !== (pr.base?.ref || 'main')) problems.push('Pull-request base changed during validation.');
  if (current.head.sha !== head) problems.push('Pull-request head moved during validation; rerun against its current head.');
  await github.rest.checks.update({ owner, repo, check_run_id: pendingCheck.id, status: 'completed',
    conclusion: problems.length ? 'failure' : 'success',
    output: { title: problems.length ? 'Review evidence incomplete' : 'Final-head review evidence verified',
      summary: problems.length ? problems.join('\n') : `Configured review completed for ${head}; every thread has commit and validation evidence.` }
  });
  completed = true;
  if (problems.length) throw new Error(problems.join('\n'));
  } catch (error) {
    if (!completed) {
      await github.rest.checks.update({ owner, repo, check_run_id: pendingCheck.id,
        status: 'completed', conclusion: 'failure',
        output: { title: 'Review evidence validation failed', summary: 'Evidence could not be collected or validated; retry the gate.' }
      });
    }
    throw error;
  }
}

async function preparePullRequests({ github, context }) {
  const { owner, repo } = context.repo;
  const number = context.payload.pull_request?.number ||
    (context.payload.issue?.pull_request ? context.payload.issue.number : undefined) ||
    Number(context.payload.inputs?.pr_number);
  let pullRequests;
  if (context.eventName === 'push') {
    pullRequests = await github.paginate(github.rest.pulls.list, { owner, repo, state: 'open', per_page: 100 });
  } else if (context.eventName === 'workflow_run') {
    pullRequests = context.payload.workflow_run.pull_requests || [];
    if (!pullRequests.length && ['CI', 'Security', 'Review evidence signal'].includes(context.payload.workflow_run.name)) {
      // Fork CI/Security runs and review signals can omit PR association metadata.
      // Revalidate every open PR without trusting a PR-written artifact.
      pullRequests = await github.paginate(github.rest.pulls.list, { owner, repo, state: 'open', per_page: 100 });
    }
  } else {
    if (!number) throw new Error('A pull-request number is required.');
    pullRequests = [{ number }];
  }
  // Discovery only selects PR numbers. Check creation and current-head reads
  // happen together inside the per-PR assessment lock.
  return [...new Set(pullRequests.map(pr => pr.number))].map(number => ({number}));
}

function bucketTargets(targets) {
  return [...new Set(targets.map(target => target.number % BUCKET_COUNT))].sort((a, b) => a - b);
}

async function runBucket({ github, context, bucket }) {
  if (!Number.isInteger(bucket) || bucket < 0 || bucket >= BUCKET_COUNT) throw new Error('Invalid review bucket.');
  const { owner, repo } = context.repo;
  // Refresh the whole stable bucket after taking its lock. A newer individual
  // event can replace a queued bulk job without dropping another PR's validation.
  const prs = await github.paginate(github.rest.pulls.list, { owner, repo, state: 'open', per_page: 100 });
  const failures = [];
  for (const pr of prs.filter(pr => pr.number % BUCKET_COUNT === bucket)) {
    try {
      await run({ github, context: { ...context, payload: { pull_request: { number: pr.number } } } });
    } catch (error) {
      failures.push(`#${pr.number}: ${error.message}`);
    }
  }
  if (failures.length) throw new Error(failures.join('\n'));
}

module.exports = { isRunForPR, targetReceiptFromArchive, fetchTargetReceipt, verifyApprovedDefinitionPaths, approvedDefinitionPaths, assess, run, preparePullRequests, fetchWorkflowRuns, bucketTargets, runBucket, affirmativeValidation, fetchCommitEvidence, relevantComments, relevantReviews, definitionMatches, metadata };
