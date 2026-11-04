#!/usr/bin/env python3
"""Write metadata.json and SHA256SUMS for a recorded run into pdr/evidence/<run>/.

Inputs: the rosbag2 folder (metadata.yaml + .mcap), the run's verify_mcap.py summary.json
(for the label and layout coverage) and pdr/evidence/environment.txt (versions).
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'pdr/evidence'
TOPIC_LIST = ROOT/'02_Ground_Station_Telemetry/src/lunabotics_telemetry/config/topics_to_record.txt'


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def versions(environment):
    found = {}
    if environment.is_file():
        for line in environment.read_text().splitlines():
            if '\t' in line:
                name, version = line.split('\t', 1)
                found[name] = version
            elif ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                found[key.strip()] = value.strip()
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('bag', type=Path, help='rosbag2 folder with metadata.yaml and .mcap')
    ap.add_argument('--evidence', type=Path, help='evidence folder (default pdr/evidence/<bag name>)')
    args = ap.parse_args()

    bag = args.bag.expanduser().resolve()
    out = args.evidence or EVIDENCE/bag.name
    info = yaml.safe_load((bag/'metadata.yaml').read_text())['rosbag2_bagfile_information']
    summary = json.loads((out/'summary.json').read_text())
    files = sorted(bag.glob('*.mcap'))
    expected = [t.strip() for t in TOPIC_LIST.read_text().splitlines() if t.strip()]
    counts = {t['topic_metadata']['name']: t['message_count'] for t in info['topics_with_message_count']}
    types = {t['topic_metadata']['name']: t['topic_metadata']['type'] for t in info['topics_with_message_count']}
    stamp = re.search(r'(\d{8})_(\d{6})', bag.name)
    started = (datetime.datetime.strptime(''.join(stamp.groups()), '%Y%m%d%H%M%S').isoformat()
               if stamp else None)

    metadata = {
        'run_id': bag.name,
        'date_local': started,
        'mode_label': summary['label'],
        'source': 'Gazebo simulation, HARDWARE_ENABLED=0' if summary['label'] == 'SIMULATION' else 'see label',
        'duration_s': info['duration']['nanoseconds']/1e9,
        'time_base': summary['recording_stats']['time_base'],
        'message_count_total': info['message_count'],
        'message_count_per_topic': dict(sorted(counts.items())),
        'topics': [{'topic': t, 'type': types[t]} for t in sorted(types)],
        'missing_topics': {
            'from_topics_to_record': [t for t in expected if counts.get(t, 0) == 0],
            'needed_by_layout': summary['layout_coverage']['missing'],
        },
        'storage_plugin': info['storage_identifier'],
        'rosbag2_bagfile_version': info.get('version'),
        'ros_distro': info.get('ros_distro'),
        'compression': info.get('compression_format') or 'none',
        'files': [{'name': f.name, 'bytes': f.stat().st_size, 'sha256': sha256(f)} for f in files],
        'versions': versions(EVIDENCE/'environment.txt'),
        'verification': {'tool': 'tools/verify_mcap.py', 'passed': summary['passed'],
                         'checks': summary['checks'], 'summary': 'summary.md'},
        'raw_data_location': 'see pdr/evidence_location.md (not in GitHub)',
    }
    (out/'metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(f"{f['sha256']}  {f['name']}\n" for f in metadata['files']))
    print(f"{out/'metadata.json'}\n{out/'SHA256SUMS'}")
    for f in metadata['files']:
        print(f"  {f['sha256']}  {f['name']}  ({f['bytes']} bytes)")


if __name__ == '__main__':
    main()
