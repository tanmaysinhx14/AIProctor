# AI Proctoring System

A real-time, webcam-based computer vision project for exploring exam-session monitoring. A FastAPI backend receives frames over a WebSocket, analyzes them with face, pose, gaze, hand, and object-detection components, and streams telemetry to a browser dashboard.

This is an experimental learning project. Its risk scores and event labels are automated signals, not findings of misconduct. Lighting, camera angle, accessibility needs, ordinary movement, and model errors can all affect detections. Any flagged event needs human review and context.

## GPU setup

On Windows systems with an NVIDIA GPU, the default `torch` requirement may install a CPU-only wheel. Verify the active environment before starting the server:

```powershell
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
```

For the RTX-enabled setup, install the CUDA PyTorch wheel in the project venv using the current command from the official PyTorch selector, then reinstall the remaining requirements. YOLO uses CUDA only when `torch.version.cuda` is non-empty and `torch.cuda.is_available()` is `True`; otherwise the application intentionally falls back to CPU.

## What it does

### Live video analysis

- Detects and tracks up to five faces with facial landmarks and temporal tracking.
- Estimates head pose (yaw, pitch, and roll), iris-based gaze direction, eye visibility, face orientation, and movement.
- Combines head, gaze, and orientation signals in a per-face attention state model (`FOCUSED`, `TRANSITIONING`, `LOOKING_AWAY`) with adaptive baselines and confidence checks.
- Detects hands near or covering the face.
- Uses YOLOv8 to detect people and phone-like objects. The default model maps `cell phone` directly and can probe related COCO classes such as `laptop`, `book`, `remote`, `mouse`, and `tv` as possible phone signals.
- Supports an optional, separately configured gadget model for audio-device detections.
- Checks frame quality and can warn about low light, a blurry or dirty camera, and a blocked view.
- Analyzes background motion and learns zones during calibration to help filter stationary scene activity.

### Risk signals and review tiers

The risk engine evaluates 11 rule types: multiple people, multiple faces, phone detected, audio device detected, face missing, face not facing the camera, extreme gaze, vertical head movement, horizontal head movement, high movement, and hand on face. Temporal activation and release gates, score smoothing, and repetition weighting help prevent a single noisy frame from driving the session state.

A separate event tier system organizes rule activations:

| Tier | Meaning in the application |
| --- | --- |
| 1 | A brief trigger is recorded in the session event log. |
| 2 | The same rule activates at least three times within a rolling 120-second window. |
| 3 | A configured high-severity rule remains active for a sustained period, or a configured combination of rules is active together. |

Tier labels are software-generated review cues. They do not establish intent or determine whether an exam rule was broken.

### Guided calibration

The dashboard can guide a user through eight stages before monitoring:

1. Neutral face and posture baseline
2. Gaze at screen center
3. Gaze toward the left edge
4. Gaze toward the right edge
5. Gaze toward the top edge
6. Gaze toward the bottom edge
7. Gentle vertical head movement
8. Hand-to-face gesture

The calibration manager checks collected samples and creates a session profile with personalized thresholds and learned background-motion zones. Calibration can also be cancelled or queried while connected.

### Adaptive processing and diagnostics

At session start, the backend selects a CPU, mid-range GPU, or high-performance GPU profile. Profiles set frame stride, target image size, face-detection interval, and object-detection rate. Feedback from CPU use and frame latency can increase or reduce the stride, and inference can fall back to CPU after a CUDA error.

The dashboard displays live risk and attention data, detections, warnings, event history, frame rate, dropped frames, per-stage timings, and available resource metrics. A threshold tuner can update supported risk, eye-tracking, and phone-detection thresholds during a session. Performance reports include metric summaries and a session timeline, and can be exported as JSON under `reports/`.

Risk snapshots are disabled by default in `config.py`. If enabled, the backend can include a limited number of captured images in the active session response when the configured score threshold is reached.

## Architecture

```text
Browser dashboard (frontend/index.html)
    ├── gets camera access in the browser
    ├── sends base64 JPEG frames and control commands
    └── renders streamed detections, risk signals, and metrics
                 │ WebSocket /ws
                 ▼
FastAPI application (main.py)
    ├── creates one ProctoringSession per WebSocket connection
    ├── uses bounded latest-frame queues to manage inference latency
    └── returns frame analysis and command responses
          │              │                │
          ▼              ▼                ▼
   vision/          tracking/        pipeline/ + hardware/
   perception,      face/person      hardware profiles and
   calibration,     association      adaptive scheduling
   risk and tiers
                 │
                 ▼
          utils/ reporting,
          smoothing and resources
```

## Tech stack

- Python 3.10 or newer
- FastAPI, Uvicorn, and WebSockets
- OpenCV and NumPy
- PyTorch and Ultralytics YOLOv8
- MediaPipe Face Mesh and Hands
- SciPy for assignment and distance calculations
- psutil for hardware and resource metrics
- Plain HTML, CSS, and JavaScript for the dashboard

## Run locally

Use Python 3.10 or newer. PyTorch installation depends on whether you want CPU inference or CUDA GPU inference; install the build that matches your machine first.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install the project dependencies from the manifest:

```bash
python -m pip install -r requirements.txt
```

`requirements.py` also exposes the direct dependencies as a Python `DEPENDENCIES` tuple for scripts and tooling. The manifest uses OpenCV's contrib build for MediaPipe compatibility and keeps NumPy below 2 for the pinned MediaPipe version. For CUDA, replace the default PyTorch build with one compatible with the installed CUDA driver. The bundled `yolov8n.pt` file is the default YOLO model. An audio-device model is optional and must be configured separately.

Start the server from the project root:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000), allow camera access, and select the camera in the dashboard. Run calibration before monitoring for session-personalized thresholds. The health endpoint is available at [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

## WebSocket interface

The WebSocket endpoint is `/ws`. The dashboard connects to it automatically. A frame message contains a base64-encoded JPEG and may include browser display dimensions:

```json
{
  "frame": "<base64-encoded-jpeg>",
  "client": {
    "viewportWidth": 1280,
    "viewportHeight": 720,
    "devicePixelRatio": 1
  }
}
```

Send control messages in place of a frame:

```json
{ "command": "start_calibration" }
{ "command": "cancel_calibration" }
{ "command": "calibration_status" }
{ "command": "reset_stats" }
{ "command": "set_thresholds", "thresholds": { "gaze_extreme_horizontal_threshold": 0.07 } }
{ "command": "get_thresholds" }
{ "command": "performance_report_status" }
{ "command": "performance_report" }
{ "command": "performance_report_export" }
{ "command": "performance_report_reset" }
```

Frame responses can include tracked faces and people, detected objects, warnings, risk score and rule breakdown, tier events, calibration progress, performance metrics, and optional risk snapshots. The Pydantic response definitions are in `models/schemas.py`.

## Project layout

```text
.
├── main.py                    # FastAPI routes and per-connection session orchestration
├── config.py                  # Central settings and default thresholds
├── frontend/
│   └── index.html             # Browser dashboard and camera client
├── hardware/
│   └── hardware_detector.py   # CPU/GPU capability detection and profiles
├── models/
│   ├── schemas.py              # Frame, response, and telemetry schemas
│   ├── face_detector.py        # Face-detector factory
│   ├── eye_tracker.py          # Eye-tracker factory
│   └── pose_model.py           # Head-pose factory
├── pipeline/
│   ├── scheduler.py            # Adaptive frame and inference scheduling
│   ├── frame_capture.py         # Reusable capture thread
│   └── inference_engine.py      # Reusable threaded inference engine
├── tracking/                    # Face and person tracking helpers
├── vision/                      # Detection, calibration, attention, risk, and tier logic
├── utils/                       # Metrics, reports, resource monitoring, and smoothing
├── test_ws.py                   # Local webcam/WebSocket client
├── yolov8n.pt                   # Default YOLOv8 model weights
└── reports/                     # JSON performance report output
```

## Configuration and development

`config.py` contains the frozen `Settings` dataclass used by the backend. Edit its defaults to change model paths, calibration behavior, risk thresholds, performance reporting, or snapshot behavior. `gadget_model_path` is empty by default; set it to a compatible model to enable optional audio-device detection.

`test_ws.py` is a small manual client that reads from the local webcam and prints selected response metrics. Start the server first, then run it in a second terminal:

```bash
python test_ws.py
```
