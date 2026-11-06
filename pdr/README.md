# PDR evidence package: slides 9–11 (LichtBlick)

All results are **SIMULATION** or **REPLAY** until real-rover data arrives on Nov 5.

| File | What it is |
| --- | --- |
| `slides_9_11.md` | Slide text, tables, figure placement, speaker notes, open actions |
| `merge_review.md` | Panel-by-panel merge of Alice Choi's dashboard (PR #4) |
| `shot_list.md` | Screenshots to take from OBS / LichtBlick, with timing and slide |
| `dependency_requests.md` | What we need from the other pairs and Vin |
| `link_budget.json` | **Placeholder** link budget used for margins; replace with measured numbers |
| `figures/` | Layout diagram and data-path figure (`tools/layout_diagram.py`) |
| `evidence/<run>/` | `verify_mcap.py` output per recording: `summary.md/.json`, plots, resources, bandwidth, banners |

## Tools

| Command | Does |
| --- | --- |
| `bash tools/run_pdr_demo.sh [--headless]` | Sim + recording in one command, banners for OBS, stops at goal or timeout |
| `python3 tools/validate_layout.py` | Every layout topic is sim-available or documented rover-only |
| `python3 tools/layout_diagram.py` | Regenerates `figures/` from the layout |
| `tools/verify_mcap.py RECORDING --label LABEL` | Verifies any MCAP and writes `evidence/<run>/` |

`verify_mcap.py` needs `mcap` and `mcap-ros2-support`. One-time setup without sudo (this Ubuntu has no `ensurepip`, so pip is bootstrapped):

```bash
python3 -m venv --system-site-packages --without-pip ~/.venvs/lunabotics-pdr
curl -fsSL -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
~/.venvs/lunabotics-pdr/bin/python /tmp/get-pip.py
~/.venvs/lunabotics-pdr/bin/pip install mcap==1.2.2 mcap-ros2-support==0.5.5
```

Run it (source ROS first if you want `--replay-parity`):

```bash
source /opt/ros/jazzy/setup.bash
R=~/lunabotics_recordings/SIMULATED_pdr_<time>
~/.venvs/lunabotics-pdr/bin/python tools/verify_mcap.py $R --label SIMULATION \
    --resources ${R}_logs/resources.csv --rosbridge-bandwidth ${R}_logs/rosbridge_bandwidth.json --replay-parity
```

Labels: `SIMULATION`, `REPLAY`, `EXISTING-ROVER MANUAL`, `EXISTING-ROVER AUTONOMOUS`, `UPGRADED-ROVER PHYSICAL`. The optional `mcap` CLI is used for `mcap info` if it is on PATH.

## Check criteria

- Topic rate within ±20 % of `topics.csv` (or `--expected-rates` CSV); no gap over 3× the expected period. Topics without an expected rate are reported, not checked.
- Layout coverage: every ROS topic the layout's panels and scripts read is in the recording.
- TF: every message frame reaches one TF root; clock monotonic.
- Live parity: Rosbridge rates (LichtBlick-style `cbor-raw`) within ±10 % of the recording.
- Replay parity: replay on isolated `ROS_DOMAIN_ID=85`, re-record; header stamps identical, no losses except within 1 s of either end.
