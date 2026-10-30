from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2

APP_NAME = "CVML Lab 10 - Single Object Tracking"
ORGANIZATION_NAME = "Sharif CVML Lab"

BASE_DIR = Path(__file__).resolve().parent
DEMO_VIDEO_PATH = BASE_DIR / "assets" / "demo.mp4"   # optional: the Demo button appears only if this file exists
MODELS_DIR = BASE_DIR / "assets" / "models"
VITTRACK_MODEL_PATH = MODELS_DIR / "object_tracking_vittrack_2023sep.onnx"
MIXFORMERV2_MODEL_PATH = MODELS_DIR / "mixformer_v2.onnx"
VITTRACK_MODEL_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/object_tracking_vittrack/"
    "object_tracking_vittrack_2023sep.onnx"
)

CAPTURE_WIDTH = 640
CAPTURE_HEIGHT = 480
TARGET_FPS = 30

DEFAULT_CAMERA_INDEX = 0
DEFAULT_THEME = "dark"

MIN_ROI_SIZE = 10

ALGORITHM_STUDENT = "student"
DEFAULT_ALGORITHM = ALGORITHM_STUDENT

TEMPLATE_METHODS = {
    "TM_CCOEFF_NORMED": cv2.TM_CCOEFF_NORMED,
    "TM_CCORR_NORMED": cv2.TM_CCORR_NORMED,
    "TM_SQDIFF_NORMED": cv2.TM_SQDIFF_NORMED,
}
DEFAULT_METHOD = "TM_CCOEFF_NORMED"
DEFAULT_SEARCH_SCALE_TENTHS = 30   # 3.0 x target size
DEFAULT_SCORE_THRESHOLD_PERCENT = 60
DEFAULT_UPDATE_TEMPLATE = False    # static template
DEFAULT_UPDATE_RATE_PERCENT = 20
DEFAULT_SHOW_SEARCH_REGION = True
DEFAULT_SHOW_TEMPLATE = True

DEFAULT_SETTINGS_MESSAGE = "Settings: Ready"

TRACKING_COLOR = (60, 220, 140)    # BGR, green
LOST_COLOR = (60, 60, 240)         # BGR, red
SEARCH_COLOR = (255, 200, 60)      # BGR, light blue

# ---- Loss handling: edit these two numbers here (they are intentionally not in the UI) ----
# After the target is lost, the tracker keeps searching for this many consecutive frames. If the target has not
# been found again by then, tracking is cancelled (the tracker is cleaned) and the application waits for a new
# selection. 0 = cancel immediately on the first lost frame. (30 frames = about 1 second at 30 FPS.)
LOST_TIMEOUT_FRAMES = 10
# After tracking was cancelled, the last (red) box stays on the screen for this many frames. No search or tracking
# runs during this time; it only keeps the last position visible. 0 = do not show it.
LOST_BOX_DISPLAY_FRAMES = 45

STATE_IDLE = "Idle"
STATE_TRACKING = "Tracking"
STATE_LOST = "Target Lost"

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff")
VIDEO_EXTENSIONS = (".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v")

FILE_FILTER = (
    "Media Files (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff "
    "*.mp4 *.avi *.mov *.mkv *.webm *.m4v);;"
    "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff);;"
    "Videos (*.mp4 *.avi *.mov *.mkv *.webm *.m4v);;"
    "All Files (*)"
)


@dataclass(frozen=True)
class TrackerParameters:
    search_scale: float
    method: int
    score_threshold: float
    update_template: bool
    update_rate: float
    show_search_region: bool
    show_template: bool
