#!/usr/bin/env python3
"""Sample CPU and memory of the sim/telemetry processes to CSV until stopped (Ctrl+C or SIGTERM)."""
import argparse
import csv
import signal
import time

import psutil

# label -> substrings that identify the process command line
GROUPS = {
    'rosbridge': ['rosbridge_websocket'],
    'recorder': ['bag record'],
    'gazebo': ['gz sim server', 'gz-sim-server'],
    'gz_bridge': ['parameter_bridge'],
    'navigator': ['simulation_navigator'],
}


def label_of(process):
    try:
        cmdline = ' '.join(process.cmdline())
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None
    for label, needles in GROUPS.items():
        if any(needle in cmdline for needle in needles):
            return label
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    ap.add_argument('--interval', type=float, default=1.0)
    ap.add_argument('--duration', type=float, default=0, help='seconds; 0 = until stopped')
    args = ap.parse_args()

    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    cores = psutil.cpu_count()
    tracked = {}
    psutil.cpu_percent()
    start = time.time()
    with open(args.out, 'w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['wall_time', 'elapsed_s', 'group', 'pids', 'cpu_percent_of_one_core',
                         'cpu_percent_of_machine', 'rss_mb', 'system_cpu_percent',
                         'system_mem_used_percent', 'cpu_cores'])
        while running and (not args.duration or time.time()-start < args.duration):
            for process in psutil.process_iter():
                if process.pid not in tracked:
                    label = label_of(process)
                    if label:
                        tracked[process.pid] = (label, process)
                        process.cpu_percent()
            time.sleep(args.interval)
            totals = {}
            for pid, (label, process) in list(tracked.items()):
                try:
                    cpu, rss = process.cpu_percent(), process.memory_info().rss
                except psutil.Error:
                    del tracked[pid]
                    continue
                entry = totals.setdefault(label, [[], 0.0, 0])
                entry[0].append(pid)
                entry[1] += cpu
                entry[2] += rss
            now = time.time()
            system_cpu, system_mem = psutil.cpu_percent(), psutil.virtual_memory().percent
            for label, (pids, cpu, rss) in sorted(totals.items()):
                writer.writerow([f'{now:.3f}', f'{now-start:.1f}', label, ' '.join(map(str, pids)),
                                 f'{cpu:.1f}', f'{cpu/cores:.2f}', f'{rss/2**20:.1f}',
                                 f'{system_cpu:.1f}', f'{system_mem:.1f}', cores])
            stream.flush()


if __name__ == '__main__':
    main()
