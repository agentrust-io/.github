import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { isDeepStrictEqual } from 'node:util';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export function validate(roster) {
  if (roster.schema !== 1 || roster.organization !== 'agentrust-io') throw Error('Invalid roster identity');
  const login = x => typeof x === 'string' && /^[A-Za-z0-9-]+$/.test(x);
  if (!Array.isArray(roster.global_maintainers) || !roster.global_maintainers.every(login)) throw Error('Invalid global maintainers');
  if (!roster.repositories || !Object.keys(roster.repositories).length) throw Error('Empty repository roster');
  for (const [repo, entry] of Object.entries(roster.repositories)) {
    if (!/^[A-Za-z0-9_.-]+$/.test(repo) || repo === '..') throw Error('Invalid repository: ' + repo);
    if (!/^[0-9a-f]{40}$/.test(entry.bootstrap_base)) throw Error('Invalid bootstrap base: ' + repo);
    const p = entry.policy;
    if (p.schema !== 1 || p.repository !== repo || p.source !== 'agentrust-io/.github:maintainers/roster.json' ||
        !Array.isArray(p.maintainers) || p.maintainers.length < 2 || !p.maintainers.every(login) ||
        new Set(p.maintainers.map(x => x.toLowerCase())).size !== p.maintainers.length) throw Error('Invalid policy: ' + repo);
    if (!Array.isArray(p.security_paths) ||
        !p.security_paths.every(x => typeof x === 'string' && x.endsWith('/') && !x.startsWith('/') && !x.includes('..')) ||
        p.security_approvals !== (p.security_paths.length ? 2 : 1)) throw Error('Invalid security approvals: ' + repo);
    if (!login(entry.primary) || !login(entry.backup) || entry.primary === entry.backup ||
        entry.primary === 'imran-siddique' || entry.backup === 'imran-siddique' ||
        !p.maintainers.includes(entry.primary) || !p.maintainers.includes(entry.backup)) throw Error('Invalid independent coverage: ' + repo);
    for (const owner of [entry.primary, entry.backup]) {
      if (!['write', 'maintain', 'admin'].includes(entry.observed_permissions[owner])) throw Error('Unverified write access: ' + repo + '/' + owner);
    }
    if (typeof entry.codeowners !== 'string' || !entry.codeowners.includes('* @')) throw Error('Missing CODEOWNERS: ' + repo);
    if (entry.release.primary !== entry.primary || entry.release.backup !== entry.backup ||
        entry.release.publisher_access !== 'unverified') throw Error('Publisher evidence belongs in the handover record: ' + repo);
  }
  return roster;
}
export function resolvedTemplate(template, entry) {
  return template.replaceAll("__BOOTSTRAP_BASE__", JSON.stringify(entry.bootstrap_base))
    .replaceAll("__BOOTSTRAP_POLICY__", JSON.stringify(entry.policy));
}
export function renderGate(workflow, template, entry) {
  if (entry) template = resolvedTemplate(template, entry);
  const prefix = workflow.slice(0, workflow.indexOf('          script: |'));
  if (!prefix || !workflow.includes('          script: |')) throw Error('Unknown gate layout');
  return prefix + '          script: |\n' + template.trimEnd().split('\n').map(l => '            ' + l).join('\n') + '\n';
}
export function detectDrift(entry, snapshot, template) {
  template = resolvedTemplate(template, entry);
  const issues = [];
  if (!isDeepStrictEqual(entry.policy, snapshot.policy)) issues.push('maintainers.json differs from canonical roster');
  if (entry.codeowners !== snapshot.codeowners) issues.push('CODEOWNERS differs from canonical roster');
  if (entry.gate_enabled && (!snapshot.gate || !snapshot.gate.endsWith(
      '          script: |\n' + template.trimEnd().split('\n').map(l => '            ' + l).join('\n') + '\n'))) {
    issues.push('maintainer gate differs from reviewed template');
  }
  return issues;
}
async function readGitHub(repo, name) {
  const headers = { Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' };
  if (process.env.GITHUB_TOKEN) headers.Authorization = 'Bearer ' + process.env.GITHUB_TOKEN;
  const response = await fetch('https://api.github.com/repos/agentrust-io/' + repo + '/contents/' + name + '?ref=main', { headers });
  if (!response.ok) throw Error(repo + '/' + name + ': HTTP ' + response.status);
  const json = await response.json();
  if (json.encoding !== 'base64') throw Error('Unexpected encoding');
  return Buffer.from(json.content, 'base64').toString('utf8');
}
export async function main(args) {
  const roster = validate(JSON.parse(await fs.readFile(path.join(root, 'maintainers/roster.json'), 'utf8')));
  const template = await fs.readFile(path.join(root, 'maintainers/gate-script.js.txt'), 'utf8');
  if (args[0] === 'validate') {
    console.log('Validated independent coverage for ' + Object.keys(roster.repositories).length + ' repositories.');
  } else if (args[0] === 'render') {
    const destination = args[1];
    if (!destination) throw Error('render requires a destination directory');
    for (const [repo, entry] of Object.entries(roster.repositories)) {
      const dir = path.join(destination, repo, '.github');
      await fs.mkdir(dir, { recursive: true });
      await fs.writeFile(path.join(dir, 'maintainers.json'), JSON.stringify(entry.policy, null, 2) + '\n');
      await fs.writeFile(path.join(dir, 'CODEOWNERS'), entry.codeowners);
    }
    console.log('Rendered policy and CODEOWNERS snapshots. Use renderGate for an existing workflow.');
  } else if (args[0] === 'audit') {
    let drift = 0;
    console.log('# Maintainer coverage drift\n\nCanonical record: agentrust-io/.github/maintainers/roster.json\n');
    for (const [repo, entry] of Object.entries(roster.repositories)) {
      try {
        const [policy, codeowners, gate] = await Promise.all([
          readGitHub(repo, '.github/maintainers.json'), readGitHub(repo, '.github/CODEOWNERS'),
          entry.gate_enabled ? readGitHub(repo, '.github/workflows/require-maintainer-approval.yml') : null,
        ]);
        const issues = detectDrift(entry, { policy: JSON.parse(policy), codeowners, gate }, template);
        drift += issues.length;
        console.log('- ' + repo + ': ' + (issues.length ? issues.join('; ') : 'aligned') +
          '. Routing: ' + entry.primary + ' / ' + entry.backup +
          '. Capacity: ' + entry.capacity + '. Publisher: ' + entry.release.publisher_access + '.');
      } catch (error) {
        drift++;
        console.log('- ' + repo + ': unable to verify (' + error.message + ').');
      }
    }
    console.log('\nPrivate team membership, organization ownership, package owners and environment approvers require separate verification.');
    if (drift) process.exitCode = 1;
  } else {
    throw Error('Usage: node scripts/maintainer-roster.mjs validate|render DIR|audit');
  }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main(process.argv.slice(2));
}
