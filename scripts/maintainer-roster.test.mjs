import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { validate, detectDrift, renderGate, resolvedTemplate } from './maintainer-roster.mjs';

const roster = JSON.parse(await fs.readFile(new URL('../maintainers/roster.json', import.meta.url), 'utf8'));
const template = await fs.readFile(new URL('../maintainers/gate-script.js.txt', import.meta.url), 'utf8');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const execute = new AsyncFunction('github', 'context', 'core', 'Buffer', template.replaceAll('__BOOTSTRAP_BASE__', JSON.stringify('initial-base')).replaceAll('__BOOTSTRAP_POLICY__', JSON.stringify({ schema: 1, repository: 'cmcp', maintainers: ['owner-a','owner-b'], security_paths: ['src/security/'], security_approvals: 2 })));
const policy = { schema: 1, repository: 'cmcp', maintainers: ['owner-a', 'owner-b'], security_paths: ['src/security/'], security_approvals: 2 };
const review = (login, state = 'APPROVED', commit = 'head', id = 1, type = 'User') =>
  ({ id, user: { login, type }, state, commit_id: commit, submitted_at: new Date(id * 1000).toISOString() });
async function run({ author = 'contributor', files = [], reviews = [], body = policy, count = files.length, error = false, missing = false, base = "reviewed-base", baseRef = 'main' } = {}) {
  const absent = ref => missing === true || (Array.isArray(missing) && missing.includes(ref));
  const denied = ref => error === true || (Array.isArray(error) && error.includes(ref));
  const failures = [], calls = [];
  const github = {
    rest: {
      pulls: {
        get: async () => ({ data: { number: 7, user: { login: author }, head: { sha: 'head' }, base: { sha: base, ref: baseRef }, changed_files: count } }),
        listFiles: 'files', listReviews: 'reviews',
      },
      repos: { getContent: async args => {
        calls.push(args);
        if (denied(args.ref)) throw Error('API denied');
        if (absent(args.ref)) throw Object.assign(Error('Not found'), {status:404});
        return { data: { encoding: 'base64', content: Buffer.from(JSON.stringify(body)).toString('base64') } };
      } },
    },
    paginate: async method => method === 'files' ? files : reviews,
  };
  await execute(github, { repo: { owner: 'agentrust-io', repo: 'cmcp' }, payload: { pull_request: { number: 7 } } },
    { setFailed: message => failures.push(message), info: () => {} }, Buffer);
  assert.equal(calls[0].ref, base);
  assert.equal(calls[0].path, '.github/maintainers.json');
  return Object.assign(failures, { calls });
}
test('canonical roster validates; self coverage, read access and weakened security fail', () => {
  validate(roster);
  for (const mutate of [
    r => { r.repositories.cmcp.backup = r.repositories.cmcp.primary; },
    r => { r.repositories.cmcp.observed_permissions[r.repositories.cmcp.primary] = 'read'; },
    r => { r.repositories.cmcp.policy.security_approvals = 1; },
  ]) {
    const changed = structuredClone(roster); mutate(changed);
    assert.throws(() => validate(changed));
  }
});
test('detects owner, gate and approval roster drift', () => {
  const entry = roster.repositories.cmcp;
  const gate = renderGate('name: gate\n          script: |\n            old\n', template, entry);
  const snapshot = { policy: entry.policy, codeowners: entry.codeowners, gate };
  assert.deepEqual(detectDrift(entry, snapshot, template), []);
  assert.equal(detectDrift(entry, { ...snapshot, policy: {} }, template).length, 1);
  assert.equal(detectDrift(entry, { ...snapshot, codeowners: '* @imran-siddique\n' }, template).length, 1);
  assert.equal(detectDrift(entry, { ...snapshot, gate: gate.replace('required : 1', 'required : 0') + 'changed' }, template).length, 1);
});
test('routine external PR needs one independent current-head human approval', async () => {
  assert.equal((await run()).length, 1);
  assert.equal((await run({ reviews: [review('owner-a')] })).length, 0);
  assert.equal((await run({ reviews: [review('owner-a', 'APPROVED', 'old')] })).length, 1);
  assert.equal((await run({ reviews: [review('owner-a', 'APPROVED', 'head', 1, 'Bot')] })).length, 1);
  assert.equal((await run({ reviews: [review('outsider')] })).length, 1);
});
test('dismissed or requested-changes review supersedes approval; comments do not', async () => {
  for (const state of ['DISMISSED', 'CHANGES_REQUESTED']) {
    assert.equal((await run({ reviews: [review('owner-a'), review('owner-a', state, 'head', 2)] })).length, 1);
  }
  assert.equal((await run({ reviews: [review('owner-a'), review('owner-a', 'COMMENTED', 'head', 2)] })).length, 0);
});
test('security changes require two distinct current-head maintainers', async () => {
  const files = [{ filename: 'src/security/check.py' }];
  assert.equal((await run({ files, reviews: [review('owner-a')] })).length, 1);
  assert.equal((await run({ files, reviews: [review('owner-a'), review('owner-a', 'APPROVED', 'head', 2)] })).length, 1);
  assert.equal((await run({ files, reviews: [review('owner-a'), review('owner-b', 'APPROVED', 'old', 2)] })).length, 1);
  assert.equal((await run({ files, reviews: [review('owner-a'), review('owner-b', 'APPROVED', 'head', 2)] })).length, 0);
});
test('security author cannot use routine author exemption or approve their own change', async () => {
  assert.equal((await run({ author: 'owner-a' })).length, 0);
  assert.equal((await run({ author: 'owner-a', files: [{ filename: 'src/security/key.py' }],
    reviews: [review('owner-a'), review('owner-b', 'APPROVED', 'head', 2)] })).length, 1);
});
test('rename out of security scope, including a file late in pagination, needs two reviews', async () => {
  const files = Array.from({ length: 31 }, (_, i) => ({ filename: 'docs/' + i + '.md' }));
  files.push({ filename: 'docs/moved.py', previous_filename: 'src/security/verify.py' });
  assert.equal((await run({ files, reviews: [review('owner-a')] })).length, 1);
});
test('missing, malformed and unavailable trusted policy fail closed; incomplete file inventory fails', async () => {
  await assert.rejects(run({ body: { ...policy, security_approvals: 1 } }), /Invalid/);
  await assert.rejects(run({ body: { ...policy, maintainers: ['owner-a', 'OWNER-A'] } }), /Invalid/);
  await assert.rejects(run({ error: true }), /API denied/);
  await assert.rejects(run({ files: [], count: 3001 }), /Incomplete/);
});

test('bootstrap is limited to its reviewed initial base; later missing policy fails closed', async () => {
  assert.equal((await run({missing:true,base:'initial-base',reviews:[review('owner-a')]})).length,0);
  await assert.rejects(run({missing:true,base:'reviewed-base'}), /Not found/);
});

test('a base from before the policy file reads the policy at the base branch tip', async () => {
  const old = { missing: ['old-base'], base: 'old-base' };
  const approved = await run({ ...old, reviews: [review('owner-a')] });
  assert.equal(approved.length, 0);
  assert.deepEqual(approved.calls.map(c => c.ref), ['old-base', 'refs/heads/main']);
  const other = await run({ missing: ['old-base'], base: 'old-base', baseRef: 'release', reviews: [review('owner-a')] });
  assert.deepEqual(other.calls.map(c => c.ref), ['old-base', 'refs/heads/release']);
  assert.equal((await run(old)).length, 1);
  assert.equal((await run({ ...old, reviews: [review('outsider')] })).length, 1);
  await assert.rejects(run({ ...old, body: { ...policy, security_approvals: 1 } }), /Invalid/);
  assert.equal((await run({ base: 'old-base', reviews: [review('owner-a')] })).calls.length, 1);
  await assert.rejects(run({ error: ['old-base'], base: 'old-base', reviews: [review('owner-a')] }), /API denied/);
});

test('the bootstrap list is used only when the base branch has no policy either', async () => {
  const body = { ...policy, maintainers: ['owner-c', 'owner-b'] };
  const initial = { missing: ['initial-base'], base: 'initial-base', body };
  assert.equal((await run({ ...initial, reviews: [review('owner-c')] })).length, 0);
  assert.equal((await run({ ...initial, reviews: [review('owner-a')] })).length, 1);
  await assert.rejects(run({ ...initial, error: ['refs/heads/main'], reviews: [review('owner-a')] }), /API denied/);
});

test('organization consumer matches canonical policy, owners and reviewed gate', async () => {
  const snapshot = {
    policy: JSON.parse(await fs.readFile(new URL('../.github/maintainers.json', import.meta.url), 'utf8')),
    codeowners: await fs.readFile(new URL('../.github/CODEOWNERS', import.meta.url), 'utf8'),
    gate: await fs.readFile(new URL('../.github/workflows/require-maintainer-approval.yml', import.meta.url), 'utf8'),
  };
  assert.deepEqual(detectDrift(roster.repositories['.github'], snapshot, template), []);
});
