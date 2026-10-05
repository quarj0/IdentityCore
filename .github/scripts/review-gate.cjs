function assess({ head, reviewer, reviews, comments, threads, commits, runs }) {
  const isReviewer = author => author?.login === reviewer || author?.login === `${reviewer}[bot]`;
  const finalReviews = reviews.filter(r => isReviewer(r.user) && r.commit_id === head);
  const latestReview = finalReviews.at(-1);
  const blockingReview = latestReview && ['CHANGES_REQUESTED', 'PENDING', 'DISMISSED'].includes(latestReview.state);
  const reviewed = !blockingReview && (reviews.some(r => isReviewer(r.user) && r.commit_id === head && ['APPROVED', 'COMMENTED'].includes(r.state)) ||
    comments.some(c => isReviewer(c.user) && [...c.body.matchAll(/\*\*Reviewed commit:\*\*\s*`([0-9a-f]{10,40})`/g)].some(m => head.startsWith(m[1]))));
  const problems = [];
  for (const name of ['CI', 'Security']) {
    const latest = runs.filter(r => r.name === name && r.head_sha === head && r.event === 'pull_request')
      .sort((a, b) => b.id - a.id)[0];
    if (!latest || latest.status !== 'completed' || latest.conclusion !== 'success') problems.push(`${name} has not passed for the final head.`);
  }
  if (!reviewed) problems.push(`Configured review has not completed for ${head}.`);
  for (const thread of threads) {
    if (!thread.isResolved) {
      problems.push(`Unresolved thread ${thread.id}.`);
      continue;
    }
    const evidence = thread.comments.nodes.slice(1).some(c =>
      c.author?.login === thread.resolvedBy?.login &&
      /\b(test|tests|validation|regression|passed|passes|superseded|inapplicable)\b/i.test(c.body) &&
      [...c.body.matchAll(/\b([0-9a-f]{7,40})\b/g)].some(m => commits.some(sha => sha.startsWith(m[1])))
    );
    if (!evidence) problems.push(`Resolved thread ${thread.id} has no fixing-commit and validation evidence from its resolver.`);
  }
  return problems;
}

async function run({ github, context }) {
  const { owner, repo } = context.repo;
  const number = context.payload.pull_request?.number ||
    (context.payload.issue?.pull_request ? context.payload.issue.number : undefined) ||
    context.payload.workflow_run?.pull_requests?.[0]?.number ||
    Number(context.payload.inputs?.pr_number);
  if (!number) throw new Error('A pull-request number is required.');
  const { data: pr } = await github.rest.pulls.get({ owner, repo, pull_number: number });
  if (pr.state !== 'open') return;
  const head = pr.head.sha;
  const reviews = await github.paginate(github.rest.pulls.listReviews, { owner, repo, pull_number: number, per_page: 100 });
  const comments = await github.paginate(github.rest.issues.listComments, { owner, repo, issue_number: number, per_page: 100 });
  const commits = (await github.paginate(github.rest.pulls.listCommits, { owner, repo, pull_number: number, per_page: 100 })).map(c => c.sha);
  const threads = [];
  let cursor = null;
  do {
    const data = await github.graphql(`query($owner:String!,$repo:String!,$number:Int!,$cursor:String) {
      repository(owner:$owner,name:$repo) { pullRequest(number:$number) {
        reviewThreads(first:100,after:$cursor) { pageInfo { hasNextPage endCursor }
          nodes { id isResolved resolvedBy { login } comments(first:100) { nodes { body author { login } } pageInfo { hasNextPage } } }
        }
      } }
    }`, { owner, repo, number, cursor });
    const page = data.repository.pullRequest.reviewThreads;
    threads.push(...page.nodes);
    cursor = page.pageInfo.hasNextPage ? page.pageInfo.endCursor : null;
  } while (cursor);
  const { data: workflowRuns } = await github.rest.actions.listWorkflowRunsForRepo({ owner, repo, head_sha: head, per_page: 100 });
  const problems = assess({ head, runs: workflowRuns.workflow_runs, reviewer: 'chatgpt-codex-connector', reviews, comments, threads, commits });
  if (threads.some(t => t.comments.pageInfo.hasNextPage)) problems.push('A thread exceeds the evidence page limit; review it explicitly.');
  const { data: current } = await github.rest.pulls.get({ owner, repo, pull_number: number });
  if (current.head.sha !== head) problems.push('Pull-request head moved during validation; rerun against its current head.');
  await github.rest.checks.create({ owner, repo, head_sha: head, name: 'review-evidence', status: 'completed',
    conclusion: problems.length ? 'failure' : 'success',
    output: { title: problems.length ? 'Review evidence incomplete' : 'Final-head review evidence verified',
      summary: problems.length ? problems.join('\n') : `Configured review completed for ${head}; every thread has commit and validation evidence.` }
  });
  if (problems.length) throw new Error(problems.join('\n'));
}

module.exports = { assess, run };
