const { spawnSync } = require('node:child_process');
const { run, fetchWorkflowRuns, metadata } = require('./review-gate.cjs');
const policy = require('../review-gate-policy.json');

function assertTrustedPolicy({ repository, protection, ruleset, policy }) {
  if (!repository.permissions?.admin) throw new Error('The authenticated merger must be a repository administrator.');
  if (!protection.enforce_admins?.enabled || !protection.required_conversation_resolution?.enabled) throw new Error('Native protections must apply to administrators and unresolved conversations.');
  if (!protection.required_status_checks?.checks?.some(check => check.context === 'review-evidence' && check.app_id === policy.publisher_app_id)) throw new Error('review-evidence must require the dedicated publisher App.');
  const actors = ruleset.bypass_actors || [];
  if (ruleset.enforcement !== 'active' || ruleset.conditions?.ref_name?.include?.join() !== 'refs/heads/main' || ruleset.conditions?.ref_name?.exclude?.length ||
      ruleset.rules?.length !== 1 || ruleset.rules[0].type !== 'update' || ruleset.rules[0].parameters?.update_allows_fetch_and_merge ||
      actors.length !== 1 || actors[0].actor_type !== 'RepositoryRole' || actors[0].actor_id !== 5 || actors[0].bypass_mode !== 'pull_request') {
    throw new Error('Main updates must be restricted to administrator PR merges.');
  }
}

function assertAppCheck(checks, appId) {
  const latest = checks.filter(check => check.name === 'review-evidence' && check.app?.id === appId).sort((a, b) => b.id - a.id)[0];
  if (!latest || latest.status !== 'completed' || latest.conclusion !== 'success') throw new Error('The latest dedicated App check is not successful.');
}

function assertCI(runs, workflows, head) {
  const activity = candidate => Date.parse(candidate.updated_at || candidate.run_started_at || candidate.created_at) || 0;
  for (const workflow of Object.values(workflows)) {
    const matching = runs.filter(candidate => candidate.workflow_id === workflow.id && candidate.head_sha === head &&
      typeof candidate.path === 'string' && candidate.path.split('@', 1)[0] === workflow.path);
    for (const event of ['pull_request', 'push']) {
      const candidates = matching.filter(candidate => candidate.event === event);
      if (event === 'push' && !candidates.length) continue;
      const latest = candidates.sort((a, b) => activity(b) - activity(a) || b.id - a.id)[0];
      if (!latest || latest.status !== 'completed' || latest.conclusion !== 'success' || candidates.some(candidate => candidate.status !== 'completed')) {
        throw new Error('Latest final-head CI and Security runs must be successful with no active runs.');
      }
    }
  }
}

async function mergeReviewedPR({ github, context, number, api, merge, validate = run, policy: selectedPolicy = policy }) {
  const {owner, repo} = context.repo;
  const [{data: repository}, protection, ruleset, {data: pr}] = await Promise.all([
    github.rest.repos.get({owner, repo}), api(`branches/main/protection`), api(`rulesets/${selectedPolicy.trusted_mergers_ruleset_id}`),
    github.rest.pulls.get({owner, repo, pull_number: number})
  ]);
  if (pr.state !== 'open' || pr.base?.ref !== 'main') throw new Error('An open PR targeting main is required.');
  assertTrustedPolicy({repository, protection, ruleset, policy: selectedPolicy});
  const head = pr.head.sha;
  assertAppCheck((await api(`commits/${head}/check-runs?per_page=100`, 'check_runs')), selectedPolicy.publisher_app_id);
  // Read-only assessment reuses the publisher's collection and stability checks.
  // These local callbacks never create or impersonate a public check run.
  let approvedUpdates = '';
  try { approvedUpdates = (await api('environments/review-evidence-publisher/variables/REVIEW_GATE_APPROVED_UPDATES'))?.value || ''; }
  catch (error) { if (error.status !== 404) throw error; }
  let result;
  const liveGithub = {...github, rest: {...github.rest, checks: {
    create: async () => ({data: {id: 0}}), update: async update => {result = update;}
  }}};
  await validate({github: liveGithub, context: {...context, payload: {pull_request: {number}}}, approvedUpdates});
  if (result?.conclusion !== 'success') throw new Error('Live review evidence did not pass.');
  const {workflows} = await metadata({github: liveGithub, owner, repo});
  const {data} = await fetchWorkflowRuns({github: liveGithub, owner, repo, head, workflows: Object.values(workflows)});
  assertCI(data.workflow_runs, workflows, head);
  const {data: current} = await github.rest.pulls.get({owner, repo, pull_number: number});
  if (current.state !== 'open' || current.head.sha !== head) throw new Error('PR head moved during pre-merge validation.');
  assertAppCheck(await api(`commits/${head}/check-runs?per_page=100`, 'check_runs'), selectedPolicy.publisher_app_id);
  if (approvedUpdates && (await api('environments/review-evidence-publisher/variables/REVIEW_GATE_APPROVED_UPDATES'))?.value !== approvedUpdates) throw new Error('Protected update approval changed during validation.');
  // Repeat mutable evidence collection after CI, check-source and approval reads.
  result = undefined;
  await validate({github: liveGithub, context: {...context, payload: {pull_request: {number}}}, approvedUpdates});
  if (result?.conclusion !== 'success') throw new Error('Final live review evidence did not pass.');
  const {data: finalPR} = await github.rest.pulls.get({owner, repo, pull_number: number});
  if (finalPR.state !== 'open' || finalPR.head.sha !== head) throw new Error('PR head moved during final live validation.');
  if (merge) await merge(head);
  return head;
}

function ghJson(args, input) {
  const result = spawnSync('gh', args, {input, encoding: 'utf8', timeout: 60000});
  if (result.error || result.status !== 0) {
    const error = new Error(result.stderr?.trim() || result.error?.message || 'gh failed');
    const status = result.stderr?.match(/\(HTTP (\d{3})\)/);
    if (status) error.status = Number(status[1]);
    throw error;
  }
  return result.stdout.trim() ? JSON.parse(result.stdout) : null;
}

function createGhAdapter(fullName, execute = ghJson) {
  const root = `repos/${fullName}`;
  const request = async (suffix, params = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== undefined));
    return {data: execute(['api', `${root}${suffix ? `/${suffix}` : ''}${query.size ? `?${query}` : ''}`])};
  };
  const github = {rest: {
    repos: {get: () => request(''), getBranch: ({branch}) => request(`branches/${encodeURIComponent(branch)}`), compareCommitsWithBasehead: ({basehead}) => request(`compare/${encodeURIComponent(basehead)}`)},
    pulls: {get: ({pull_number}) => request(`pulls/${pull_number}`),
      list: ({state, page, per_page}) => request('pulls', {state, page, per_page}),
      listReviews: ({pull_number, page, per_page}) => request(`pulls/${pull_number}/reviews`, {page, per_page})},
    issues: {listComments: ({issue_number, page, per_page}) => request(`issues/${issue_number}/comments`, {page, per_page})},
    actions: {getWorkflow: ({workflow_id}) => request(`actions/workflows/${encodeURIComponent(workflow_id)}`),
      listWorkflowRuns: ({workflow_id, head_sha, page, per_page}) => request(`actions/workflows/${encodeURIComponent(workflow_id)}/runs`, {head_sha, page, per_page})}
  }, graphql: async (query, variables) => execute(['api', 'graphql', '--input', '-'], JSON.stringify({query, variables})).data,
  paginate: async (method, params) => {
    const values = [];
    for (let page = 1; ; page++) {
      const {data} = await method({...params, page});
      if (!Array.isArray(data)) throw new Error('Unexpected paginated response.');
      values.push(...data); if (data.length < params.per_page) return values;
    }
  }};
  const api = async (suffix, listField) => {
    if (!listField) return (await request(suffix)).data;
    const values = [];
    for (let page = 1; ; page++) {
      const {data} = await request(`${suffix}&page=${page}`);
      const rows = data[listField];
      if (!Array.isArray(rows)) throw new Error('Unexpected check response.');
      values.push(...rows); if (rows.length < 100) return values;
    }
  };
  return {github, api};
}

if (require.main === module) {
  (async () => {
    const args = process.argv.slice(2);
    const fullName = args[args.indexOf('--repo') + 1];
    const number = Number(args[args.indexOf('--pr') + 1]);
    if (!args.includes('--repo') || !args.includes('--pr') || !/^[\w.-]+\/[\w.-]+$/.test(fullName) || !Number.isInteger(number) || number <= 0) throw new Error('Usage: node merge-reviewed-pr.cjs --repo OWNER/REPO --pr NUMBER [--merge]');
    const [owner, repo] = fullName.split('/');
    const {github, api} = createGhAdapter(fullName);
    const merge = args.includes('--merge') ? async head => {
      const result = spawnSync('gh', ['pr', 'merge', String(number), '--repo', fullName, '--squash', '--match-head-commit', head], {encoding: 'utf8', timeout: 60000});
      if (result.error || result.status !== 0) throw new Error(result.stderr?.trim() || result.error?.message || 'Merge failed');
    } : undefined;
    const head = await mergeReviewedPR({github, context: {repo: {owner, repo}}, number, api, merge});
    console.log(`${args.includes('--merge') ? 'Merged' : 'Validated'} #${number} at ${head}.`);
  })().catch(error => {console.error(error.message); process.exitCode = 1;});
}
module.exports = {assertTrustedPolicy, assertAppCheck, assertCI, mergeReviewedPR, createGhAdapter};
