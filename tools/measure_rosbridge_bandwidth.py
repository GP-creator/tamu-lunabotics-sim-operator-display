#!/usr/bin/env python3
"""Measure the Rosbridge bandwidth LichtBlick would pull for the layout's topics.

Subscribes the way LichtBlick 1.30.0 does (compression "cbor-raw"), including /clock, which
LichtBlick's Rosbridge player always subscribes to when it exists. Only subscribes; never publishes.
"""
import argparse
import json
from pathlib import Path
import sys
import time

import cbor2
import websocket

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_layout import LICHTBLICK, panel_topics  # noqa: E402


def layout_ros_topics(layout_path):
    layout = json.loads(Path(layout_path).read_text())
    topics = set()
    for config in layout['configById'].values():
        topics |= {t for t in panel_topics(config) if not t.startswith('/studio_script/')}
    for script in layout.get('userNodes', {}).values():
        code = script['sourceCode']
        start = code.index('inputs')
        topics |= set(json.loads(code[code.index('[', start):code.index(']', start)+1]))
    # The 3D panel subscribes to TF; the Rosbridge player subscribes to /clock.
    return sorted(topics | {'/tf', '/tf_static', '/clock'})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--url', default='ws://localhost:9090')
    ap.add_argument('--seconds', type=float, default=10)
    ap.add_argument('--layout', default=str(LICHTBLICK/'lichtblick_layout.json'))
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()

    topics = layout_ros_topics(args.layout)
    ws = websocket.create_connection(args.url, timeout=1)
    for topic in topics:
        ws.send(json.dumps({'op': 'subscribe', 'topic': topic, 'id': 'bw'+topic,
                            'compression': 'cbor-raw'}))
    counts = {t: 0 for t in topics}
    wire = {t: 0 for t in topics}
    other = 0
    start = time.time()
    while time.time()-start < args.seconds:
        try:
            frame = ws.recv()
        except websocket.WebSocketTimeoutException:
            continue
        size = len(frame) if isinstance(frame, bytes) else len(frame.encode())
        message = cbor2.loads(frame) if isinstance(frame, bytes) else json.loads(frame)
        topic = message.get('topic')
        if message.get('op') == 'publish' and topic in counts:
            counts[topic] += 1
            wire[topic] += size
        else:
            other += size
    elapsed = time.time()-start
    for topic in topics:
        ws.send(json.dumps({'op': 'unsubscribe', 'topic': topic, 'id': 'bw'+topic}))
    ws.close()

    per_topic = {t: {'messages': counts[t], 'rate_hz': counts[t]/elapsed,
                     'bytes_per_s': wire[t]/elapsed, 'kbit_per_s': wire[t]*8/elapsed/1e3}
                 for t in topics}
    total = sum(wire.values())+other
    result = {'url': args.url, 'seconds': elapsed, 'compression': 'cbor-raw',
              'topics': per_topic, 'other_bytes': other,
              'total_bytes_per_s': total/elapsed, 'total_mbit_per_s': total*8/elapsed/1e6}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    for topic, row in per_topic.items():
        print(f"{topic:26} {row['rate_hz']:7.1f} Hz {row['kbit_per_s']:10.1f} kbit/s")
    print(f"TOTAL {result['total_mbit_per_s']:.2f} Mbit/s over {elapsed:.1f} s -> {args.out}")
    return 0 if all(counts[t] for t in topics if t != '/tf_static') else 1


if __name__ == '__main__':
    sys.exit(main())
