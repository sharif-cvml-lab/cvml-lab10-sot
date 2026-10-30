"""Fixed infrastructure: ready-made OpenCV trackers behind the same interface as sot.py.

Students do not modify this file. Every tracker here exposes the attributes the GUI needs
(`box`, `search_box`, `template`, `response`, `score`, `lost`) and the methods
`init(frame, roi)` and `update(frame) -> (box, score, lost)`.

Only information that the algorithm really provides is reported: `score` is None when the
algorithm has no tracking score, and `search_box` / `response` are None because the ready-made
trackers do not expose a search region or a response map.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np

from config import ALGORITHM_STUDENT, MIXFORMERV2_MODEL_PATH, VITTRACK_MODEL_PATH


@dataclass(frozen=True)
class AlgorithmInfo:
    key: str
    label: str            # text shown in the GUI
    short_name: str
    description: str
    available: bool
    reason: str           # why it is unavailable ("" when available)
    provides_score: bool
    score_note: str       # how to interpret the score ("" if none)


def _opencv_factory(key: str):
    """Return a zero-argument function that creates the OpenCV tracker, or None if missing."""
    if key == "csrt" and hasattr(cv2, "TrackerCSRT_create"):
        return cv2.TrackerCSRT_create
    if key == "kcf" and hasattr(cv2, "TrackerKCF_create"):
        return cv2.TrackerKCF_create
    if key == "mosse" and hasattr(cv2, "legacy") and hasattr(cv2.legacy, "TrackerMOSSE_create"):
        return cv2.legacy.TrackerMOSSE_create
    if key == "vittrack" and hasattr(cv2, "TrackerVit_create") and hasattr(cv2, "TrackerVit_Params"):
        def create_vit():
            params = cv2.TrackerVit_Params()
            params.net = str(VITTRACK_MODEL_PATH)
            return cv2.TrackerVit_create(params)
        return create_vit
    return None


def list_algorithms() -> list[AlgorithmInfo]:
    """All algorithms offered by the GUI, with their availability on this computer."""
    csrt = _opencv_factory("csrt") is not None
    kcf = _opencv_factory("kcf") is not None
    mosse = _opencv_factory("mosse") is not None
    vit_api = _opencv_factory("vittrack") is not None
    vit_model = VITTRACK_MODEL_PATH.is_file()
    vit_reason = ""
    if not vit_api:
        vit_reason = "needs OpenCV 4.9 or newer (cv2.TrackerVit)"
    elif not vit_model:
        vit_reason = f"model file not found: assets/models/{VITTRACK_MODEL_PATH.name} (see assets/models/README.md)"
    mf_reason = mixformerv2_unavailable_reason()
    return [
        AlgorithmInfo(
            ALGORITHM_STUDENT, "Student - Template Matching (sot.py)", "Student",
            "Your own template-matching tracker.", True, "", True,
            "Template-matching score of your tracker (depends on the selected method).",
        ),
        AlgorithmInfo(
            "csrt", "CSRT - classic, accurate", "CSRT",
            "Correlation filter with channel and spatial reliability; accurate but slower.",
            csrt, "" if csrt else "not available in this OpenCV build", False, "",
        ),
        AlgorithmInfo(
            "kcf", "KCF - classic, fast", "KCF",
            "Kernelized correlation filter; fast.",
            kcf, "" if kcf else "not available in this OpenCV build", False, "",
        ),
        AlgorithmInfo(
            "mosse", "MOSSE - very fast", "MOSSE",
            "Minimum output sum of squared error filter; the fastest, least accurate.",
            mosse, "" if mosse else "needs opencv-contrib-python (cv2.legacy)", False, "",
        ),
        AlgorithmInfo(
            "vittrack", "VitTrack - deep learning", "VitTrack",
            "Vision-transformer tracker (ONNX model); robust to appearance change.",
            vit_api and vit_model, vit_reason, True,
            "VitTrack's own confidence. It is specific to this method and not comparable with other scores.",
        ),
        AlgorithmInfo(
            "mixformerv2", "MixFormerV2 - transformer, most accurate", "MixFormerV2",
            "One-stream transformer tracker (NeurIPS 2023) run with ONNX Runtime; the most accurate option here.",
            mf_reason == "", mf_reason, True,
            "MixFormerV2's own confidence (0 to 1). It is specific to this method and not comparable with other scores.",
        ),
    ]


def algorithm_info(key: str) -> AlgorithmInfo:
    for info in list_algorithms():
        if info.key == key:
            return info
    raise KeyError(key)


class OpenCVTracker:
    """Adapter that gives a ready-made OpenCV tracker the same interface as SingleObjectTracker."""

    def __init__(self, key: str):
        self.key = key
        self._tracker = None
        self.template: np.ndarray | None = None   # not exposed by these algorithms
        self.box: tuple[int, int, int, int] | None = None
        self.search_box = None                    # not exposed by these algorithms
        self.response = None                      # not exposed by these algorithms
        self.score: float | None = None           # None = not provided by the algorithm
        self.lost = False

    def init(self, frame: np.ndarray, roi: tuple[int, int, int, int]) -> None:
        factory = _opencv_factory(self.key)
        if factory is None:
            raise RuntimeError(f"{self.key} is not available in this OpenCV build")
        tracker = factory()  # may raise, e.g. if the VitTrack model file is broken
        roi = tuple(int(v) for v in roi)
        tracker.init(frame, roi)
        self._tracker = tracker
        self.box = roi
        self.score = None
        self.lost = False

    def update(self, frame: np.ndarray):
        ok, bbox = self._tracker.update(frame)
        if ok:
            x, y, w, h = (int(round(v)) for v in bbox)
            self.box = (x, y, max(w, 1), max(h, 1))
        self.lost = not ok
        if self.key == "vittrack":
            self.score = float(self._tracker.getTrackingScore())
        return self.box, self.score, self.lost


# ----------------------------------------------------------------------------------------------
# MixFormerV2 (ONNX Runtime)
#
# Reference: Cui et al., "MixFormerV2: Efficient Fully Transformer Tracking", NeurIPS 2023 (MIT license),
# https://github.com/MCG-NJU/MixFormerV2. The pre/post-processing below follows the official tracker:
# RGB crops, ImageNet normalization, template crop 2.0x -> 112 px, search crop 4.5x -> 224 px,
# the box is the mean of the predicted boxes, and an online template is refreshed every 200 frames.
# The ONNX model has three inputs (img_t, img_ot, img_search) and two outputs (pred_boxes, pred_scores).
# ----------------------------------------------------------------------------------------------
MIXFORMER_TEMPLATE_FACTOR = 2.0
MIXFORMER_TEMPLATE_SIZE = 112
MIXFORMER_SEARCH_FACTOR = 4.5
MIXFORMER_SEARCH_SIZE = 224
MIXFORMER_UPDATE_INTERVAL = 200
MIXFORMER_ONLINE_SCORE = 0.5     # a new online template is accepted only above this confidence
MIXFORMER_LOST_SCORE = 0.3       # below this confidence the target is reported as lost
_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
_IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 1, 3)


def mixformerv2_unavailable_reason() -> str:
    """Empty string if MixFormerV2 can run, otherwise a short explanation."""
    try:
        import onnxruntime  # noqa: F401
    except Exception:
        return "needs the onnxruntime package (pip install onnxruntime)"
    if not MIXFORMERV2_MODEL_PATH.is_file():
        return f"model file not found: assets/models/{MIXFORMERV2_MODEL_PATH.name} (see assets/models/README.md)"
    return ""


def sample_target(frame: np.ndarray, box, search_area_factor: float, output_size: int):
    """Square crop centered on `box` (x, y, w, h), `search_area_factor` times the target size.

    Returns the crop resized to output_size x output_size (zero-padded where it leaves the frame)
    and the resize factor that was applied.
    """
    x, y, w, h = box
    crop_size = math.ceil(math.sqrt(w * h) * search_area_factor)
    if crop_size < 1:
        raise ValueError("the target box is too small")
    x1 = int(round(x + 0.5 * w - crop_size * 0.5))
    y1 = int(round(y + 0.5 * h - crop_size * 0.5))
    x2, y2 = x1 + crop_size, y1 + crop_size
    x1_pad, y1_pad = max(0, -x1), max(0, -y1)
    x2_pad, y2_pad = max(x2 - frame.shape[1] + 1, 0), max(y2 - frame.shape[0] + 1, 0)
    crop = frame[y1 + y1_pad:y2 - y2_pad, x1 + x1_pad:x2 - x2_pad, :]
    if crop.size == 0:
        raise ValueError("the target is outside the frame")
    crop = cv2.copyMakeBorder(crop, y1_pad, y2_pad, x1_pad, x2_pad, cv2.BORDER_CONSTANT)
    return cv2.resize(crop, (output_size, output_size)), output_size / crop_size


def _mixformer_input(patch_bgr: np.ndarray) -> np.ndarray:
    """BGR uint8 patch -> normalized RGB float32 tensor of shape (1, 3, H, W)."""
    rgb = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    rgb = (rgb - _IMAGENET_MEAN) / _IMAGENET_STD
    return np.ascontiguousarray(rgb.transpose(2, 0, 1)[None])


class MixFormerV2Tracker:
    """MixFormerV2 with the same interface as SingleObjectTracker (see OpenCVTracker)."""

    def __init__(self, session=None):
        self._session = session
        self.template = None
        self.box = None
        self.search_box = None
        self.response = None
        self.score: float | None = None
        self.lost = False
        self.lost_threshold = MIXFORMER_LOST_SCORE  # the GUI score threshold is applied here

    # ---- model loading
    def _load_session(self):
        reason = mixformerv2_unavailable_reason()
        if reason:
            raise RuntimeError(reason)
        import onnxruntime as ort

        session = ort.InferenceSession(str(MIXFORMERV2_MODEL_PATH), providers=["CPUExecutionProvider"])
        self._bind_names(session)
        return session

    def _bind_names(self, session) -> None:
        """Find which model input/output is which, and fail clearly for a model that does not fit."""
        inputs = {i.name: i for i in session.get_inputs()}
        if {"img_t", "img_ot", "img_search"} <= set(inputs):
            self._in_template, self._in_online, self._in_search = "img_t", "img_ot", "img_search"
        elif len(inputs) == 3:  # other names: the two small inputs are the templates, the large one is the search image
            ordered = sorted(inputs.values(), key=lambda i: (i.shape[-1] if isinstance(i.shape[-1], int) else 0))
            self._in_template, self._in_online, self._in_search = (ordered[0].name, ordered[1].name, ordered[2].name)
        else:
            raise RuntimeError(f"unexpected model inputs {list(inputs)}; expected img_t, img_ot, img_search")
        for name, expected in ((self._in_template, MIXFORMER_TEMPLATE_SIZE), (self._in_online, MIXFORMER_TEMPLATE_SIZE),
                               (self._in_search, MIXFORMER_SEARCH_SIZE)):
            size = inputs[name].shape[-1]
            if isinstance(size, int) and size != expected:
                raise RuntimeError(f"model input {name} has size {size}, expected {expected} (a different MixFormerV2 variant?)")
        outputs = [o.name for o in session.get_outputs()]
        if len(outputs) < 2:
            raise RuntimeError(f"unexpected model outputs {outputs}; expected pred_boxes and pred_scores")
        self._out_boxes = "pred_boxes" if "pred_boxes" in outputs else outputs[0]
        self._out_scores = "pred_scores" if "pred_scores" in outputs else outputs[1]

    # ---- tracker interface
    def init(self, frame: np.ndarray, roi) -> None:
        if self._session is None:
            self._session = self._load_session()
        else:
            self._bind_names(self._session)
        x, y, w, h = (float(v) for v in roi)
        patch, _ = sample_target(frame, (x, y, w, h), MIXFORMER_TEMPLATE_FACTOR, MIXFORMER_TEMPLATE_SIZE)
        self._template = _mixformer_input(patch)
        self._online_template = self._template
        self._online_max_template = self._template
        self._max_score = -1.0
        self._frame_id = 0
        self._state = [x, y, w, h]
        self.template = patch
        self.box = tuple(int(round(v)) for v in self._state)
        self.score = None
        self.lost = False

    def update(self, frame: np.ndarray):
        frame_h, frame_w = frame.shape[:2]
        self._frame_id += 1
        patch, resize_factor = sample_target(frame, self._state, MIXFORMER_SEARCH_FACTOR, MIXFORMER_SEARCH_SIZE)
        outputs = self._session.run(
            [self._out_boxes, self._out_scores],
            {self._in_template: self._template, self._in_online: self._online_template,
             self._in_search: _mixformer_input(patch)},
        )
        boxes = np.asarray(outputs[0], dtype=np.float32).reshape(-1, 4)
        score = float(np.asarray(outputs[1], dtype=np.float32).reshape(-1)[0])

        # mean of the predicted boxes: (cx, cy, w, h) relative to the search crop -> frame coordinates
        cx, cy, w, h = (boxes.mean(axis=0) * MIXFORMER_SEARCH_SIZE / resize_factor).tolist()
        prev_cx = self._state[0] + 0.5 * self._state[2]
        prev_cy = self._state[1] + 0.5 * self._state[3]
        half_side = 0.5 * MIXFORMER_SEARCH_SIZE / resize_factor
        real_cx, real_cy = cx + (prev_cx - half_side), cy + (prev_cy - half_side)
        self._state = self._clip_box([real_cx - 0.5 * w, real_cy - 0.5 * h, w, h], frame_h, frame_w, margin=10)

        # online template: remember the most confident recent appearance, adopt it every update_interval frames
        if score > MIXFORMER_ONLINE_SCORE and score > self._max_score:
            patch_t, _ = sample_target(frame, self._state, MIXFORMER_TEMPLATE_FACTOR, MIXFORMER_TEMPLATE_SIZE)
            self._online_max_template = _mixformer_input(patch_t)
            self._max_score = score
        if self._frame_id % MIXFORMER_UPDATE_INTERVAL == 0:
            self._online_template = self._online_max_template
            self._max_score = -1.0
            self._online_max_template = self._template

        self.box = tuple(int(round(v)) for v in self._state)
        self.score = score
        self.lost = score < self.lost_threshold
        return self.box, self.score, self.lost

    @staticmethod
    def _clip_box(box, height, width, margin=0):
        x1, y1, w, h = box
        x2, y2 = x1 + w, y1 + h
        x1, x2 = min(max(0, x1), width - margin), min(max(margin, x2), width)
        y1, y2 = min(max(0, y1), height - margin), min(max(margin, y2), height)
        return [x1, y1, max(margin, x2 - x1), max(margin, y2 - y1)]


def create_tracker(key: str):
    """Create the tracker object for an algorithm key (the student's class or an OpenCV adapter)."""
    if key == ALGORITHM_STUDENT:
        from sot import SingleObjectTracker
        return SingleObjectTracker()
    if key == "mixformerv2":
        return MixFormerV2Tracker()
    return OpenCVTracker(key)
