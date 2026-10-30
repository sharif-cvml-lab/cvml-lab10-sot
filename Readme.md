# Lab10_SOT

Welcome to the tenth assignment of the Computer Vision and Machine Learning lab course!

This project provides a real-time PyQt6 application ("Single Object Tracking Playground"). You select one object with the mouse and the application follows it, frame by frame, using **template matching**. The goal of this lab is to understand how a very simple tracker works, and where it fails: occlusion, appearance change, similar objects and **template drift**.

## 🎯 Assignment Objectives

In this lab you will complete two methods of one class located in `sot.py`:

```
SingleObjectTracker.init(frame, roi)
SingleObjectTracker.update(frame)
```

Students should modify only `sot.py`. Do not modify `main.py`, `gui.py`, `video_thread.py`, `annotation.py`, `config.py`, or any other project file. The constructor of `SingleObjectTracker` is already implemented; leave it unchanged.

The expected processing pipeline is:

```
User draws a rectangle (ROI) on the first frame
     ↓
init():   cut the initial Template out of the frame
     ↓
For every new frame:
update(): Search Region around the last box
     ↓
          Template Matching (cv2.matchTemplate)
     ↓
          Best Match and Tracking Score
     ↓
          score >= threshold ?  yes → new Bounding Box (and optional Template update)
                                no  → Target Lost, keep the last box
```

## ✨ Features

- Real-time tracking from the bundled demo video (`assets/demo.mp4`, replaceable), a webcam, or any video/image file.
- **Several tracking algorithms in one application:** your own template-matching tracker (`sot.py`) and ready-made OpenCV trackers (CSRT, KCF, MOSSE, VitTrack, MixFormerV2) to compare accuracy and speed. Switching the algorithm while tracking continues with the same target.
- Target selection with the mouse: click **Select Target** (or press `S`), then drag a rectangle on the frozen frame.
- **Original / Tracking View:** bounding box, tracking score, status (Tracking / Target Lost), optional search region and template thumbnail.
- **Search View:** the region searched by your tracker, the best match, and the matching map (heat map). Ready-made trackers do not expose these, so the view says so instead of showing invented data.
- **Tracking Information:** algorithm, state, tracking score (only if the algorithm has one), position, size, displacement and FPS.
- Live tuning: search-region size, template-matching method, score threshold, static or adaptive template, and the template update rate.
- When the score drops below the threshold the tracker reports **Target Lost** and keeps searching for a limited time. If the target is not found again, tracking is cancelled and the tracker waits for a new selection (see *Loss handling*). You can select the target again at any time.
- Dark mode and light mode, full-screen mode, responsive scaling.
- Pause, restart, reset-to-default button and automatic restoration of settings.

## 🛠️ Setup & Installation

1. Clone the repository and navigate to the project directory.

2. Create a virtual environment (recommended):

```
python -m venv venv
```

Activate it on Linux/macOS:

```
source venv/bin/activate
```

On Windows PowerShell:

```
venv\Scripts\Activate.ps1
```

3. Install the required dependencies:

```
pip install -r requirements.txt
```

4. Run the application:

```
python main.py
```

The application starts with `assets/demo.mp4` (or with the webcam if that file is absent). Use **Webcam**, or **Browse** and **Upload**, to change the source.

Optional: the VitTrack and MixFormerV2 algorithms need a model file in `assets/models/` (see `assets/models/README.md`).

## 🎮 Using the Application

Until you finish `init` and `update`, the **Student** algorithm shows no box (placeholder behavior). The ready-made trackers work from the start, so you can try them first.

- **Search region:** how many times larger than the target the searched area is. Too small: fast objects escape. Too large: slower and easier to confuse with similar objects.
- **Method:** compare `TM_CCOEFF_NORMED`, `TM_CCORR_NORMED` and `TM_SQDIFF_NORMED` on the same video. Remember that for `TM_SQDIFF_NORMED` the best match is the minimum.
- **Score threshold:** below it the result is not trusted and the target is declared lost.
- **Adaptive template:** the template is blended with the newest patch. It follows slow appearance changes but can drift away from the object after a wrong match. Increase the update rate to see drift faster.

### Loss handling

Two numbers at the top of the loss section of `config.py` (not in the UI) control what happens after the target is lost:

| Constant | Meaning |
|----------|---------|
| `LOST_TIMEOUT_FRAMES` (default 10) | The tracker keeps searching for this many consecutive lost frames. If the target has not been found by then, tracking is cancelled: the tracker is cleaned and waits for a new selection. This stops a tracker from locking onto some other area after a long loss. `0` cancels immediately on the first lost frame. |
| `LOST_BOX_DISPLAY_FRAMES` (default 45) | After tracking was cancelled, the last (red) box stays on the screen for this many frames. No search or tracking runs during this time, the box is only displayed. `0` shows nothing. |

At 30 FPS, 30 frames are about one second. These values are independent of the algorithm and apply to all of them.

### Ready-made trackers

| Algorithm | Character | Tracking score | Search View / matching map |
|-----------|-----------|----------------|----------------------------|
| Student (`sot.py`) | your template matching | yes (depends on the method) | yes |
| CSRT | classic, accurate, slower | not provided | not provided |
| KCF | classic, fast | not provided | not provided |
| MOSSE | very fast, least accurate (needs `opencv-contrib-python`) | not provided | not provided |
| VitTrack | deep learning, small model (needs its ONNX file, OpenCV 4.9+) | yes, **VitTrack-specific**: not comparable with other scores | not provided |
| MixFormerV2 | transformer, the most accurate (needs `onnxruntime` and its ONNX file) | yes, **MixFormerV2-specific**: not comparable with other scores | not provided |

Algorithms that are not available on your computer are greyed out in the list, with the reason. The settings of the **Student Algorithm Settings** box (search region, method, template update) apply to your tracker only. The **Score threshold** of the *Lost Detection* box applies to your tracker and to MixFormerV2; CSRT, KCF, MOSSE and VitTrack use their own built-in decision. When a ready-made tracker loses the target the state becomes **Target Lost**; select the target again to continue.

If your methods raise an exception the application keeps running and shows the error in the status bar.

## 📂 Repository Structure

```
cvml-lab10-sot/
├── .gitignore
├── Readme.md
├── requirements.txt
├── main.py
├── gui.py
├── video_thread.py
├── annotation.py
├── trackers.py
├── config.py
├── assets/
│   ├── README.md
│   ├── demo.mp4              # placeholder video: replace it with a real one (same name)
│   └── models/
│       └── README.md         # where the optional VitTrack / MixFormerV2 models go
├── tools/
│   └── download_models.py    # downloads the VitTrack model (optional)
└── sot.py                    # The only file students should modify
```

### Module responsibilities

- `main.py` — application entry point only.
- `gui.py` — PyQt6 user interface, mouse ROI selection, controls, themes, persistence, and rendering.
- `video_thread.py` — capture loop, target state (Idle / Tracking / Target Lost) and calls to your tracker.
- `annotation.py` — Tracking View and Search View drawing.
- `trackers.py` — the ready-made trackers (CSRT, KCF, MOSSE, VitTrack, MixFormerV2) behind the same interface as `sot.py`.
- `config.py` — constants and shared parameter definitions.
- `sot.py` — `SingleObjectTracker` class (`__init__` ready, `init` and `update` are your implementation).

## ⌨️ Keyboard Shortcuts

- `S` — Select Target
- `Esc` — Cancel selection
- `Space` — Pause / Resume
- `F11` — Full Screen / Windowed
- `R` — Reset Defaults
- `Q` — Quit
