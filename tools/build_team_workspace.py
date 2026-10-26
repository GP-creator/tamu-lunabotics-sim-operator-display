#!/usr/bin/env python3
"""Build only the selected team's packages, without discovering old backups."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def configuration(root=ROOT):
    return json.loads((root/'MAIN/profiles.json').read_text())


def prepare(profile, workspace, root=ROOT):
    cfg = configuration(root)
    selected = cfg['profiles'][profile]
    root = root.resolve()
    workspace = workspace.expanduser().resolve()
    if workspace == root or root in workspace.parents:
        raise ValueError('Build workspace must be outside the source download')
    src = workspace/'src'
    if src.is_symlink(): raise ValueError('Workspace src cannot be a symlink')
    if src.exists() and set(p.name for p in src.iterdir())-set(selected):
        raise ValueError('Use an empty workspace or the same team profile')
    src.mkdir(parents=True, exist_ok=True)
    for name in selected:
        source = (root/cfg['package_paths'][name]).resolve()
        if not source.is_relative_to(root) or not (source/'package.xml').is_file():
            raise ValueError('Missing or invalid source package: '+name)
        target = src/name
        if target.is_symlink() and target.resolve() == source: continue
        if target.exists() or target.is_symlink():
            raise ValueError('Refusing to overwrite '+str(target))
        target.symlink_to(source, target_is_directory=True)
    return workspace, selected


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('profile', choices=configuration()['profiles'])
    ap.add_argument('--workspace', type=Path)
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args()
    workspace = args.workspace or Path.home()/('lunabotics_'+args.profile+'_ws')
    selected = configuration()['profiles'][args.profile]
    command = ['colcon','build','--symlink-install','--base-paths',
               *['src/'+name for name in selected], '--packages-select',*selected]
    print('Workspace:', workspace)
    print(' '.join(command))
    if args.execute:
        workspace, _ = prepare(args.profile, workspace)
        raise SystemExit(subprocess.call(command, cwd=workspace))


if __name__ == '__main__': main()
