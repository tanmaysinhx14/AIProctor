## Done

- Confirmed the active venv has `torch 2.15.0+cpu`, so YOLO cannot access CUDA.
- Added backend frame-processing error reporting so inference failures no longer silently stop the WebSocket pipeline.
- Added frontend handling for backend frame-processing errors.
- Documented the CUDA/PyTorch verification and installation requirement.
- `main.py` and `vision/object_detector.py` pass Python compilation checks.

## Next

- Install a CUDA-enabled PyTorch wheel in `.venv` and verify `torch.cuda.is_available()` is `True`.
- Start the app and confirm the first response reports `metrics.yoloDevice` as `cuda:0` and processed-frame stats increase.

## Blockers

- The current environment is CPU-only; installing the CUDA wheel requires package download/installation outside the code patch.
