#!/usr/bin/env python3
"""Draw slide figures from the LichtBlick layout: annotated panel diagram and telemetry data path."""
import argparse
import csv
import json
from pathlib import Path
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_layout import LICHTBLICK, TOPICS_CSV, panel_topics  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXTRA_TYPES = {'/tf': 'tf2_msgs/msg/TFMessage', '/tf_static': 'tf2_msgs/msg/TFMessage'}
COLOURS = {'Indicator': '#ede7f6', '3D': '#e3f2fd', 'Image': '#e8f5e9', 'Plot': '#fff3e0',
           'StateTransitions': '#fce4ec'}


def topic_types():
    with TOPICS_CSV.open() as stream:
        types = {row['topic']: row['type'] for row in csv.DictReader(stream)}
    return types | EXTRA_TYPES


def geometry(node, x=0.0, y=0.0, w=1.0, h=1.0, out=None):
    out = [] if out is None else out
    if isinstance(node, str):
        out.append((node, x, y, w, h))
        return out
    p = node.get('splitPercentage', 50)/100
    if node['direction'] == 'row':
        geometry(node['first'], x, y, w*p, h, out)
        geometry(node['second'], x+w*p, y, w*(1-p), h, out)
    else:
        geometry(node['first'], x, y, w, h*p, out)
        geometry(node['second'], x, y+h*p, w, h*(1-p), out)
    return out


def describe(pid, config, layout, types):
    """Lines: panel type, then topic -> message type (scripts resolved to their ROS inputs)."""
    scripts = {}
    for script in layout.get('userNodes', {}).values():
        code = script['sourceCode']
        inputs = json.loads(re.search(r'inputs\s*=\s*(\[[^\]]*\])', code).group(1))
        scripts[re.search(r'output\s*=\s*"([^"]+)"', code).group(1)] = (script['name'], inputs)
    if str(config.get('path', '')).rsplit('.', 1)[-1] in ('battery', 'estop', 'faults'):
        return ['no input topic → UNAVAILABLE']
    lines = []
    for topic in sorted(panel_topics(config)):
        if topic in scripts:
            name, inputs = scripts[topic]
            lines.append(f'script {name} ←')
            lines += [f'  {t} → {types.get(t, "?").split("/")[-1]}' for t in inputs]
        else:
            lines.append(f'{topic} → {types.get(topic, "?").split("/")[-1]}')
    return list(dict.fromkeys(lines))


def layout_figure(layout_path, out):
    layout = json.loads(Path(layout_path).read_text())
    configs = layout['configById']
    operator = configs['Tab!main']['tabs'][0]['layout'] if 'Tab!main' in configs else layout['layout']
    types = topic_types()
    plt.rcParams.update({'font.family': 'DejaVu Sans'})
    fig = plt.figure(figsize=(13.333, 7.5), dpi=150)
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.9])
    ax.set_xlim(0, 1)
    ax.set_ylim(1, 0)
    ax.axis('off')
    for pid, x, y, w, h in geometry(operator):
        kind = pid.split('!')[0]
        config = configs[pid]
        ax.add_patch(FancyBboxPatch((x+0.003, y+0.004), w-0.006, h-0.008,
                                    boxstyle='round,pad=0,rounding_size=0.006',
                                    facecolor=COLOURS.get(kind, '#f5f5f5'), edgecolor='#455a64', linewidth=1.2))
        title = config.get('lichtblickPanelTitle', pid.split('!')[1])
        size = 9.5 if h > 0.12 else 7.5
        limit = int(w*(148 if size > 9 else 205))-len(kind)-2  # keep titles inside narrow boxes
        if len(title) > limit:
            title = title[:max(limit-1, 4)].rstrip(' :(')+'…'
        ax.text(x+0.008, y+0.012, f'{kind}: {title}', fontsize=size, fontweight='bold', va='top',
                wrap=True, clip_on=True)
        if h > 0.09:
            body = describe(pid, config, layout, types)
            ax.text(x+0.008, y+0.012+0.035*(size/9.5), '\n'.join(body[:8]), fontsize=size-1.5,
                    va='top', family='DejaVu Sans Mono', clip_on=True, linespacing=1.25)
        else:
            body = describe(pid, config, layout, types)
            ax.text(x+0.008, y+h-0.012, body[0] if body else '', fontsize=6.5, va='bottom',
                    family='DejaVu Sans Mono', clip_on=True)
    fig.suptitle('LichtBlick operator layout (Operator tab): panel type → topic → message type',
                 fontsize=17, fontweight='bold', y=0.975)
    fig.text(0.99, 0.925, 'Source: lichtblick_layout.json · LichtBlick 1.30.0 · topics: SIMULATION',
             ha='right', fontsize=10, color='#455a64')
    fig.savefig(out, facecolor='white')
    plt.close(fig)


def data_path_figure(out):
    fig = plt.figure(figsize=(13.333, 7.5), dpi=150)
    ax = fig.add_axes([0, 0, 1, 0.9])
    ax.set_xlim(0, 13.333)
    ax.set_ylim(0, 6.6)
    ax.axis('off')

    def box(x, y, text, colour, w=2.2, h=1.25):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.05,rounding_size=0.12',
                                    facecolor=colour, edgecolor='#37474f', linewidth=1.6))
        ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=12.5, linespacing=1.35)
        return x, y, w, h

    def arrow(a, b, label=''):
        ax.annotate('', xy=(b[0], b[1]+b[3]/2), xytext=(a[0]+a[2], a[1]+a[3]/2),
                    arrowprops=dict(arrowstyle='-|>', lw=2.2, color='#37474f'))
        if label:
            ax.text((a[0]+a[2]+b[0])/2, a[1]+a[3]+0.12, label, ha='center', va='bottom',
                    fontsize=10.5, color='#263238')

    live_y, rec_y = 3.9, 1.0
    gz = box(0.2, live_y, 'Gazebo Harmonic\narena + sensors\n(LiDAR, camera, IMU)', '#e3f2fd')
    br = box(2.95, live_y, 'ros_gz_bridge\nparameter_bridge', '#e3f2fd')
    ros = box(5.7, live_y, 'ROS 2 Jazzy\ndomain 84, /sim/*\n+ navigator, TF', '#e8f5e9')
    rb = box(8.45, live_y, 'rosbridge_server\nws://localhost:9090', '#fff3e0')
    lb = box(11.2, live_y, 'LichtBlick 1.30.0\nlive (Rosbridge)', '#ede7f6', w=1.95)
    arrow(gz, br, 'gz topics')
    arrow(br, ros, 'ROS msgs')
    arrow(ros, rb, 'subscribe')
    arrow(rb, lb, 'CBOR over WS')
    rec = box(5.7, rec_y, 'ros2 bag record\n(record_simulation.sh)', '#e8f5e9')
    mc = box(8.45, rec_y, 'MCAP file\nSIMULATED_*.mcap', '#fff3e0')
    lr = box(11.2, rec_y, 'LichtBlick 1.30.0\nreplay (open file)', '#ede7f6', w=1.95)
    ax.annotate('', xy=(rec[0]+rec[2]/2, rec[1]+rec[3]), xytext=(ros[0]+ros[2]/2, ros[1]),
                arrowprops=dict(arrowstyle='-|>', lw=2.2, color='#37474f'))
    ax.text(ros[0]+ros[2]/2+0.12, (rec[1]+rec[3]+ros[1])/2, 'topics_to_record.txt', fontsize=10.5)
    arrow(rec, mc, 'write')
    arrow(mc, lr, 'offline, no ROS')
    ax.text(0.25, live_y+1.75, 'LIVE', fontsize=15, fontweight='bold', color='#1565c0')
    ax.text(0.25, rec_y+1.75, 'RECORD / REPLAY', fontsize=15, fontweight='bold', color='#2e7d32')
    ax.text(0.25, 0.25, 'All data shown: SIMULATION (HARDWARE_ENABLED=0). Display only: no command path to any rover.',
            fontsize=11, color='#455a64')
    fig.suptitle('Telemetry data path: live and replay', fontsize=18, fontweight='bold', y=0.965)
    fig.savefig(out, facecolor='white')
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--layout', default=str(LICHTBLICK/'lichtblick_layout.json'))
    ap.add_argument('--out-dir', type=Path, default=ROOT/'pdr/figures')
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    layout_figure(args.layout, args.out_dir/'layout_diagram.png')
    data_path_figure(args.out_dir/'data_path.png')
    print('wrote', args.out_dir/'layout_diagram.png', 'and', args.out_dir/'data_path.png')


if __name__ == '__main__':
    main()
