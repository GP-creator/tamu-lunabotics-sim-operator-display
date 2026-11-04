#!/usr/bin/env python3
"""Check a LichtBlick layout: every topic is sim-available or documented rover-only, no orphans."""
import argparse
import csv
import difflib
import json
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
LICHTBLICK = ROOT/'02_Ground_Station_Telemetry/deliverables/lichtblick'
TOPICS_CSV = ROOT/'01_Interfaces_Communication/src/lunabotics_interfaces/config/topics.csv'
BRIDGE = ROOT/'01_Interfaces_Communication/src/lunabotics_interfaces/config/gazebo_bridge.yaml'
# Published by the static_transform_publisher nodes in simulation.launch.py.
LAUNCH_TOPICS = {'/tf_static'}
SCRIPT_PREFIX = '/studio_script/'
TOPIC_RE = re.compile(r'^(/[A-Za-z0-9_/]+?)(?:\.|$|\{|\[)')


def sim_topics():
    with TOPICS_CSV.open() as stream:
        names = {row['topic'] for row in csv.DictReader(stream)}
    names |= {entry['ros_topic_name'] for entry in yaml.safe_load(BRIDGE.read_text())}
    return names | LAUNCH_TOPICS


def rover_only_topics(path):
    names = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            names.add(line.split()[0])
    return names


def leaves(node):
    if node is None:
        return []
    if isinstance(node, str):
        return [node]
    return leaves(node.get('first')) + leaves(node.get('second'))


def topic_of(value):
    match = TOPIC_RE.match(value) if isinstance(value, str) else None
    return match.group(1) if match else None


def panel_topics(config):
    """Topics a panel reads, from the config keys LichtBlick 1.30.0 uses."""
    found = set()
    for key in ('path', 'topicPath'):
        if topic_of(config.get(key)):
            found.add(topic_of(config[key]))
    for item in config.get('paths', []):
        if topic_of(item.get('value')):
            found.add(topic_of(item['value']))
    image = config.get('imageMode', {})
    for key in ('imageTopic', 'calibrationTopic'):
        if image.get(key):
            found.add(image[key])
    found |= set(config.get('topics', {}))
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('layout', nargs='?', type=Path, default=LICHTBLICK/'lichtblick_layout.json')
    ap.add_argument('--rover-only', type=Path, default=LICHTBLICK/'rover_only_topics.txt')
    ap.add_argument('--known', type=Path, action='append', default=[],
                    help='extra topic list (same format as rover_only_topics.txt), labelled by file name')
    ap.add_argument('--no-sim', action='store_true',
                    help='do not treat simulation topics as available (e.g. for the GNC-2027 layout)')
    ap.add_argument('--json', type=Path, help='also write the report as JSON')
    args = ap.parse_args()

    layout = json.loads(args.layout.read_text())
    configs = layout['configById']
    sim, rover = (set() if args.no_sim else sim_topics()), rover_only_topics(args.rover_only)
    known = {path.stem: rover_only_topics(path) for path in args.known}

    def availability(topic):
        if topic in sim:
            return 'sim-available'
        if topic in rover:
            return 'rover-only'
        return next((f'in {label}' for label, names in known.items() if topic in names), 'UNKNOWN')
    problems = []

    placed = leaves(layout['layout'])
    for config in configs.values():
        for tab in config.get('tabs', []):
            placed += leaves(tab.get('layout'))
    for pid in sorted(set(configs) - set(placed)):
        problems.append(f'orphan panel config (not placed in layout): {pid}')
    for pid in sorted(set(placed) - set(configs)):
        problems.append(f'placed panel has no config: {pid}')

    scripts = {}
    for script in layout.get('userNodes', {}).values():
        code = script['sourceCode']
        inputs = json.loads(re.search(r'inputs\s*=\s*(\[[^\]]*\])', code).group(1))
        output = re.search(r'output\s*=\s*"([^"]+)"', code).group(1)
        scripts[output] = {'name': script['name'], 'inputs': inputs}

    rows, used_outputs = [], set()
    for pid, config in sorted(configs.items()):
        for topic in sorted(panel_topics(config)):
            if topic.startswith(SCRIPT_PREFIX):
                status = 'script output' if topic in scripts else 'NO SCRIPT PRODUCES THIS'
                used_outputs.add(topic)
            else:
                status = availability(topic)
            rows.append((pid, topic, status))
    for output, script in scripts.items():
        for topic in script['inputs']:
            status = availability(topic)
            rows.append((f"script:{script['name']}", topic, status))
        if output not in used_outputs:
            problems.append(f"script {script['name']} output {output} is not used by any panel")

    for where, topic, status in rows:
        if status in ('UNKNOWN', 'NO SCRIPT PRODUCES THIS'):
            candidates = sim | rover | set(scripts) | set().union(*known.values())
            near = difflib.get_close_matches(topic, sorted(candidates), n=1, cutoff=0.8)
            hint = f' (typo of {near[0]}?)' if near else ''
            problems.append(f'{where}: {topic} is {status}{hint}')

    width = max(len(r[0]) for r in rows)
    for where, topic, status in rows:
        print(f'{where:{width}}  {topic:40}  {status}')
    print()
    for problem in problems:
        print('PROBLEM:', problem)
    print('LAYOUT CHECK', 'FAIL' if problems else 'PASS',
          f'({len(configs)} panels, {len(scripts)} scripts, {len({r[1] for r in rows})} topics)')
    if args.json:
        args.json.write_text(json.dumps({
            'layout': str(args.layout.relative_to(ROOT)) if args.layout.is_relative_to(ROOT) else str(args.layout),
            'rows': [dict(zip(('panel', 'topic', 'status'), r)) for r in rows],
            'problems': problems, 'passed': not problems}, indent=2) + '\n')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
