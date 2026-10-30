"""Download the VitTrack ONNX model into assets/models/ (optional; needs an internet connection)."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import MODELS_DIR, VITTRACK_MODEL_PATH, VITTRACK_MODEL_URL  # noqa: E402


def main() -> int:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if VITTRACK_MODEL_PATH.is_file():
        print(f"Already present: {VITTRACK_MODEL_PATH}")
        return 0
    print(f"Downloading {VITTRACK_MODEL_URL}")
    try:
        with urllib.request.urlopen(VITTRACK_MODEL_URL, timeout=60) as response:
            data = response.read()
    except Exception as error:
        print(f"Download failed: {error}\nDownload the file manually from the OpenCV Zoo and put it in {MODELS_DIR}")
        return 1
    if len(data) < 100_000:  # a real model is about 1 MB; this is probably an error page
        print("The downloaded file is too small to be the model. Download it manually from the OpenCV Zoo.")
        return 1
    VITTRACK_MODEL_PATH.write_bytes(data)
    print(f"Saved {VITTRACK_MODEL_PATH} ({len(data) / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
