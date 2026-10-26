#!/usr/bin/env python3
"""Download the reviewed LichtBlick release and verify its SHA-256."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=['windows','linux-amd64','linux-arm64'])
    parser.add_argument('--output', type=Path, default=Path.home()/'Downloads')
    args = parser.parse_args()
    target = args.platform or ('windows' if platform.system() == 'Windows' else
                              'linux-arm64' if platform.machine() in ('aarch64','arm64')
                              else 'linux-amd64')
    lock = json.loads((ROOT/'MAIN/dependency-lock.json').read_text())
    ending = {'windows':'win.exe','linux-amd64':'linux-amd64.deb',
              'linux-arm64':'linux-arm64.deb'}[target]
    asset = next(a for a in lock['lichtblick']['assets'] if a['name'].endswith(ending))
    args.output.mkdir(parents=True, exist_ok=True)
    destination = args.output/asset['name']
    def checksum(path):
        h = hashlib.sha256()
        with path.open('rb') as stream:
            while block := stream.read(1024*1024): h.update(block)
        return h.hexdigest()
    if destination.exists() and checksum(destination) == asset['sha256']:
        print('Already verified:', destination)
        return
    temporary = destination.with_suffix(destination.suffix+'.partial')
    try:
        with urllib.request.urlopen(asset['url'], timeout=60) as response, temporary.open('wb') as stream:
            while block := response.read(1024*1024): stream.write(block)
        if temporary.stat().st_size != asset['bytes'] or checksum(temporary) != asset['sha256']:
            raise ValueError('Downloaded installer size or SHA-256 mismatch')
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    print('Downloaded and verified:', destination)


if __name__ == '__main__': main()
