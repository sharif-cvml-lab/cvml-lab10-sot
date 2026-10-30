from __future__ import annotations

import cv2
import numpy as np


class SingleObjectTracker:
    def __init__(
        self,
        search_scale: float = 3.0,
        method: int = cv2.TM_CCOEFF_NORMED,
        score_threshold: float = 0.6,
        update_template: bool = False,
        update_rate: float = 0.2,
    ):
        """Already implemented. Do NOT modify.

        search_scale:    the search region is search_scale times larger than the target box.
        method:          OpenCV template-matching constant (cv2.TM_CCOEFF_NORMED,
                         cv2.TM_CCORR_NORMED or cv2.TM_SQDIFF_NORMED).
        score_threshold: tracking is valid only if the best-match score reaches this value.
        update_template: False = static template, True = adaptive template.
        update_rate:     blending weight of the new patch when the template is updated.

        The GUI changes these five attributes live, so always read them from self.
        """
        self.search_scale = search_scale
        self.method = method
        self.score_threshold = score_threshold
        self.update_template = update_template
        self.update_rate = update_rate

        self.template: np.ndarray | None = None              # current template (BGR image)
        self.box: tuple[int, int, int, int] | None = None    # last valid box (x, y, w, h)
        self.search_box: tuple[int, int, int, int] | None = None  # region searched in this frame
        self.response: np.ndarray | None = None              # matching map (only for display)
        self.score = 0.0
        self.lost = False

    def init(self, frame: np.ndarray, roi: tuple[int, int, int, int]) -> None:
        """
        TODO: Initialize the tracker from the region selected by the user.

        IMPORTANT:

        - This is the only file students should modify.
        - Keep the class name, __init__ and the signatures of init() and update() unchanged.
        - Do not add other top-level functions or classes to this file.
        - Do not use cv2.Tracker* classes (KCF, CSRT, ...) or any other ready-made tracker.
          You may use cv2.matchTemplate and cv2.minMaxLoc.

        Called once, when the user finishes drawing a rectangle on the first frame.

        Inputs:

            frame: BGR image, shape (H, W, 3)
            roi:   (x, y, w, h) in pixels, always inside the frame and at least 10x10

        Expected implementation sequence:

        1. Cut the initial template out of the frame (copy it!) and store it in self.template.
        2. Store the box as self.box = roi and also as self.search_box = roi.
        3. Reset the state: self.score = 1.0, self.lost = False, self.response = None.
        """
        pass

    def update(self, frame: np.ndarray) -> tuple[tuple[int, int, int, int], float, bool]:
        """
        TODO: Find the target in a new frame with template matching.

        Called once per frame after init().

        Input:

            frame: BGR image, shape (H, W, 3)

        Return exactly this tuple:

            (box, score, lost)
            box:   (x, y, w, h) of the target (the last valid box when the target is lost)
            score: best-match score in [0, 1], higher is better, for every method
            lost:  True if the best score is below self.score_threshold

        Expected implementation sequence:

        1. Search region: a rectangle centered on the center of self.box with size
           self.search_scale times the box size. Clip it to the frame borders and store it
           in self.search_box as (x, y, w, h).
        2. If the clipped search region is smaller than the template, the target cannot be
           found: set self.lost = True, self.score = 0.0 and return.
        3. Template matching: cv2.matchTemplate(search_image, self.template, self.method).
           Keep the result in self.response (the GUI displays it).
        4. Best match: cv2.minMaxLoc(response). For cv2.TM_SQDIFF_NORMED the BEST value is the
           minimum (and score = 1 - minimum); for the other methods it is the maximum.
        5. If score < self.score_threshold, the result is not valid: set self.lost = True and
           return the OLD box (do not move it and do not touch the template). The tracker keeps
           searching around the last valid box in the next frames, so it can find the target
           again after a short occlusion.
        6. Otherwise convert the best location (relative to the search region) into frame
           coordinates, set the new self.box (same size as the template) and self.lost = False.
        7. Adaptive template: if self.update_template is True, blend the new patch into the
           template: template = (1 - update_rate) * template + update_rate * patch.

        Keep the implementation deterministic and free of GUI code.
        """
        return self.box, self.score, self.lost
