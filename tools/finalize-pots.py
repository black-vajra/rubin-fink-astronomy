#!/usr/bin/env python3
"""Capture and publish this explicitly authorized November 20 astronomy closeout.

Uses the existing Pots gh login. Large/raw scientific data and delivery ZIPs are
release assets; their manifests are committed. No credential files are selected.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'black-vajra/rubin-fink-astronomy'
DELIVERIES = [
    'rubin-historical-2026.zip', 'rubin-fink-astronomy-start.zip',
    'rubin-extragalactic-update.zip', 'rubin-journal-c.zip',
    'rubin-qy297-update.zip', 'rubin-physical-orbit-update.zip',
    'rubin-research-finalize-2026-11-20.zip',
]


def run(*cmd, capture=False, check=True):
    return subprocess.run(list(map(str, cmd)), cwd=ROOT, check=check,
                          text=True, capture_output=capture)


def output(*cmd):
    return run(*cmd, capture=True).stdout.strip()


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def remote_assets(release):
    pages = json.loads(output('gh', 'api', '--paginate', '--slurp',
        f"repos/{REPOSITORY}/releases/{release['id']}/assets?per_page=100"))
    return {asset['name']: asset for page in pages for asset in page}


def commit_if_changed(message):
    if run('git', 'diff', '--cached', '--quiet', check=False).returncode:
        run('git', 'commit', '-m', message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared-commit', required=True)
    args = parser.parse_args()
    if output('git', 'branch', '--show-current') != 'main':
        raise SystemExit('Run in the main checkout; no branch/reset operations are performed.')
    if output('git', 'remote', 'get-url', 'origin').removesuffix('.git').rstrip('/') not in (
        f'https://github.com/{REPOSITORY}', f'git@github.com:{REPOSITORY}'):
        raise SystemExit('Unexpected origin; refusing to publish to another repository.')
    run('gh', 'auth', 'status', '--hostname', 'github.com')
    user = json.loads(output('gh', 'api', 'user'))
    if not run('git', 'config', 'user.name', capture=True, check=False).stdout.strip():
        run('git', 'config', 'user.name', user['login'])
    if not run('git', 'config', 'user.email', capture=True, check=False).stdout.strip():
        run('git', 'config', 'user.email', f"{user['id']}+{user['login']}@users.noreply.github.com")
    state_dir = ROOT/'.release-assets'/('finalize-'+args.prepared_commit[:12])
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir/'state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    if state.get('complete'):
        print('This closeout already completed:', state['release_url'])
        return
    if not state.get('capture_manifest'):
        before = set((ROOT/'data/manifests').glob('pots-capture-*.json'))
        run(sys.executable, ROOT/'tools/capture-pots.py', '--include-large-data')
        added = set((ROOT/'data/manifests').glob('pots-capture-*.json'))-before
        if len(added) != 1:
            raise SystemExit('Expected exactly one new capture manifest.')
        manifest = added.pop()
        state['capture_manifest'] = str(manifest.relative_to(ROOT))
        state['tag'] = 'research-archive-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        save(state_path, state)
    manifest = ROOT/state['capture_manifest']
    captured = json.loads(manifest.read_text())
    tag = state['tag']
    assets = [ROOT/r['path'] for r in captured['release_parts']]
    delivery_rows = []
    for name in DELIVERIES:
        path = Path.home()/'Downloads'/name
        if path.is_file():
            delivery_rows.append({'name': name, 'bytes': path.stat().st_size,
                                  'sha256': digest(path), 'source': str(path), 'status': 'selected'})
            assets.append(path)
        else:
            delivery_rows.append({'name': name, 'status': 'not present in Downloads'})
    delivery_manifest = ROOT/'data/manifests'/f'deliveries-{tag}.json'
    save(delivery_manifest, {'files': delivery_rows, 'archive_tag': tag})
    assets += [manifest, delivery_manifest]
    if len({p.name for p in assets}) != len(assets):
        raise SystemExit('Duplicate release asset filenames; no overwrite attempted.')
    # Verify the research tree before staging it. Release assets are intentionally ignored.
    run(sys.executable, ROOT/'tools/verify_archive.py')
    run('git', 'add', '--', 'archive/hosts/pots', 'data/manifests', 'reports',
        'evaluations', 'journal', 'docs', 'config', 'tools', 'requirements.txt', 'README.md')
    commit_if_changed('Archive November 20 Pots downloads, reports, tests and journal g')
    data_commit = output('git', 'rev-parse', 'HEAD')
    run('git', 'push', 'origin', 'HEAD:main')
    notes = state_dir/'release-notes.md'
    notes.write_text('November 20 astronomy closeout: allowlisted Pots research capture and delivery downloads. '
                     'Large/raw data are split tar.gz stream parts. Concatenate part-*.bin in filename order '
                     'to reconstruct the archive. SHA-256 manifests are committed and attached. '
                     'SQLite files were captured with the SQLite backup API. Scientific limitations remain in journal g.\n')
    if run('gh', 'release', 'view', tag, '--repo', REPOSITORY, capture=True, check=False).returncode:
        run('gh', 'release', 'create', tag, '--repo', REPOSITORY, '--target', data_commit,
            '--title', 'Rubin research archive · November 20, 2026', '--notes-file', notes)
    release = json.loads(output('gh', 'api', f'repos/{REPOSITORY}/releases/tags/{tag}'))
    remote = remote_assets(release)
    local = []
    for asset in assets:
        expected = {'name': asset.name, 'bytes': asset.stat().st_size, 'sha256': digest(asset)}
        if asset.name not in remote:
            run('gh', 'release', 'upload', tag, asset, '--repo', REPOSITORY)
        local.append(expected)
    release = json.loads(output('gh', 'api', f'repos/{REPOSITORY}/releases/tags/{tag}'))
    remote = remote_assets(release)
    receipt_assets = []
    for expected in local:
        actual = remote.get(expected['name'])
        if actual is None or actual['size'] != expected['bytes']:
            raise SystemExit('Release asset missing or wrong size: '+expected['name'])
        remote_digest = actual.get('digest')
        if remote_digest and remote_digest != 'sha256:'+expected['sha256']:
            raise SystemExit('Release checksum mismatch: '+expected['name'])
        receipt_assets.append({**expected, 'url': actual['browser_download_url'],
                               'remote_digest': remote_digest,
                               'verification': 'sha256 and size' if remote_digest else 'size; local SHA-256 retained'})
    receipt_path = ROOT/'data/manifests'/f'publication-{tag}.json'
    save(receipt_path, {'verified_UTC': datetime.now(timezone.utc).isoformat(),
         'repository': REPOSITORY, 'release_url': release['html_url'],
         'data_commit': data_commit, 'assets': receipt_assets})
    journal = ROOT/'journal/2026/11/2026-11-20g-rubin-journal.md'
    journal.write_text(journal.read_text()+f'\n## Verified Pots publication\n\n'
        f'The authenticated finalizer pushed research commit `{data_commit}`, uploaded and verified '
        f'{len(receipt_assets)} release assets, and recorded publication receipt '
        f'`{receipt_path.relative_to(ROOT)}`. Release: {release["html_url"]}. '
        'Remote checksums were checked when supplied by GitHub; otherwise asset size was checked '
        'and the local SHA-256 retained. Missing download filenames and absent source roots are listed '
        'in the capture manifests rather than silently declared archived.\n')
    run('git', 'add', '--', journal.relative_to(ROOT), receipt_path.relative_to(ROOT))
    commit_if_changed('Record verified November 20 release assets and journal g publication')
    run('git', 'push', 'origin', 'HEAD:main')
    head = output('git', 'rev-parse', 'HEAD')
    if output('git', 'ls-remote', 'origin', 'refs/heads/main').split()[0] != head:
        raise SystemExit('Remote main verification failed.')
    state.update(complete=True, release_url=release['html_url'], final_commit=head)
    save(state_path, state)
    print(f'Published and verified {REPOSITORY} main {head[:12]}.')
    print('Release:', release['html_url'])


if __name__ == '__main__':
    main()
