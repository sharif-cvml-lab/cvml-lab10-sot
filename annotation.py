from __future__ import annotations

import cv2
import numpy as np

from config import LOST_COLOR, SEARCH_COLOR, STATE_IDLE, STATE_LOST, TRACKING_COLOR


def annotate_tracking(
    frame: np.ndarray,
    state: str,
    box,
    score,
    search_box,
    template,
    show_search_region: bool,
    show_template: bool,
    ghost_box=None,
) -> np.ndarray:
    """Tracking View: bounding box, status text, optional search region and template thumbnail.

    `ghost_box` is the last box of a target whose tracking was cancelled after a loss: it is only displayed.
    """
    output = frame.copy()
    if state == STATE_IDLE and ghost_box is not None:
        x, y, w, h = (int(v) for v in ghost_box)
        cv2.rectangle(output, (x, y), (x + w, y + h), LOST_COLOR, 2)
        cv2.putText(output, "LOST", (x, max(20, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, LOST_COLOR, 2, cv2.LINE_AA)
        cv2.putText(output, "TARGET LOST - tracking stopped. Select the target again (S)", (16, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, LOST_COLOR, 2, cv2.LINE_AA)
        return output
    if state == STATE_IDLE or box is None:
        cv2.putText(output, "Select a target (S)", (16, 32), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (255, 255, 255), 2, cv2.LINE_AA)
        return output

    lost = state == STATE_LOST
    color = LOST_COLOR if lost else TRACKING_COLOR
    if show_search_region and search_box is not None:
        sx, sy, sw, sh = (int(v) for v in search_box)
        cv2.rectangle(output, (sx, sy), (sx + sw, sy + sh), SEARCH_COLOR, 1)
    x, y, w, h = (int(v) for v in box)
    cv2.rectangle(output, (x, y), (x + w, y + h), color, 2)
    label = "LOST" if lost else "Target"
    if score is not None:  # algorithms without a score show no number (nothing is invented)
        label += f" {score:.2f}"
    cv2.putText(output, label, (x, max(20, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
    if lost:
        cv2.putText(output, "TARGET LOST - press S to select again", (16, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, LOST_COLOR, 2, cv2.LINE_AA)

    if show_template and template is not None and template.size:
        th = 72
        tw = max(1, int(template.shape[1] * th / template.shape[0]))
        thumb = cv2.resize(template, (tw, th))
        y0, x0 = output.shape[0] - th - 12, 12
        if y0 >= 0 and x0 + tw < output.shape[1]:
            output[y0:y0 + th, x0:x0 + tw] = thumb
            cv2.rectangle(output, (x0, y0), (x0 + tw, y0 + th), (255, 255, 255), 1)
            cv2.putText(output, "template", (x0, y0 - 4), cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, (255, 255, 255), 1, cv2.LINE_AA)
    return output


def render_search_view(
    frame: np.ndarray,
    state: str,
    box,
    search_box,
    response,
    method: int,
    out_size=(480, 360),
) -> np.ndarray:
    """Search View: the region searched by the tracker, the best match, and the matching map."""
    canvas = np.zeros((out_size[1], out_size[0], 3), np.uint8)
    if state == STATE_IDLE or search_box is None or box is None:
        cv2.putText(canvas, "No target selected", (20, out_size[1] // 2), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (200, 200, 200), 2, cv2.LINE_AA)
        return canvas

    sx, sy, sw, sh = (int(v) for v in search_box)
    crop = frame[sy:sy + sh, sx:sx + sw]
    if crop.size == 0:
        return canvas
    scale = min(out_size[0] / crop.shape[1], out_size[1] / crop.shape[0])
    new_w, new_h = max(1, int(crop.shape[1] * scale)), max(1, int(crop.shape[0] * scale))
    canvas[:new_h, :new_w] = cv2.resize(crop, (new_w, new_h))

    x, y, w, h = (int(v) for v in box)
    color = LOST_COLOR if state == STATE_LOST else TRACKING_COLOR
    p1 = (int((x - sx) * scale), int((y - sy) * scale))
    p2 = (int((x - sx + w) * scale), int((y - sy + h) * scale))
    cv2.rectangle(canvas, p1, p2, color, 2)
    cv2.putText(canvas, "search region", (6, out_size[1] - 8), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, SEARCH_COLOR, 1, cv2.LINE_AA)

    if response is not None and response.size:
        resp = response.astype(np.float32)
        if method == cv2.TM_SQDIFF_NORMED:
            resp = 1.0 - resp  # make "brighter = better" for every method
        resp = np.clip(resp, 0.0, 1.0)
        heat = cv2.applyColorMap((resp * 255).astype(np.uint8), cv2.COLORMAP_JET)
        inset_w = out_size[0] // 3
        inset_h = max(1, int(heat.shape[0] * inset_w / heat.shape[1]))
        inset_h = min(inset_h, out_size[1] // 2)
        heat = cv2.resize(heat, (inset_w, inset_h), interpolation=cv2.INTER_NEAREST)
        x0, y0 = out_size[0] - inset_w - 6, out_size[1] - inset_h - 6
        canvas[y0:y0 + inset_h, x0:x0 + inset_w] = heat
        cv2.rectangle(canvas, (x0, y0), (x0 + inset_w, y0 + inset_h), (255, 255, 255), 1)
        cv2.putText(canvas, "matching map", (x0, y0 - 4), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (255, 255, 255), 1, cv2.LINE_AA)
    return canvas


def render_notice_view(title: str, lines: list[str], out_size=(480, 360)) -> np.ndarray:
    """Search View for algorithms that have no search region or response map to show."""
    canvas = np.zeros((out_size[1], out_size[0], 3), np.uint8)
    y = out_size[1] // 2 - 20 * len(lines) // 2 - 10
    cv2.putText(canvas, title, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    for line in lines:
        y += 28
        cv2.putText(canvas, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
    return canvas
