# Where the raw recordings are, and how to check and replay them

Raw MCAP files are **not in GitHub** (100+ MB each; GitHub rejects files over 100 MB). This repo holds only the evidence about them: `pdr/evidence/<run>/metadata.json`, `SHA256SUMS`, `summary.md` and plots.

## Locations

| Run | Label | File | Size (bytes) | SHA-256 |
| --- | --- | --- | --- | --- |
| `SIMULATED_pdr_20261104_124956` (OBS run, main PDR evidence) | SIMULATION | `SIMULATED_pdr_20261104_124956_0.mcap` | 106,370,973 | `28797737cd1a10bbcd997f1bea2f570fbea7dc03b7e7614fbd74da67db39c36f` |
| `SIMULATED_pdr_20261104_112151` (NO PATH event) | SIMULATION | `SIMULATED_pdr_20261104_112151_0.mcap` | 145,032,547 | `56dd34c4b0858eb719291e2093986c61bf41f992a62c6eccb919a22c574d0190` |

- **Shared copy (team): PLACEHOLDER: shared Drive folder `CDH / PDR / LichtBlick recordings` (link TBD, owner Gadadhar).** Upload each run folder (the `.mcap` and its `metadata.yaml`) plus the matching `pdr/evidence/<run>/SHA256SUMS`.
- **Original:** Gadadhar's laptop, `~/lunabotics_recordings/<run>/` (WSL). Copies for the web app: `C:\Users\gadha\Downloads\lunabotics_pdr\` (checksums verified 2026-11-04).
- **Rover data from Vin (Nov 5):** goes in the same Drive folder under its own run ID. The rover footage and the MCAP must share that run ID.

## For another member: download, verify, replay

1. **Download** the run folder from the shared Drive folder (link TBD) into a normal folder, e.g. `Downloads\lunabotics_pdr\` on Windows or `~/lunabotics_recordings/` on Ubuntu.
2. **Verify the checksum** against the table above or `pdr/evidence/<run>/SHA256SUMS`:
   - Windows PowerShell: `Get-FileHash .\SIMULATED_pdr_20261104_124956_0.mcap -Algorithm SHA256`. The hash must equal the table (case does not matter).
   - Ubuntu, in the folder with the `.mcap`: `sha256sum -c /path/to/repo/pdr/evidence/SIMULATED_pdr_20261104_124956/SHA256SUMS` → `…: OK`.
   - If it does not match, the download is incomplete or the wrong file: download again and do not use it as evidence.
3. **Replay offline**, with no ROS needed:
   - LichtBlick (desktop 1.30.0 preferred): **File → Open local file(s)…** → the `.mcap`; **View → Import layout from file…** → `02_Ground_Station_Telemetry/deliverables/lichtblick/lichtblick_layout.json`. Press play.
   - The web app cannot open files under `\\wsl$\…`; keep the file in a normal Windows folder.
4. **Replay through ROS** (optional, Ubuntu with the workspace built; no live simulation running):
   `bash 02_Ground_Station_Telemetry/deliverables/lichtblick/record_replay.sh replay <run folder>`, then connect LichtBlick to `ws://localhost:9090`.
5. **Re-check the evidence** (optional): `record_replay.sh verify <run folder> REPLAY`, then compare with `pdr/evidence/<run>/summary.md`.
