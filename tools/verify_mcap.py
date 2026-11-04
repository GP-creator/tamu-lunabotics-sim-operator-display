#!/usr/bin/env python3
"""Verify any ROS 2 MCAP recording and write PDR evidence: summary.json/.md and PNG plots.

Works on simulation, replay and real-rover recordings. Needs the `mcap` and
`mcap-ros2-support` packages (see pdr/README.md); the optional replay-parity check also needs ROS 2.

  python3 tools/verify_mcap.py RECORDING --label SIMULATION [--resources resources.csv]
          [--rosbridge-bandwidth rosbridge_bandwidth.json] [--replay-parity]
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))

LABELS = ('SIMULATION', 'REPLAY', 'EXISTING-ROVER MANUAL', 'EXISTING-ROVER AUTONOMOUS',
          'UPGRADED-ROVER PHYSICAL')
TOPICS_CSV = ROOT/'01_Interfaces_Communication/src/lunabotics_interfaces/config/topics.csv'
LAYOUT = ROOT/'02_Ground_Station_Telemetry/deliverables/lichtblick/lichtblick_layout.json'
LINK_BUDGET = ROOT/'pdr/link_budget.json'
RATE_TOLERANCE = 0.20          # measured mean rate must be within 20 % of expected
GAP_FACTOR = 3.0               # a gap is longer than 3x the expected period
EDGE_S = 1.0                   # replay parity: losses this close to either end are re-record edge effects
LATCHED = {'/tf_static'}       # published once; no rate expected
TF_SCHEMAS = {'tf2_msgs/msg/TFMessage'}
DECODE_ALL = {'tf2_msgs/msg/TFMessage', 'rosgraph_msgs/msg/Clock', 'nav_msgs/msg/Odometry',
              'nav_msgs/msg/Path'}
NS = 1e9


def load_expected_rates(path):
    rates = {}
    if path and Path(path).is_file():
        with open(path) as stream:
            for row in csv.DictReader(stream):
                value = (row.get('expected_rate_hz') or '').strip()
                if row.get('topic') and value:
                    rates[row['topic'].strip()] = float(value)
    return rates


def layout_topics(path):
    from measure_rosbridge_bandwidth import layout_ros_topics
    # Required by panels/scripts; /clock is optional for LichtBlick (used if present).
    return sorted(set(layout_ros_topics(path)) - {'/clock'})


def mcap_files(path):
    path = Path(path)
    if path.is_dir():
        files = sorted(path.glob('*.mcap'))
        if not files:
            raise SystemExit(f'No .mcap files in {path}')
        return files
    return [path]


def read_recording(files):
    from mcap.reader import make_reader
    from mcap_ros2.decoder import DecoderFactory
    topics = {}
    compression = set()
    first_header = {}
    decoded = {}
    for file in files:
        with open(file, 'rb') as stream:
            reader = make_reader(stream)
            summary = reader.get_summary()
            if summary:
                compression |= {c.compression or 'none' for c in summary.chunk_indexes}
        # mcap_ros2 caches decoders by schema id, which is only unique within one file.
        factory, decoders = DecoderFactory(), {}
        with open(file, 'rb') as stream:
            reader = make_reader(stream)
            for schema, channel, message in reader.iter_messages(log_time_order=True):
                schema_name = schema.name if schema else '(none)'
                entry = topics.setdefault(channel.topic, {
                    'schema': schema_name, 'encoding': channel.message_encoding,
                    'times': [], 'bytes': 0})
                entry['times'].append(message.log_time)
                entry['bytes'] += len(message.data)
                wants_all = schema_name in DECODE_ALL or channel.topic.endswith('/status')
                if not wants_all and channel.topic in first_header:
                    continue
                key = (channel.message_encoding, schema.id if schema else None)
                if key not in decoders:
                    decoders[key] = factory.decoder_for(channel.message_encoding, schema)
                if decoders[key] is None:
                    first_header.setdefault(channel.topic, None)
                    continue
                try:
                    msg = decoders[key](message.data)
                except Exception as error:  # keep going: report undecodable topics
                    first_header.setdefault(channel.topic, f'decode error: {error}')
                    continue
                if channel.topic not in first_header:
                    header = getattr(msg, 'header', None)
                    first_header[channel.topic] = getattr(header, 'frame_id', None)
                if wants_all:
                    decoded.setdefault(channel.topic, []).append((message.log_time, msg))
    return topics, compression, first_header, decoded


def topic_stats(name, entry, expected, start_ns):
    times = entry['times']
    count = len(times)
    first, last = times[0], times[-1]
    span = (last-first)/NS
    gaps = [(b-a)/NS for a, b in zip(times, times[1:])]
    mean_rate = (count-1)/span if count > 1 and span > 0 else None
    stats = {
        'schema': entry['schema'], 'encoding': entry['encoding'], 'count': count,
        'bytes': entry['bytes'], 'first_s': (first-start_ns)/NS, 'last_s': (last-start_ns)/NS,
        'mean_rate_hz': mean_rate, 'min_gap_s': min(gaps) if gaps else None,
        'max_gap_s': max(gaps) if gaps else None, 'expected_rate_hz': expected,
    }
    checks = {'present': count > 0}
    if name in LATCHED:
        stats['note'] = 'latched (published once); no rate check'
    elif expected:
        checks['rate_within_20pct'] = mean_rate is not None and abs(mean_rate-expected)/expected <= RATE_TOLERANCE
        limit = GAP_FACTOR/expected
        long_gaps = [{'at_s': (times[i]-start_ns)/NS, 'gap_s': g}
                     for i, g in enumerate(gaps) if g > limit]
        stats['gap_limit_s'] = limit
        stats['long_gaps'] = long_gaps
        checks['no_gap_over_3x_period'] = not long_gaps
    else:
        stats['note'] = 'no expected rate configured; rate not checked'
        if gaps:
            limit = GAP_FACTOR*statistics.median(gaps)
            stats['gap_limit_s'] = limit
            stats['long_gaps'] = [{'at_s': (times[i]-start_ns)/NS, 'gap_s': g}
                                  for i, g in enumerate(gaps) if g > limit]
            stats['gap_limit_basis'] = '3x median period (informational)'
    stats['checks'] = checks
    stats['passed'] = all(checks.values())
    return stats


def tf_and_clock(topics, decoded, first_header):
    result = {}
    clocks = [t for t, e in topics.items() if e['schema'] == 'rosgraph_msgs/msg/Clock']
    for topic in clocks:
        values = [m.clock.sec + m.clock.nanosec/NS for _, m in decoded.get(topic, [])]
        backwards = sum(1 for a, b in zip(values, values[1:]) if b < a)
        log = [t/NS for t, _ in decoded.get(topic, [])]
        offset = [lt-v for lt, v in zip(log, values)]
        result[topic] = {
            'messages': len(values), 'monotonic': backwards == 0, 'backwards_steps': backwards,
            'first_s': values[0] if values else None, 'last_s': values[-1] if values else None,
            'max_abs_log_minus_clock_s': max(map(abs, offset)) if offset else None}
    edges = {}
    for topic, entry in topics.items():
        if entry['schema'] in TF_SCHEMAS:
            for _, msg in decoded.get(topic, []):
                for transform in msg.transforms:
                    parent = transform.header.frame_id.lstrip('/')
                    child = transform.child_frame_id.lstrip('/')
                    edges.setdefault(child, set()).add((parent, topic))
    parents = {child: sorted(p for p, _ in values) for child, values in edges.items()}

    def root(frame, seen=()):
        if frame in seen:
            return None, True
        if frame not in parents:
            return frame, False
        return root(parents[frame][0], seen+(frame,))
    sensor_frames = {}
    for topic, frame in first_header.items():
        if isinstance(frame, str) and frame and not frame.startswith('decode error'):
            frame = frame.lstrip('/')
            top, loop = root(frame)
            sensor_frames[topic] = {'frame': frame, 'tf_root': top, 'loop': loop}
    roots = {v['tf_root'] for v in sensor_frames.values()}
    multi_parent = {c: p for c, p in parents.items() if len(p) > 1}
    tf_ok = bool(parents) and len(roots) <= 1 and not multi_parent and \
        not any(v['loop'] for v in sensor_frames.values())
    result['tf'] = {
        'edges': {child: p for child, p in sorted(parents.items())},
        'frames_with_multiple_parents': multi_parent, 'message_frames': sensor_frames,
        'common_root': next(iter(roots)) if len(roots) == 1 else sorted(r for r in roots if r),
        'all_message_frames_connected': tf_ok}
    result['passed'] = tf_ok and all(v['monotonic'] for k, v in result.items() if k in clocks)
    return result


def status_timeline(decoded, start_ns):
    for topic, items in decoded.items():
        if not topic.endswith('/status'):
            continue
        timeline, previous, goal, source = [], None, None, None
        for log_time, msg in items:
            try:
                payload = json.loads(msg.data)
            except (AttributeError, ValueError, TypeError):
                break
            source = payload.get('source', source)
            goal = payload.get('goal', goal)
            state = payload.get('state')
            if state != previous:
                timeline.append({'at_s': (log_time-start_ns)/NS, 'state': state})
                previous = state
        if timeline:
            return {'topic': topic, 'source': source, 'goal': goal, 'transitions': timeline,
                    'goal_reached': any(t['state'] == 'complete' for t in timeline)}
    return None


def path_data(topics, decoded):
    odom = next((t for t, e in sorted(topics.items()) if e['schema'] == 'nav_msgs/msg/Odometry'), None)
    path = next((t for t, e in sorted(topics.items()) if e['schema'] == 'nav_msgs/msg/Path'), None)
    xy = [(m.pose.pose.position.x, m.pose.pose.position.y) for _, m in decoded.get(odom, [])]
    plans = [[(p.pose.position.x, p.pose.position.y) for p in m.poses] for _, m in decoded.get(path, [])]
    plans = [p for p in plans if p]
    travelled = sum(math.dist(a, b) for a, b in zip(xy, xy[1:]))
    return {'odom_topic': odom, 'path_topic': path, 'xy': xy, 'plans': plans,
            'odom_frame': decoded[odom][0][1].header.frame_id if odom and decoded.get(odom) else None,
            'distance_travelled_m': travelled if xy else None}


def resources_summary(path):
    if not path:
        return None
    groups = {}
    with open(path) as stream:
        for row in csv.DictReader(stream):
            g = groups.setdefault(row['group'], {'cpu': [], 'rss': []})
            g['cpu'].append(float(row['cpu_percent_of_one_core']))
            g['rss'].append(float(row['rss_mb']))
            cores = int(row['cpu_cores'])
    return {'source': str(path), 'cpu_cores': cores, 'groups': {
        name: {'samples': len(v['cpu']), 'cpu_mean_pct_of_one_core': statistics.mean(v['cpu']),
               'cpu_max_pct_of_one_core': max(v['cpu']), 'rss_max_mb': max(v['rss'])}
        for name, v in sorted(groups.items())}}


def mcap_cli_info(files):
    exe = shutil.which('mcap')
    if not exe:
        return 'mcap CLI not on PATH; skipped (Python mcap library used instead)'
    out = []
    for file in files:
        run = subprocess.run([exe, 'info', str(file)], capture_output=True, text=True)
        out.append(run.stdout or run.stderr)
    return '\n'.join(out)


def replay_parity(recording, topics, domain=85):
    """Replay on an isolated ROS domain, re-record, and compare counts and header stamps."""
    if not shutil.which('ros2'):
        return {'ran': False, 'reason': 'ros2 not available (source ROS 2 first)'}
    from mcap.reader import make_reader
    from mcap_ros2.decoder import DecoderFactory
    env = dict(os.environ, ROS_DOMAIN_ID=str(domain))
    names = sorted(topics)
    with tempfile.TemporaryDirectory(prefix='replay_parity_') as tmp:
        out = Path(tmp)/'rerecord'
        rec = subprocess.Popen(['ros2', 'bag', 'record', '--storage', 'mcap', '--output', str(out),
                                *names], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
        try:
            time.sleep(3)  # let the recorder discover topics before playback starts
            subprocess.run(['ros2', 'bag', 'play', str(recording), '--disable-keyboard-controls'],
                           env=env, check=True, capture_output=True, timeout=600)
            time.sleep(3)
        finally:
            os.killpg(rec.pid, signal.SIGINT)
            rec.wait(timeout=30)
        def stamps(files, wanted):
            counts, stamp_sets = {}, {}
            for file in files:
                with open(file, 'rb') as stream:
                    factory, decoders = DecoderFactory(), {}
                    for schema, channel, message in make_reader(stream).iter_messages():
                        if channel.topic not in wanted:
                            continue
                        counts[channel.topic] = counts.get(channel.topic, 0)+1
                        key = schema.id
                        if key not in decoders:
                            decoders[key] = factory.decoder_for(channel.message_encoding, schema)
                        msg = decoders[key](message.data)
                        header = getattr(msg, 'header', None)
                        if header is not None:
                            stamp = (header.stamp.sec, header.stamp.nanosec)
                            stamp_sets.setdefault(channel.topic, set()).add(stamp)
            return counts, stamp_sets
        replay_files = sorted(out.glob('*.mcap'))
        orig_counts, orig_stamps = stamps(mcap_files(recording), set(names))
        new_counts, new_stamps = stamps(replay_files, set(names))
    rows = {}
    for topic in names:
        a, b = orig_counts.get(topic, 0), new_counts.get(topic, 0)
        row = {'original': a, 'replayed': b, 'count_ratio': b/a if a else None,
               'header_stamps_preserved_fraction': None}
        if topic in orig_stamps:
            replayed = new_stamps.get(topic, set())
            row['header_stamps_preserved_fraction'] = len(replayed & orig_stamps[topic])/max(1, len(replayed))
            # Where are the lost messages? Losses within EDGE_S of either end are recorder
            # discovery/shutdown effects of the re-record; interior losses would be real drops.
            ordered = sorted(orig_stamps[topic])
            first, last = ordered[0][0]+ordered[0][1]/NS, ordered[-1][0]+ordered[-1][1]/NS
            missing = [s[0]+s[1]/NS for s in orig_stamps[topic]-replayed]
            row['missing_at_edges'] = sum(1 for m in missing if m-first <= EDGE_S or last-m <= EDGE_S)
            row['missing_interior'] = len(missing)-row['missing_at_edges']
        rows[topic] = row
    same_topics = all(r['replayed'] > 0 for r in rows.values())
    stamps_ok = all(r['header_stamps_preserved_fraction'] in (None, 1.0) for r in rows.values())
    no_interior = all(r.get('missing_interior', 0) == 0 for r in rows.values())
    headerless_ok = all(r['count_ratio'] is not None and r['count_ratio'] >= 0.99
                        for r in rows.values() if r['header_stamps_preserved_fraction'] is None)
    return {'ran': True, 'method': f'ros2 bag play on isolated ROS_DOMAIN_ID={domain}, re-recorded with ros2 bag record',
            'criteria': f'all topics replayed; header stamps identical; header topics lose no messages '
                        f'except within {EDGE_S:.0f} s of either end; header-less topics keep >= 99 % of messages',
            'topics': rows, 'same_topics': same_topics, 'header_stamps_preserved': stamps_ok,
            'no_interior_losses': no_interior, 'headerless_counts_ok': headerless_ok,
            'passed': same_topics and stamps_ok and no_interior and headerless_ok}


def live_parity(bandwidth_json, per_topic):
    if not bandwidth_json:
        return None
    live = json.loads(Path(bandwidth_json).read_text())
    rows = {}
    for topic, row in live['topics'].items():
        mcap_rate = per_topic.get(topic, {}).get('mean_rate_hz')
        ratio = row['rate_hz']/mcap_rate if mcap_rate else None
        rows[topic] = {'live_rosbridge_hz': row['rate_hz'], 'mcap_hz': mcap_rate, 'ratio': ratio,
                       'in_recording': topic in per_topic}
    checked = {t: r for t, r in rows.items() if t not in LATCHED}
    passed = all(r['in_recording'] and r['ratio'] is not None and abs(r['ratio']-1) <= 0.10
                 for r in checked.values())
    return {'source': str(bandwidth_json), 'live_window_s': live['seconds'],
            'tolerance': '±10 % rate', 'topics': rows, 'passed': passed,
            'live_total_mbit_per_s': live['total_mbit_per_s']}


def margins(link_mbit, budget):
    assumed = budget.get('assumed_link_mbit_per_s')
    if assumed is None or link_mbit is None:
        return {'required_mbit_per_s': link_mbit, 'assumed_link_mbit_per_s': assumed,
                'margin_mbit_per_s': None, 'utilisation_pct': None, 'placeholder': True}
    return {'required_mbit_per_s': link_mbit, 'assumed_link_mbit_per_s': assumed,
            'margin_mbit_per_s': assumed-link_mbit, 'utilisation_pct': 100*link_mbit/assumed,
            'placeholder': budget.get('placeholder', True)}


# ---------------------------------------------------------------- plots
def setup_matplotlib():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 16, 'axes.titlesize': 20, 'axes.labelsize': 17,
                         'figure.facecolor': 'white', 'axes.facecolor': 'white',
                         'savefig.facecolor': 'white', 'axes.grid': True, 'grid.alpha': 0.3})
    return plt


def fig(plt):
    return plt.subplots(figsize=(13.333, 7.5), dpi=150)


def plot_rates(plt, topics, key_topics, start_ns, label, out):
    figure, ax = fig(plt)
    styles = ['-', '--', ':', '-.']  # topics with identical rates would otherwise hide each other
    for index, topic in enumerate(key_topics):
        times = [(t-start_ns)/NS for t in topics[topic]['times']]
        if not times:
            continue
        bins = range(0, int(math.ceil(times[-1]))+1)
        counts = [0]*len(bins)
        for t in times:
            counts[min(int(t), len(bins)-1)] += 1
        ax.step(list(bins), counts, where='post', linewidth=3.2-0.4*(index % 4),
                linestyle=styles[index % 4], label=topic)
    ax.set_xlabel('Time since start of recording (s)')
    ax.set_ylabel('Messages per second')
    ax.set_title(f'[{label}] Topic rate over time (1 s bins)')
    ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1), fontsize=14)
    figure.tight_layout()
    figure.savefig(out)
    plt.close(figure)


def plot_xy(plt, path, timeline, label, out):
    if not path['xy']:
        return False
    figure, ax = fig(plt)
    for i, plan in enumerate(path['plans']):
        xs, ys = zip(*plan)
        ax.plot(xs, ys, color='#00acc1', alpha=0.15, linewidth=1.5,
                label=f"planned paths ({path['path_topic']}, all updates)" if i == 0 else None)
    if path['plans']:
        xs, ys = zip(*path['plans'][0])
        ax.plot(xs, ys, color='#00838f', linewidth=3, linestyle='--', label='first planned path')
    xs, ys = zip(*path['xy'])
    ax.plot(xs, ys, color='#d84315', linewidth=3.5, label=f"rover path ({path['odom_topic']})")
    ax.scatter([xs[0]], [ys[0]], s=220, marker='o', color='#2e7d32', zorder=5, label='start')
    goal = timeline.get('goal') if timeline else None
    if goal:
        ax.scatter([goal[0]], [goal[1]], s=320, marker='*', color='#f9a825', edgecolor='black',
                   zorder=5, label='goal (from status)')
    ax.scatter([xs[-1]], [ys[-1]], s=180, marker='X', color='#212121', zorder=6, label='end')
    ax.set_aspect('equal', adjustable='datalim')
    frame = path['odom_frame'] or '?'
    ax.set_xlabel(f'x in {frame} (m)')
    ax.set_ylabel(f'y in {frame} (m)')
    ax.set_title(f'[{label}] Rover XY path vs planned path')
    ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1), fontsize=14)
    figure.tight_layout()
    figure.savefig(out)
    plt.close(figure)
    return True


def plot_bandwidth(plt, per_topic, duration, label, out):
    rows = sorted(((t, s['bytes']*8/duration/1e3) for t, s in per_topic.items()), key=lambda r: r[1])
    figure, ax = fig(plt)
    names, kbit = zip(*rows)
    bars = ax.barh(names, kbit, color='#1565c0')
    ax.set_xscale('log')
    for bar, value in zip(bars, kbit):
        ax.text(value*1.08, bar.get_y()+bar.get_height()/2, f'{value:,.1f}', va='center', fontsize=13)
    ax.set_xlabel('Recorded payload bandwidth (kbit/s, log scale)')
    ax.set_title(f'[{label}] Telemetry bandwidth per topic (total {sum(kbit)/1e3:.2f} Mbit/s)')
    ax.set_xlim(right=max(kbit)*6)
    figure.tight_layout()
    figure.savefig(out)
    plt.close(figure)


def plot_gaps(plt, topics, per_topic, start_ns, duration, label, out):
    names = sorted(t for t in per_topic if t not in LATCHED)
    figure, ax = fig(plt)
    for row, topic in enumerate(names):
        stats = per_topic[topic]
        ax.hlines(row, stats['first_s'], stats['last_s'], color='#90a4ae', linewidth=8)
        for gap in stats.get('long_gaps', []):
            ax.hlines(row, gap['at_s'], gap['at_s']+gap['gap_s'], color='#c62828', linewidth=12)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=13)
    ax.set_xlim(0, duration)
    ax.set_xlabel('Time since start of recording (s)')
    ax.set_title(f'[{label}] Message coverage (grey) and gaps > 3x period (red)')
    figure.tight_layout()
    figure.savefig(out)
    plt.close(figure)


# ---------------------------------------------------------------- report
def fmt(value, digits=2):
    if value is None:
        return '—'
    if isinstance(value, float):
        return f'{value:.{digits}f}'
    return str(value)


def write_markdown(summary, out):
    s = summary
    lines = [f"# MCAP verification: {s['run_name']}", '',
             f"**Run label: {s['label']}**  ", f"Recording: `{s['recording']}`  ",
             f"Overall: **{'PASS' if s['passed'] else 'FAIL'}**", '',
             '## Recording', '', '| Item | Value |', '| --- | --- |']
    r = s['recording_stats']
    for key, label in [('duration_s', 'Duration (s)'), ('file_size_mb', 'File size (MB)'),
                       ('mb_per_min', 'Storage rate (MB/min)'), ('compression', 'Chunk compression'),
                       ('message_count', 'Messages'), ('topic_count', 'Topics'),
                       ('payload_mbit_per_s', 'Recorded payload rate (Mbit/s)'),
                       ('time_base', 'Time base')]:
        lines.append(f'| {label} | {fmt(r[key])} |')
    lines += ['', '## Per-topic checks', '',
              '| Topic | Schema | Count | Mean Hz | Expected Hz | Min gap s | Max gap s | Gaps >3x | kbit/s | Result |',
              '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for topic, t in s['topics'].items():
        gaps = len(t.get('long_gaps', [])) if 'long_gaps' in t else '—'
        result = 'PASS' if t['passed'] else 'FAIL: ' + ', '.join(k for k, v in t['checks'].items() if not v)
        lines.append(f"| `{topic}` | `{t['schema']}` | {t['count']} | {fmt(t['mean_rate_hz'])} | "
                     f"{fmt(t['expected_rate_hz'], 0)} | {fmt(t['min_gap_s'], 3)} | {fmt(t['max_gap_s'], 3)} | "
                     f"{gaps} | {fmt(t['kbit_per_s'], 1)} | {result} |")
    lines += ['', 'First/last timestamps per topic are in `summary.json`.', '',
              '## Layout coverage', '',
              f"{s['layout_coverage']['present']}/{s['layout_coverage']['required']} topics the LichtBlick layout needs are present "
              f"(**{fmt(s['layout_coverage']['percent'], 0)} %**)."]
    if s['layout_coverage']['missing']:
        lines.append('Missing: ' + ', '.join(f'`{m}`' for m in s['layout_coverage']['missing']))
    tf = s['tf_clock']
    lines += ['', '## TF and clock', '']
    for topic, c in tf.items():
        if topic.startswith('/') and isinstance(c, dict) and 'monotonic' in c:
            lines.append(f"- `{topic}`: {c['messages']} messages, monotonic: **{c['monotonic']}**, "
                         f"max |log time − clock| = {fmt(c['max_abs_log_minus_clock_s'], 3)} s")
    lines.append(f"- TF root: `{tf['tf']['common_root']}`; all message frames connected: "
                 f"**{tf['tf']['all_message_frames_connected']}**")
    for topic, f in tf['tf']['message_frames'].items():
        lines.append(f"  - `{topic}` frame `{f['frame']}` → root `{f['tf_root']}`")
    if s.get('status_timeline'):
        st = s['status_timeline']
        lines += ['', f"## Mission state timeline (`{st['topic']}`, source `{st['source']}`)", '',
                  '| t (s) | State |', '| --- | --- |']
        lines += [f"| {x['at_s']:.2f} | {x['state']} |" for x in st['transitions']]
        lines.append(f"\nGoal reached: **{st['goal_reached']}**")
    if s.get('path'):
        lines += ['', f"Distance travelled (odometry): {fmt(s['path']['distance_travelled_m'])} m"]
    if s.get('live_parity'):
        lp = s['live_parity']
        lines += ['', '## Live vs recording parity (Rosbridge rates vs MCAP rates)', '',
                  f"Live window {lp['live_window_s']:.1f} s, tolerance {lp['tolerance']}: **{'PASS' if lp['passed'] else 'FAIL'}**", '',
                  '| Topic | Live Hz | MCAP Hz | Ratio |', '| --- | --- | --- | --- |']
        lines += [f"| `{t}` | {fmt(r['live_rosbridge_hz'])} | {fmt(r['mcap_hz'])} | {fmt(r['ratio'], 3)} |"
                  for t, r in lp['topics'].items()]
    if s.get('replay_parity'):
        rp = s['replay_parity']
        lines += ['', '## Replay parity', '']
        if rp['ran']:
            lines += [f"{rp['method']}. Criteria: {rp['criteria']}.", '',
                      f"Same topics **{rp['same_topics']}**, header stamps identical **{rp['header_stamps_preserved']}**, "
                      f"no interior losses **{rp['no_interior_losses']}**, header-less counts ≥ 99 % **{rp['headerless_counts_ok']}** "
                      f"→ **{'PASS' if rp['passed'] else 'FAIL'}**", '',
                      '| Topic | Original | Replayed | Ratio | Stamps identical | Lost at edges | Lost inside |',
                      '| --- | --- | --- | --- | --- | --- | --- |']
            lines += [f"| `{t}` | {r['original']} | {r['replayed']} | {fmt(r['count_ratio'], 3)} | "
                      f"{fmt(r['header_stamps_preserved_fraction'], 3)} | {fmt(r.get('missing_at_edges'))} | {fmt(r.get('missing_interior'))} |"
                      for t, r in rp['topics'].items()]
        else:
            lines.append(f"Not run: {rp['reason']}")
    if s.get('resources'):
        res = s['resources']
        lines += ['', f"## Process resources ({res['cpu_cores']} cores; CPU % of one core)", '',
                  '| Process | Samples | CPU mean % | CPU max % | RSS max MB |', '| --- | --- | --- | --- | --- |']
        lines += [f"| {g} | {v['samples']} | {v['cpu_mean_pct_of_one_core']:.1f} | {v['cpu_max_pct_of_one_core']:.1f} | {v['rss_max_mb']:.1f} |"
                  for g, v in res['groups'].items()]
    m = s['margins']
    lines += ['', '## Link margin (PLACEHOLDER BUDGET)', '',
              f"Required (live Rosbridge, layout topics): **{fmt(m['required_mbit_per_s'])} Mbit/s**. "
              f"Assumed link: **{fmt(m['assumed_link_mbit_per_s'])} Mbit/s** ← placeholder from `pdr/link_budget.json`, "
              f"replace with Sabu+Robin's measured numbers.", '',
              f"Margin: {fmt(m['margin_mbit_per_s'])} Mbit/s; utilisation {fmt(m['utilisation_pct'], 0)} %."]
    lines += ['', '## Plots', ''] + [f'- `{p}`' for p in s['plots']]
    lines += ['', '## mcap CLI', '', '```', s['mcap_cli'].strip(), '```', '']
    out.write_text('\n'.join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('recording', help='.mcap file or rosbag2 folder')
    ap.add_argument('--label', required=True, choices=LABELS)
    ap.add_argument('--name', help='run name (default: <label>_<recording name>)')
    ap.add_argument('--out-root', type=Path, default=ROOT/'pdr/evidence')
    ap.add_argument('--expected-rates', default=str(TOPICS_CSV),
                    help='CSV with topic,expected_rate_hz columns (default: interfaces topics.csv)')
    ap.add_argument('--layout', default=str(LAYOUT))
    ap.add_argument('--resources', help='resources.csv from tools/sample_resources.py')
    ap.add_argument('--rosbridge-bandwidth', help='JSON from tools/measure_rosbridge_bandwidth.py')
    ap.add_argument('--replay-parity', action='store_true',
                    help='replay on isolated ROS domain 85, re-record and compare (needs ROS 2)')
    ap.add_argument('--key-topics', nargs='*', help='topics for the rate plot (default: auto)')
    args = ap.parse_args()

    files = mcap_files(args.recording)
    stem = Path(args.recording).name.removesuffix('.mcap')
    prefix = args.label.replace(' ', '_')
    name = args.name or (stem if stem.upper().startswith(prefix[:5]) else f'{prefix}_{stem}')
    out = args.out_root/name
    out.mkdir(parents=True, exist_ok=True)

    topics, compression, first_header, decoded = read_recording(files)
    if not topics:
        raise SystemExit('Recording has no messages')
    start_ns = min(e['times'][0] for e in topics.values())
    end_ns = max(e['times'][-1] for e in topics.values())
    duration = (end_ns-start_ns)/NS
    size_mb = sum(f.stat().st_size for f in files)/1e6
    expected = load_expected_rates(args.expected_rates)

    per_topic = {}
    for topic in sorted(topics):
        stats = topic_stats(topic, topics[topic], expected.get(topic), start_ns)
        stats['kbit_per_s'] = topics[topic]['bytes']*8/duration/1e3 if duration else None
        stats['frame_id'] = first_header.get(topic)
        per_topic[topic] = stats

    required = layout_topics(args.layout) if Path(args.layout).is_file() else []
    present = [t for t in required if t in topics]
    coverage = {'layout': str(args.layout), 'required': len(required), 'present': len(present),
                'missing': [t for t in required if t not in topics],
                'percent': 100*len(present)/len(required) if required else None}

    tf_clock = tf_and_clock(topics, decoded, first_header)
    timeline = status_timeline(decoded, start_ns)
    path = path_data(topics, decoded)
    live = live_parity(args.rosbridge_bandwidth, per_topic)
    replay = replay_parity(args.recording, [t for t in topics if t not in LATCHED]) if args.replay_parity else None
    budget = json.loads(LINK_BUDGET.read_text()) if LINK_BUDGET.is_file() else {}
    link_required = live['live_total_mbit_per_s'] if live else None

    plt = setup_matplotlib()
    plots = []
    keys = args.key_topics or [t for t in sorted(per_topic, key=lambda t: -per_topic[t]['count'])
                               if per_topic[t]['expected_rate_hz'] and t != '/clock'][:6] \
        or sorted(per_topic, key=lambda t: -per_topic[t]['count'])[:6]
    plot_rates(plt, topics, keys, start_ns, args.label, out/'topic_rates.png')
    plots.append('topic_rates.png')
    if plot_xy(plt, path, timeline, args.label, out/'xy_path.png'):
        plots.append('xy_path.png')
    plot_bandwidth(plt, per_topic, duration, args.label, out/'bandwidth_per_topic.png')
    plots.append('bandwidth_per_topic.png')
    plot_gaps(plt, topics, per_topic, start_ns, duration, args.label, out/'gap_timeline.png')
    plots.append('gap_timeline.png')

    layout_ok = coverage['percent'] in (None, 100.0)
    checks = {'all_topics_pass': all(t['passed'] for t in per_topic.values()),
              'layout_coverage_100pct': layout_ok, 'tf_and_clock_ok': tf_clock['passed']}
    if live:
        checks['live_parity'] = live['passed']
    if replay and replay.get('ran'):
        checks['replay_parity'] = replay['passed']
    summary = {
        'run_name': name, 'label': args.label, 'recording': str(args.recording),
        'files': [str(f) for f in files],
        'recording_stats': {
            'duration_s': duration, 'file_size_mb': size_mb,
            'mb_per_min': size_mb/(duration/60) if duration else None,
            'compression': ', '.join(sorted(compression)) or 'unknown',
            'message_count': sum(len(e['times']) for e in topics.values()), 'topic_count': len(topics),
            'payload_mbit_per_s': sum(e['bytes'] for e in topics.values())*8/duration/1e6 if duration else None,
            'start_ns': start_ns, 'end_ns': end_ns,
            'time_base': 'simulation time (starts near 0)' if start_ns < 1e18 else 'wall clock'},
        'topics': per_topic, 'layout_coverage': coverage, 'tf_clock': tf_clock,
        'status_timeline': timeline,
        'path': {k: v for k, v in path.items() if k not in ('xy', 'plans')} | {
            'odom_samples': len(path['xy']), 'planned_path_updates': len(path['plans'])},
        'live_parity': live, 'replay_parity': replay,
        'resources': resources_summary(args.resources),
        'margins': margins(link_required, budget), 'link_budget_file': str(LINK_BUDGET),
        'thresholds': {'rate_tolerance': RATE_TOLERANCE, 'gap_factor': GAP_FACTOR},
        'checks': checks, 'passed': all(checks.values()),
        'plots': plots, 'mcap_cli': mcap_cli_info(files)}
    for source in (args.resources, args.rosbridge_bandwidth):
        if source:
            shutil.copy(source, out/Path(source).name)
    (out/'summary.json').write_text(json.dumps(summary, indent=2, default=str)+'\n')
    write_markdown(summary, out/'summary.md')
    print(f"[{args.label}] {name}: {'PASS' if summary['passed'] else 'FAIL'}  "
          + ' '.join(f'{k}={v}' for k, v in checks.items()))
    for topic, t in per_topic.items():
        if not t['passed']:
            print(f"  FAIL {topic}: " + ', '.join(k for k, v in t['checks'].items() if not v)
                  + f" (mean {fmt(t['mean_rate_hz'])} Hz, expected {fmt(t['expected_rate_hz'], 0)})")
    print(f'  -> {out}')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
