from __future__ import annotations

import threading
import time

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

from annotation import annotate_tracking, render_notice_view, render_search_view
from config import (
    CAPTURE_HEIGHT,
    CAPTURE_WIDTH,
    STATE_IDLE,
    STATE_LOST,
    STATE_TRACKING,
    ALGORITHM_STUDENT,
    LOST_BOX_DISPLAY_FRAMES,
    LOST_TIMEOUT_FRAMES,
    TARGET_FPS,
    TrackerParameters,
)
from sot import SingleObjectTracker
from trackers import MixFormerV2Tracker, algorithm_info, create_tracker


def bgr_to_qimage(frame: np.ndarray) -> QImage:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    height, width, channels = rgb.shape
    return QImage(rgb.data, width, height, channels * width, QImage.Format.Format_RGB888).copy()


class VideoThread(QThread):
    """Capture frames (camera, image or video) and run the selected tracker off the GUI thread."""

    # tracking view, search view, info dict, fps
    frame_ready = pyqtSignal(object, object, object, float)
    status_changed = pyqtSignal(str)
    processing_error = pyqtSignal(str)
    algorithm_failed = pyqtSignal(str, str, str)  # failed key, message, algorithm that stays active

    def __init__(
        self,
        camera_index: int = 0,
        source_type: str = "camera",
        file_path: str = "",
        algorithm: str = ALGORITHM_STUDENT,
        parent=None,
    ):
        super().__init__(parent)
        self._camera_index = camera_index
        self._source_type = source_type
        self._file_path = file_path
        self._parameters: TrackerParameters | None = None
        self._lock = threading.Lock()
        self._running = threading.Event()
        self._running.set()
        self._restart = threading.Event()
        self._clear = threading.Event()
        self._selecting = False
        self._pending_roi: tuple[int, int, int, int] | None = None
        self._algorithm = algorithm            # the algorithm in use
        self._pending_algorithm: str | None = None
        self._paused = False
        self._last_status = ""
        self._last_error = ""

    # ---- commands from the GUI
    def set_parameters(self, parameters: TrackerParameters) -> None:
        with self._lock:
            self._parameters = parameters

    def set_paused(self, paused: bool) -> None:
        with self._lock:
            self._paused = paused

    def restart_source(self) -> None:
        self._restart.set()

    def begin_selection(self) -> None:
        """Freeze the current frame so the user can draw a rectangle on it."""
        with self._lock:
            self._selecting = True

    def cancel_selection(self) -> None:
        with self._lock:
            self._selecting = False

    def set_roi(self, roi: tuple[int, int, int, int]) -> None:
        with self._lock:
            self._pending_roi = roi
            self._selecting = False

    def set_algorithm(self, key: str) -> None:
        """Switch the tracking algorithm; an active target is re-initialized with its last box."""
        with self._lock:
            self._pending_algorithm = key

    def _take_pending_algorithm(self):
        with self._lock:
            pending, self._pending_algorithm = self._pending_algorithm, None
        return pending

    def clear_target(self) -> None:
        self._clear.set()

    def _snapshot(self):
        with self._lock:
            return self._parameters, self._paused, self._selecting, self._pending_roi

    def _consume_roi(self) -> None:
        with self._lock:
            self._pending_roi = None

    def _emit_status(self, message: str) -> None:
        if message != self._last_status:
            self._last_status = message
            self.status_changed.emit(message)

    def _emit_error(self, message: str) -> None:
        if message != self._last_error:
            self._last_error = message
            self.processing_error.emit(message)

    def _open_source(self):
        """Return (capture, still_image). Exactly one of them is not None on success."""
        if self._source_type == "file":
            image = cv2.imread(self._file_path)
            if image is not None:
                return None, image
            cap = cv2.VideoCapture(self._file_path)
        else:
            cap = cv2.VideoCapture(self._camera_index)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
        if not cap.isOpened():
            cap.release()
            return None, None
        return cap, None

    @staticmethod
    def _apply_parameters(tracker, parameters: TrackerParameters) -> None:
        if isinstance(tracker, MixFormerV2Tracker):
            tracker.lost_threshold = parameters.score_threshold  # the only setting that applies to MixFormerV2
            return
        if not isinstance(tracker, SingleObjectTracker):
            return  # these settings belong to the student's algorithm only
        tracker.search_scale = parameters.search_scale
        tracker.method = parameters.method
        tracker.score_threshold = parameters.score_threshold
        tracker.update_template = parameters.update_template
        tracker.update_rate = parameters.update_rate

    def _render(self, frame, tracker, state, score, parameters, displacement, fps, ghost_box=None) -> None:
        info_alg = algorithm_info(self._algorithm)
        tracking_view = annotate_tracking(
            frame, state, tracker.box if state != STATE_IDLE else None, score,
            tracker.search_box, tracker.template,
            parameters.show_search_region, parameters.show_template, ghost_box,
        )
        if state == STATE_IDLE or isinstance(tracker, SingleObjectTracker):
            search_view = render_search_view(
                frame, state, tracker.box if state != STATE_IDLE else None,
                tracker.search_box, tracker.response, parameters.method,
            )
        else:
            search_view = render_notice_view(
                "Search View not available",
                [f"{info_alg.short_name} does not expose a search region",
                 "or a matching map, so there is nothing to display.",
                 "Select 'Student - Template Matching' to see them."],
            )
        info = {
            "state": state,
            "algorithm": self._algorithm,
            "algorithm_name": info_alg.short_name,
            "score": None if score is None else float(score),
            "score_note": info_alg.score_note,
            "box": tuple(int(v) for v in tracker.box) if (state != STATE_IDLE and tracker.box is not None) else None,
            "displacement": displacement,
            "stopped": state == STATE_IDLE and ghost_box is not None,
        }
        self.frame_ready.emit(bgr_to_qimage(tracking_view), bgr_to_qimage(search_view), info, fps)

    def run(self) -> None:
        tracker = create_tracker(self._algorithm)
        state = STATE_IDLE
        score = 0.0
        displacement = (0, 0)
        cap = None
        still_image = None
        last_frame = None
        lost_frames = 0       # consecutive frames in which the target is lost
        ghost_box = None      # last box of a cancelled track, displayed only
        ghost_left = 0        # frames left to display it
        frame_period = 1.0 / TARGET_FPS

        def drop_target(show_box=None):
            """Clean the tracker and wait for a new selection; optionally keep showing the last box for a while."""
            nonlocal tracker, state, score, lost_frames, ghost_box, ghost_left
            tracker, state, score = create_tracker(self._algorithm), STATE_IDLE, 0.0
            lost_frames = 0
            ghost_left = LOST_BOX_DISPLAY_FRAMES if show_box is not None else 0
            ghost_box = show_box if ghost_left > 0 else None

        try:
            while self._running.is_set():
                if self._restart.is_set():
                    self._restart.clear()
                    if cap is not None:
                        cap.release()
                    cap, still_image, last_frame = None, None, None
                    drop_target()
                if self._clear.is_set():
                    self._clear.clear()
                    drop_target()

                pending_algorithm = self._take_pending_algorithm()
                if pending_algorithm is not None and pending_algorithm != self._algorithm:
                    try:
                        new_tracker = create_tracker(pending_algorithm)
                        if state != STATE_IDLE and tracker.box is not None and last_frame is not None:
                            new_tracker.init(last_frame, tracker.box)  # continue with the same target
                            score = 1.0 if isinstance(new_tracker, SingleObjectTracker) else None
                            state = STATE_TRACKING
                            lost_frames = 0
                        tracker, self._algorithm = new_tracker, pending_algorithm
                        self._emit_error("")
                        self._emit_status(f"Algorithm: {algorithm_info(self._algorithm).short_name}")
                    except Exception as error:  # e.g. a broken VitTrack model file: keep the old tracker
                        self.algorithm_failed.emit(pending_algorithm, f"{type(error).__name__}: {error}", self._algorithm)

                parameters, paused, selecting, pending_roi = self._snapshot()
                if parameters is None:
                    time.sleep(0.05)
                    continue
                self._apply_parameters(tracker, parameters)

                if cap is None and still_image is None:
                    cap, still_image = self._open_source()
                    if cap is None and still_image is None:
                        self._emit_status("Source is unavailable. Retrying...")
                        time.sleep(1.0)
                        continue
                    self._emit_status("Source connected")

                loop_started = time.perf_counter()
                frozen = paused or selecting
                if frozen and last_frame is not None:
                    frame = last_frame
                elif still_image is not None:
                    frame = still_image
                else:
                    ret, frame = cap.read()
                    if not ret:
                        if self._source_type == "file":  # video file: loop, the target must be selected again
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            drop_target()
                            self._emit_status("Video restarted. Select the target again.")
                            ret, frame = cap.read()
                        if not ret:
                            self._emit_status("Frame read failed. Reconnecting...")
                            cap.release()
                            cap = None
                            time.sleep(0.25)
                            continue
                    last_frame = frame

                if pending_roi is not None:
                    self._consume_roi()
                    try:
                        tracker = create_tracker(self._algorithm)
                        self._apply_parameters(tracker, parameters)
                        tracker.init(frame, pending_roi)
                        state = STATE_TRACKING
                        score = 1.0 if isinstance(tracker, SingleObjectTracker) else None
                        lost_frames, ghost_box, ghost_left = 0, None, 0
                        self._emit_error("")
                        self._emit_status("Tracking")
                    except Exception as error:
                        state = STATE_IDLE
                        self._emit_error(f"init: {type(error).__name__}: {error}")
                        if self._algorithm != ALGORITHM_STUDENT:
                            failed_key = self._algorithm
                            self._algorithm = ALGORITHM_STUDENT
                            tracker = create_tracker(ALGORITHM_STUDENT)
                            self.algorithm_failed.emit(failed_key, f"{type(error).__name__}: {error}", self._algorithm)
                elif state != STATE_IDLE and not frozen:
                    previous = tracker.box
                    try:
                        box, score, lost = tracker.update(frame)
                        state = STATE_LOST if lost else STATE_TRACKING
                        if previous is not None and box is not None:
                            displacement = (int(box[0] - previous[0]), int(box[1] - previous[1]))
                        self._emit_error("")
                    except Exception as error:  # a bug in the student's code must not kill the app
                        self._emit_error(f"update: {type(error).__name__}: {error}")
                        state = STATE_IDLE
                    if state == STATE_LOST:
                        lost_frames += 1
                        if lost_frames > LOST_TIMEOUT_FRAMES:  # give up: clean the tracker, wait for a new target
                            drop_target(show_box=tracker.box)
                            self._emit_status("Target lost - tracking stopped. Select the target again (S).")
                        else:
                            self._emit_status("Target Lost")
                    else:
                        lost_frames = 0
                        if state == STATE_TRACKING and self._last_status == "Target Lost":
                            self._emit_status("Tracking")
                elif state == STATE_IDLE and ghost_box is not None and not frozen:
                    ghost_left -= 1  # only the last red box is shown; nothing is searched
                    if ghost_left <= 0:
                        ghost_box = None

                if selecting:
                    ghost_box, ghost_left = None, 0
                    self._emit_status("Draw a rectangle around the target")
                elif paused:
                    self._emit_status("Paused")

                elapsed = time.perf_counter() - loop_started
                fps = 1.0 / elapsed if elapsed > 0 else TARGET_FPS
                self._render(frame, tracker, state, score, parameters, displacement, fps, ghost_box)
                time.sleep(max(0.0, frame_period - (time.perf_counter() - loop_started)))
        finally:
            if cap is not None:
                cap.release()
            self._emit_status("Source stopped")

    def stop(self) -> None:
        self._running.clear()
        self.wait()
