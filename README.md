# CrimeScan

CrimeScan is a modular forensic-scene documentation and evidence-management
research project spanning desktop software, evidence integrity and reporting, a
separately maintained Flutter mobile companion, and embedded hardware
integration. The available desktop source retains the historical **SpiderCam
Forensic Suite** branding in parts of its UI and output.

## Repository scope

This repository contains the desktop Python application and its evidence
integrity, reporting, and visualization workflows. The Flutter mobile
application and embedded hardware/firmware are maintained separately and are
not included here. The wider system description below provides context; it
does not imply that those separate implementations are available in this
repository. The repository also does not contain the remote token/API service
needed for optional live streaming.

## Problem

Scene documentation can involve separate steps for capturing images, reviewing
objects of interest, recording evidence metadata, and preparing reports.
CrimeScan explores a desktop workflow that brings image review, candidate
detection, basic file-integrity checks, and visualization together while
keeping a human operator in the loop.

The software is a research and demonstration prototype. It is not a validated
forensic product and does not establish legal admissibility or chain of custody.

## CrimeScan system architecture

The wider CrimeScan project is organized into four components. Components 1
and 2 are represented in this repository; components 3 and 4 are separate
project work and are not part of this checkout.

| Component | Wider system role | In this repository |
|---|---|---|
| **1. Desktop application** | Python/PyQt6 interface for scene viewing, image/video review, computer-vision-assisted candidate detection, and scene visualization. | Included in `spiderweb.py`, `remote_stream.py`, `reconstruction_3d.py`, and `viewer/`. |
| **2. Evidence integrity and reporting** | Case evidence records, SHA-256 file checks, manifests, audit logging, and PDF/JSON/CSV exports. | Included as desktop application workflows. These are basic mutable-file checks, not an immutable or legally validated chain of custody. |
| **3. Mobile companion application** | Separate Flutter/Dart application for mobile case and evidence capture/review, with location/media metadata and synchronization workflows. | Maintained separately; no Flutter source is included here. Its workflows and integrations are a prototype and are not validated by this repository. |
| **4. Embedded hardware integration** | Separate hardware/firmware work associated with the camera documentation platform and embedded control/communication. | Maintained separately; no firmware or hardware-control source is included here. |

The desktop repository's internal data flow is:

```text
Camera / local image or video files
                 |
                 v
      PyQt6 desktop application
       |           |            |
       |           |            +-- PDF / JSON / CSV reports
       |           +-- OpenCV processing and YOLO candidate detection
       +-- SHA-256 manifest and append-only audit-log file
                 |
                 +-- Optional LiveKit subscriber
                 |      (requires an externally operated token service)
                 |
                 +-- COLMAP + Open3D reconstruction workflow
                        |
                        v
                   Flask on loopback
                        |
                        v
                Three.js point-cloud viewer
```

`spiderweb.py` is the desktop entry point. `remote_stream.py` implements the
desktop LiveKit subscriber and accesses a separately configured token service.
`reconstruction_3d.py` prepares frames, invokes COLMAP, converts point clouds
for the viewer, and serves local viewer data. The mobile stream publisher and
token-service backend are not included.

## Implemented functionality

- PyQt6 desktop interface with live-feed, evidence-gallery, scene-mapping,
  candidate-detection, report, settings, and reconstruction views. The Analysis
  view is a placeholder.
- OpenCV image and video handling, frame extraction, image stitching, manual
  mosaic composition, grid overlays, and map export.
- Ultralytics YOLO model integration for a selected subset of COCO classes.
  Detection boxes, confidence values, and image-grid references are presented
  as **candidates for human review**, not forensic identification.
- Case manifests with chunked SHA-256 file hashes, re-verification of recorded
  files, and a text audit log.
- PDF, JSON, and CSV report export.
- Optional LiveKit video subscription, contingent on an external token service,
  its credentials, and a compatible publisher.
- COLMAP/Open3D sparse and dense reconstruction attempts and a local Three.js
  point-cloud viewer. When genuine reconstruction output is unavailable, the
  code can show an explicitly labeled synthetic demonstration point cloud.

The code includes an HTTP bridge for sharing current detection results, but no
separate mobile client is included in this repository.

## Technology

Python, PyQt6, OpenCV, NumPy, Ultralytics, LiveKit, Flask, Open3D, COLMAP,
ReportLab, and Three.js r128 (loaded from a CDN).

Python dependencies are listed in [`requirements.txt`](requirements.txt).
COLMAP is an external executable and is not installed by that file.

## Installation

Use Python 3.11 or another version supported by the installed dependency
releases. The project does not currently pin dependency versions.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Install COLMAP separately if you intend to run 3D reconstruction. Configure
`COLMAP_EXECUTABLE` with the full path to its executable, or ensure `colmap` is
available on `PATH`. Open3D must also be installed for point-cloud conversion.

The YOLO weights file is intentionally not included. On first inference,
Ultralytics may download `yolov8n.pt` through its model distribution mechanism.
Review the model source and applicable terms before downloading or using weights.
The local weight file from the development machine has no verified provenance
in this repository. The installed Ultralytics package metadata reports
AGPL-3.0; review [Ultralytics licensing information](https://www.ultralytics.com/license)
and the applicable model terms before redistributing or deploying it.

## Configuration

See [`.env.example`](.env.example) for variable names. It is a template only;
the application does not load `.env` files automatically. Set variables in the
shell or another secure local configuration mechanism.

| Variable | Required for | Description |
|---|---|---|
| `SPIDERCAM_API_BASE_URL` | Remote device/stream integration | URL of the separately operated API service. No endpoint is bundled or assumed. |
| `SPIDERCAM_SHARED_KEY` | Remote device/stream integration | API key supplied by that service operator. |
| `COLMAP_EXECUTABLE` | 3D reconstruction, unless on `PATH` | Path to the COLMAP executable. |
| `CRIMESCAN_DATA_DIR` | Optional | Root directory for generated 3D reconstruction and viewer data. Defaults to the application directory. |

Do not put real credentials in `.env.example`, source files, screenshots, or
public issue reports.

## Usage

Launch the desktop application from the project directory:

```powershell
python spiderweb.py
```

Load local images or a video through the relevant desktop page to explore
processing, candidate detection, evidence records, or exports. Remote streaming
requires the external service and publisher to be configured separately.
Three-dimensional reconstruction requires at least two usable frames, COLMAP,
and Open3D. A synthetic output, if produced, is visibly marked as demonstration
data and must not be interpreted as a scene reconstruction.

Run the focused automated tests with:

```powershell
python -m unittest discover -s tests -v
```

## Evidence integrity approach

The manifest computes SHA-256 incrementally from file bytes and stores the
digest alongside a path, filename, timestamp, case/operator fields, and action.
Verification reports verified, modified, missing, unreadable, or invalid
manifest states. A hash failure raises an error rather than returning a value
that could compare as a digest. Audit-log write failures are surfaced rather
than treated as successful logging.

These are basic application-level checks. Manifests and logs are ordinary
mutable files; this software does not provide immutable storage, independently
trusted timestamps, access-control guarantees, or a legally validated
chain-of-custody process.

## Reconstruction workflow

The application prepares selected frames under the configured data directory,
invokes COLMAP feature extraction, matching, mapping, and dense reconstruction
commands, then converts available point-cloud output for the Three.js viewer.
COLMAP and Open3D failures are surfaced. Where processing cannot yield usable
reconstruction data, the application may generate a synthetic visualization;
the viewer marks this output as demonstration-only and does not create random
replacement geometry when point-cloud data cannot be loaded.

The viewer page uses Three.js r128 from cdnjs, so the browser needs network
access to that CDN unless the dependency is separately reviewed and served
locally.

## Repository structure

```text
CrimeScan/
├── spiderweb.py
├── remote_stream.py
├── reconstruction_3d.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── tests/
│   └── test_public_release.py
└── viewer/
    └── index.html
```

Generated case data, evidence, models, databases, and reconstruction outputs
are excluded by `.gitignore`.

## Current limitations

- This source has no packaged installer, dependency lockfile, or integration
  test for the full desktop GUI.
- Remote stream and device-list operations require an external API service and
  a compatible publisher, neither of which is included.
- YOLO output is general object detection and is not trained or validated here
  for crime-scene interpretation.
- COLMAP reconstruction quality depends on input imagery, calibration, runtime
  configuration, and external dependencies. Mesh generation is an attempted
  workflow step and is not guaranteed.
- The evidence manifest and audit log are not cryptographically chained,
  immutable, or independently secured.
- The code uses relative UI/data conventions and has not been validated on all
  operating systems.

## Development roadmap

- Add portable, isolated tests for image-processing and reconstruction flows.
- Improve configuration and error handling across desktop modules.
- Add sanitized, explicitly synthetic sample inputs and reproducible demos.
- Validate the end-to-end reconstruction path with documented environment and
  test data.
- Review dependency, model, and browser-asset licensing before distribution.

## Intellectual Property

CrimeScan is an ongoing forensic technology research and development project. Certain proprietary hardware designs, unpublished research components, and security-sensitive implementation details are intentionally excluded from this public repository. Publicly available components are provided for technical demonstration and review. Use and redistribution are governed by the applicable repository license and third-party licenses.

No repository license is included in this preparation copy.

## Contact and contributions

For project questions or proposed contributions, use the repository's GitHub
discussion or issue channels. Please do not include real case materials,
personal data, or credentials in public reports.
