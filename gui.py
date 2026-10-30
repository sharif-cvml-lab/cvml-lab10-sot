from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QPoint, QRect, QSettings, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QKeySequence, QPainter, QPen, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from config import (
    ALGORITHM_STUDENT,
    APP_NAME,
    DEFAULT_ALGORITHM,
    DEFAULT_CAMERA_INDEX,
    DEFAULT_METHOD,
    DEFAULT_SCORE_THRESHOLD_PERCENT,
    DEFAULT_SEARCH_SCALE_TENTHS,
    DEFAULT_SETTINGS_MESSAGE,
    DEFAULT_SHOW_SEARCH_REGION,
    DEFAULT_SHOW_TEMPLATE,
    DEFAULT_THEME,
    DEFAULT_UPDATE_RATE_PERCENT,
    DEFAULT_UPDATE_TEMPLATE,
    DEMO_VIDEO_PATH,
    FILE_FILTER,
    MIN_ROI_SIZE,
    ORGANIZATION_NAME,
    STATE_IDLE,
    STATE_LOST,
    STATE_TRACKING,
    TEMPLATE_METHODS,
    TrackerParameters,
)
from trackers import list_algorithms
from video_thread import VideoThread


DARK_STYLE = """
QMainWindow, QWidget {
    background: #11151b;
    color: #e7ebf0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
QFrame#Header, QFrame#SidebarCard, QFrame#VideoCard, QFrame#StatusBar {
    background: #171c23;
    border: 1px solid #28303a;
    border-radius: 12px;
}
QFrame#VideoCanvas {
    background: #0a0d11;
    border: 1px solid #303945;
    border-radius: 10px;
}
QLabel#Title { font-size: 22px; font-weight: 700; }
QLabel#Subtitle, QLabel#Muted { color: #8e98a6; }
QLabel#PanelTitle { font-size: 14px; font-weight: 700; }
QLabel#Metric { color: #9aa6b4; font-size: 12px; }
QLabel#MetricValue { font-size: 15px; font-weight: 700; }
QLabel#ValueChip {
    background: #202833;
    border: 1px solid #364250;
    border-radius: 6px;
    padding: 2px 8px;
    min-width: 42px;
}
QPushButton {
    background: #212833;
    color: #eef2f6;
    border: 1px solid #35404d;
    border-radius: 8px;
    padding: 8px 12px;
}
QPushButton:hover { background: #2a3441; border-color: #4e6175; }
QPushButton:pressed { background: #18202a; }
QPushButton#accent { background: #3a7d67; border-color: #4c9b80; font-weight: 700; }
QPushButton#accent:hover { background: #479276; }
QPushButton#danger { background: #322126; border-color: #5d333d; }
QSpinBox {
    background: #1a2028;
    border: 1px solid #35404d;
    border-radius: 7px;
    padding: 6px;
}
QSlider::groove:horizontal { height: 5px; background: #2b333d; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #4d9d80; border-radius: 3px; }
QSlider::handle:horizontal {
    background: #80c6ab;
    border: 1px solid #9ad9c0;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QGroupBox {
    border: 1px solid #28303a;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 700;
}
QGroupBox::title { left: 12px; padding: 0 6px; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { width: 10px; background: transparent; }
QScrollBar::handle:vertical { background: #313b47; border-radius: 5px; min-height: 30px; }
QLabel#Error { color: #ff7b7b; font-weight: 700; }
QCheckBox { spacing: 8px; }
QListWidget, QComboBox {
    background: #1a2028;
    border: 1px solid #35404d;
    border-radius: 7px;
    padding: 4px;
}
"""

LIGHT_STYLE = """
QMainWindow, QWidget {
    background: #eef1f5;
    color: #1d252d;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
QFrame#Header, QFrame#SidebarCard, QFrame#VideoCard, QFrame#StatusBar {
    background: #ffffff;
    border: 1px solid #d3dae2;
    border-radius: 12px;
}
QFrame#VideoCanvas {
    background: #dfe5ec;
    border: 1px solid #c4ccd6;
    border-radius: 10px;
}
QLabel#Title { font-size: 22px; font-weight: 700; }
QLabel#Subtitle, QLabel#Muted { color: #5f6b78; }
QLabel#PanelTitle { font-size: 14px; font-weight: 700; }
QLabel#Metric { color: #5f6b78; font-size: 12px; }
QLabel#MetricValue { font-size: 15px; font-weight: 700; }
QLabel#Error { color: #c0392b; font-weight: 700; }
QLabel#ValueChip {
    background: #e8edf2;
    border: 1px solid #c4ccd6;
    border-radius: 6px;
    padding: 2px 8px;
    min-width: 42px;
}
QPushButton {
    background: #f7f9fb;
    color: #1d252d;
    border: 1px solid #c4ccd6;
    border-radius: 8px;
    padding: 8px 12px;
}
QPushButton:hover { background: #e8eef4; border-color: #8fa3b5; }
QPushButton:pressed { background: #dbe3ea; }
QPushButton#accent { background: #3a7d67; color: #ffffff; border-color: #4c9b80; font-weight: 700; }
QPushButton#accent:hover { background: #479276; }
QPushButton#danger { background: #f8e3e6; border-color: #e0b4bc; }
QSpinBox, QListWidget, QComboBox {
    background: #ffffff;
    border: 1px solid #c4ccd6;
    border-radius: 7px;
    padding: 6px;
}
QSlider::groove:horizontal { height: 5px; background: #cdd5de; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #4d9d80; border-radius: 3px; }
QSlider::handle:horizontal {
    background: #3a7d67;
    border: 1px solid #2c614f;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QGroupBox {
    border: 1px solid #d3dae2;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 700;
}
QGroupBox::title { left: 12px; padding: 0 6px; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { width: 10px; background: transparent; }
QScrollBar::handle:vertical { background: #bcc6d1; border-radius: 5px; min-height: 30px; }
"""


class VideoLabel(QLabel):
    """Scalable image view that preserves the source aspect ratio."""

    def __init__(self):
        super().__init__()
        self._pixmap = QPixmap()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(260, 190)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_frame(self, image: QImage) -> None:
        self._pixmap = QPixmap.fromImage(image)
        self._refresh_pixmap()

    def clear_frame(self) -> None:
        self._pixmap = QPixmap()
        self.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_pixmap()

    def _refresh_pixmap(self) -> None:
        if self._pixmap.isNull():
            return
        self.setPixmap(
            self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


class ValueSlider(QWidget):
    def __init__(self, title: str, minimum: int, maximum: int, value: int, parent=None):
        super().__init__(parent)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(minimum, maximum)
        self.slider.setValue(value)
        self.title_label = QLabel(title)
        self.title_label.setMinimumWidth(120)
        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("ValueChip")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value_label)
        self.slider.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, value: int) -> None:
        self.value_label.setText(str(value))

    def value(self) -> int:
        return self.slider.value()

    def set_value(self, value: int) -> None:
        self.slider.setValue(value)


def map_label_point_to_image(px: float, py: float, label_w: float, label_h: float, image_w: int, image_h: int):
    """Map a point inside the label to frame pixels.

    The frame is drawn centered and scaled with its aspect ratio kept (see VideoLabel), so the
    displayed size follows from the label size and the frame size alone. Points on the black
    bars around the frame are clamped to the nearest frame edge.
    """
    if label_w <= 0 or label_h <= 0 or image_w <= 0 or image_h <= 0:
        return None
    scale = min(label_w / image_w, label_h / image_h)
    offset_x = (label_w - image_w * scale) / 2
    offset_y = (label_h - image_h * scale) / 2
    x = (px - offset_x) / scale
    y = (py - offset_y) / scale
    x = min(max(x, 0), image_w - 1)
    y = min(max(y, 0), image_h - 1)
    return int(x), int(y)


class RoiLabel(VideoLabel):
    """Video view where the user can drag a rectangle (ROI) while selection mode is active."""

    roi_selected = pyqtSignal(int, int, int, int)

    def __init__(self):
        super().__init__()
        self.selecting = False
        self._start: QPoint | None = None
        self._current: QPoint | None = None

    def set_selecting(self, selecting: bool) -> None:
        self.selecting = selecting
        self._start = self._current = None
        self.setCursor(Qt.CursorShape.CrossCursor if selecting else Qt.CursorShape.ArrowCursor)
        self.update()

    def _to_image(self, point: QPoint):
        """Convert a label position to pixel coordinates of the displayed frame."""
        if self._pixmap.isNull():
            return None
        rect = self.contentsRect()
        return map_label_point_to_image(
            point.x() - rect.x(), point.y() - rect.y(), rect.width(), rect.height(),
            self._pixmap.width(), self._pixmap.height(),
        )

    def mousePressEvent(self, event) -> None:
        if self.selecting and event.button() == Qt.MouseButton.LeftButton:
            self._start = self._current = event.position().toPoint()
            self.update()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self.selecting and self._start is not None:
            self._current = event.position().toPoint()
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self.selecting and self._start is not None:
            start, end = self._to_image(self._start), self._to_image(event.position().toPoint())
            self._start = self._current = None
            self.update()
            if start is None or end is None:
                return
            x, y = min(start[0], end[0]), min(start[1], end[1])
            w, h = abs(end[0] - start[0]), abs(end[1] - start[1])
            if w >= MIN_ROI_SIZE and h >= MIN_ROI_SIZE:
                self.roi_selected.emit(x, y, w, h)
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.selecting and self._start is not None and self._current is not None:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 200, 0), 2, Qt.PenStyle.DashLine))
            painter.drawRect(QRect(self._start, self._current).normalized())
            painter.end()


class AppWindow(QMainWindow):
    """Main interactive UI for Lab 10."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(QSize(1120, 740))
        self.resize(1400, 900)

        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        self.video_thread: VideoThread | None = None
        has_demo = DEMO_VIDEO_PATH.is_file()
        self.selected_file = str(DEMO_VIDEO_PATH) if has_demo else ""
        self.source_type = "file" if has_demo else "camera"   # start with assets/demo.mp4 if it exists, else the webcam
        self.algorithm = DEFAULT_ALGORITHM
        self.theme = DEFAULT_THEME
        self._closing = False
        self._restoring = False

        self._build_ui()
        self._restore_settings()
        self._build_shortcuts()
        self._apply_theme()
        self._start_video_thread()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 12)
        root.setSpacing(12)

        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)
        title_box = QVBoxLayout()
        title = QLabel("Single Object Tracking Playground")
        title.setObjectName("Title")
        subtitle = QLabel("Select a target and follow it with template matching")
        subtitle.setObjectName("Subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box, 1)
        self.theme_button = QPushButton("Light Mode")
        self.theme_button.clicked.connect(self._toggle_theme)
        header_layout.addWidget(self.theme_button)
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("danger")
        self.reset_button.clicked.connect(self._reset_defaults)
        header_layout.addWidget(self.reset_button)
        root.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        video_side = QWidget()
        video_layout = QVBoxLayout(video_side)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_grid = QGridLayout()
        video_grid.setSpacing(10)
        self.tracking_panel = self._create_video_card("Original / Tracking View", RoiLabel())
        self.search_panel = self._create_video_card("Search View", VideoLabel())
        self.tracking_panel.image.roi_selected.connect(self._roi_selected)
        video_grid.addWidget(self.tracking_panel, 0, 0)
        video_grid.addWidget(self.search_panel, 0, 1)
        video_grid.setColumnStretch(0, 3)
        video_grid.setColumnStretch(1, 2)
        video_layout.addLayout(video_grid, 1)

        status = QFrame()
        status.setObjectName("StatusBar")
        status_layout = QHBoxLayout(status)
        status_layout.setContentsMargins(14, 8, 14, 8)
        self.status_label = QLabel("Starting source...")
        self.status_label.setObjectName("Muted")
        self.error_label = QLabel("")
        self.error_label.setObjectName("Error")
        self.settings_label = QLabel(DEFAULT_SETTINGS_MESSAGE)
        self.settings_label.setObjectName("MetricValue")
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setObjectName("MetricValue")
        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.error_label)
        status_layout.addSpacing(18)
        status_layout.addWidget(self.settings_label)
        status_layout.addSpacing(18)
        status_layout.addWidget(self.fps_label)
        video_layout.addWidget(status)

        splitter.addWidget(video_side)
        splitter.addWidget(self._build_sidebar())
        splitter.setSizes([1020, 380])
        root.addWidget(splitter, 1)
        self.setCentralWidget(central)

    def _create_video_card(self, title: str, image: VideoLabel) -> QFrame:
        card = QFrame()
        card.setObjectName("VideoCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName("PanelTitle")
        layout.addWidget(title_label)
        canvas = QFrame()
        canvas.setObjectName("VideoCanvas")
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        image.setText("Waiting for source...")
        canvas_layout.addWidget(image)
        layout.addWidget(canvas, 1)
        card.image = image
        return card

    def _build_sidebar(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(10)

        source_box = QGroupBox("Input Source")
        source_layout = QVBoxLayout(source_box)
        camera_row = QHBoxLayout()
        camera_row.addWidget(QLabel("Camera index"))
        self.camera_spin = QSpinBox()
        self.camera_spin.setRange(0, 9)
        self.camera_spin.valueChanged.connect(self._camera_index_changed)
        camera_row.addWidget(self.camera_spin)
        source_layout.addLayout(camera_row)

        source_buttons = QHBoxLayout()
        self.webcam_button = QPushButton("Webcam")
        self.webcam_button.clicked.connect(self._use_webcam)
        self.demo_button = QPushButton("Demo")
        self.demo_button.clicked.connect(self._use_demo)
        self.demo_button.setVisible(DEMO_VIDEO_PATH.is_file())  # only if a demo video is shipped
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self._browse_file)
        self.upload_button = QPushButton("Upload")
        self.upload_button.setObjectName("accent")
        self.upload_button.setEnabled(False)
        self.upload_button.clicked.connect(self._upload_selected_file)
        for button in (self.webcam_button, self.demo_button, self.browse_button, self.upload_button):
            source_buttons.addWidget(button)
        source_layout.addLayout(source_buttons)

        self.file_label = QLabel("Source: demo video" if DEMO_VIDEO_PATH.is_file() else "Source: webcam")
        self.file_label.setObjectName("Muted")
        self.file_label.setWordWrap(True)
        source_layout.addWidget(self.file_label)

        action_row = QHBoxLayout()
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self._toggle_pause)
        self.restart_button = QPushButton("Restart")
        self.restart_button.clicked.connect(self._restart_source)
        action_row.addWidget(self.pause_button)
        action_row.addWidget(self.restart_button)
        source_layout.addLayout(action_row)
        layout.addWidget(source_box)

        target_box = QGroupBox("Target")
        target_layout = QVBoxLayout(target_box)
        target_row = QHBoxLayout()
        self.select_button = QPushButton("Select Target (S)")
        self.select_button.setObjectName("accent")
        self.select_button.clicked.connect(self._begin_selection)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_target)
        target_row.addWidget(self.select_button, 1)
        target_row.addWidget(self.clear_button)
        target_layout.addLayout(target_row)
        hint = QLabel("Click Select Target, then drag a rectangle around the object on the frame.")
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        target_layout.addWidget(hint)
        layout.addWidget(target_box)

        algorithm_box = QGroupBox("Tracking Algorithm")
        algorithm_layout = QVBoxLayout(algorithm_box)
        self.algorithm_combo = QComboBox()
        self._algorithms = list_algorithms()
        unavailable_notes = []
        for index, info in enumerate(self._algorithms):
            self.algorithm_combo.addItem(info.label if info.available else f"{info.label} (unavailable)", info.key)
            self.algorithm_combo.setItemData(index, info.description if info.available else info.reason,
                                             Qt.ItemDataRole.ToolTipRole)
            if not info.available:
                self.algorithm_combo.model().item(index).setEnabled(False)
                unavailable_notes.append(f"{info.short_name}: {info.reason}")
        algorithm_layout.addWidget(self.algorithm_combo)
        self.algorithm_hint = QLabel("")
        self.algorithm_hint.setObjectName("Muted")
        self.algorithm_hint.setWordWrap(True)
        algorithm_layout.addWidget(self.algorithm_hint)
        self._unavailable_notes = unavailable_notes
        layout.addWidget(algorithm_box)

        lost_box = QGroupBox("Lost Detection")
        self.lost_box = lost_box
        lost_layout = QVBoxLayout(lost_box)
        self.threshold_slider = ValueSlider("Score threshold ×100", 10, 95, DEFAULT_SCORE_THRESHOLD_PERCENT)
        lost_layout.addWidget(self.threshold_slider)
        lost_note = QLabel("The target is lost when the tracking score falls below this value. "
                           "Applies to the Student and MixFormerV2 algorithms; the others use their own built-in decision.")
        lost_note.setObjectName("Muted")
        lost_note.setWordWrap(True)
        lost_layout.addWidget(lost_note)
        layout.addWidget(lost_box)

        tracker_box = QGroupBox("Student Algorithm Settings (sot.py)")
        self.student_box = tracker_box
        tracker_layout = QVBoxLayout(tracker_box)
        self.search_slider = ValueSlider("Search region ×10", 15, 80, DEFAULT_SEARCH_SCALE_TENTHS)
        self.rate_slider = ValueSlider("Update rate ×100", 1, 100, DEFAULT_UPDATE_RATE_PERCENT)
        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Method"))
        self.method_combo = QComboBox()
        for name in TEMPLATE_METHODS:
            self.method_combo.addItem(name)
        method_row.addWidget(self.method_combo, 1)
        tracker_layout.addLayout(method_row)
        tracker_layout.addWidget(self.search_slider)
        self.update_check = QCheckBox("Adaptive template (update template)")
        tracker_layout.addWidget(self.update_check)
        tracker_layout.addWidget(self.rate_slider)
        self.search_check = QCheckBox("Show search region")
        self.template_check = QCheckBox("Show template")
        tracker_layout.addWidget(self.search_check)
        tracker_layout.addWidget(self.template_check)
        layout.addWidget(tracker_box)

        info_box = QGroupBox("Tracking Information")
        info_layout = QGridLayout(info_box)
        self.metric_values: dict[str, QLabel] = {}
        for row, name in enumerate(("Algorithm", "State", "Tracking score", "Position (x, y)", "Size (w × h)", "Displacement", "FPS")):
            label = QLabel(name)
            label.setObjectName("Metric")
            value = QLabel("--")
            value.setObjectName("MetricValue")
            value.setWordWrap(True)
            info_layout.addWidget(label, row, 0)
            info_layout.addWidget(value, row, 1)
            self.metric_values[name] = value
        layout.addWidget(info_box)
        layout.addStretch(1)

        for control in (self.search_slider, self.threshold_slider, self.rate_slider):
            control.slider.valueChanged.connect(self._parameters_changed)
        for check in (self.update_check, self.search_check, self.template_check):
            check.toggled.connect(self._parameters_changed)
        self.method_combo.currentIndexChanged.connect(self._parameters_changed)
        self.algorithm_combo.currentIndexChanged.connect(self._algorithm_changed)
        self._update_algorithm_ui()

        scroll.setWidget(content)
        return scroll

    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence("Space"), self, activated=self._toggle_pause)
        QShortcut(QKeySequence("F11"), self, activated=self._toggle_fullscreen)
        QShortcut(QKeySequence("R"), self, activated=self._reset_defaults)
        QShortcut(QKeySequence("S"), self, activated=self._begin_selection)
        QShortcut(QKeySequence("Escape"), self, activated=self._cancel_selection)
        QShortcut(QKeySequence("Q"), self, activated=self.close)

    def _current_parameters(self) -> TrackerParameters:
        return TrackerParameters(
            search_scale=self.search_slider.value() / 10.0,
            method=TEMPLATE_METHODS[self.method_combo.currentText()],
            score_threshold=self.threshold_slider.value() / 100.0,
            update_template=self.update_check.isChecked(),
            update_rate=self.rate_slider.value() / 100.0,
            show_search_region=self.search_check.isChecked(),
            show_template=self.template_check.isChecked(),
        )

    def _start_video_thread(self) -> None:
        self._stop_video_thread()
        self.tracking_panel.image.set_selecting(False)
        self.video_thread = VideoThread(
            camera_index=self.camera_spin.value(),
            source_type=self.source_type,
            file_path=self.selected_file,
            algorithm=self.algorithm,
            parent=self,
        )
        self.video_thread.set_parameters(self._current_parameters())
        self.video_thread.frame_ready.connect(self._update_frames)
        self.video_thread.status_changed.connect(self.status_label.setText)
        self.video_thread.processing_error.connect(self._show_error)
        self.video_thread.algorithm_failed.connect(self._on_algorithm_failed)
        self.video_thread.start()
        self.pause_button.setText("Pause")
        self.status_label.setText("Starting source...")

    def _stop_video_thread(self) -> None:
        if self.video_thread is not None:
            self.video_thread.stop()
            self.video_thread.deleteLater()
            self.video_thread = None

    def _update_frames(self, qt_tracking, qt_search, info: dict, fps: float) -> None:
        self.tracking_panel.image.set_frame(qt_tracking)
        self.search_panel.image.set_frame(qt_search)
        state = info["state"]
        self.metric_values["Algorithm"].setText(info["algorithm_name"])
        self.metric_values["State"].setText("Target Lost (tracking stopped)" if info.get("stopped") else state)
        box = info["box"]
        if state == STATE_IDLE or box is None:
            for name in ("Tracking score", "Position (x, y)", "Size (w × h)", "Displacement"):
                self.metric_values[name].setText("--")
        else:
            score = info["score"]
            if score is None:  # never show an invented value
                score_text = f"Not provided by {info['algorithm_name']}"
            elif info["algorithm"] == ALGORITHM_STUDENT:
                score_text = f"{score:.3f}"
            else:
                score_text = f"{score:.3f} ({info['algorithm_name']}-specific, not comparable)"
            self.metric_values["Tracking score"].setText(score_text)
            self.metric_values["Tracking score"].setToolTip(info["score_note"])
            self.metric_values["Position (x, y)"].setText(f"({box[0]}, {box[1]})")
            self.metric_values["Size (w × h)"].setText(f"{box[2]} × {box[3]}")
            dx, dy = info["displacement"]
            self.metric_values["Displacement"].setText(f"({dx:+d}, {dy:+d}) px")
        self.metric_values["FPS"].setText(f"{fps:.1f}")
        self.fps_label.setText(f"FPS: {fps:.1f}")

    # ---- algorithm selection
    def _update_algorithm_ui(self) -> None:
        student = self.algorithm == ALGORITHM_STUDENT
        self.student_box.setEnabled(student)
        self.lost_box.setEnabled(self.algorithm in (ALGORITHM_STUDENT, "mixformerv2"))
        notes = []
        if not student:
            notes.append("Search region, matching map and the settings below belong to the Student algorithm only.")
        notes += [f"Unavailable - {note}" for note in self._unavailable_notes]
        self.algorithm_hint.setText("\n".join(notes))
        self.algorithm_hint.setVisible(bool(notes))

    def _algorithm_changed(self, index: int) -> None:
        key = self.algorithm_combo.itemData(index)
        if key is None or key == self.algorithm:
            return
        self.algorithm = key
        self._update_algorithm_ui()
        self._save_settings()
        if self.video_thread is not None:
            self.video_thread.set_algorithm(key)

    def _on_algorithm_failed(self, key: str, message: str, active: str) -> None:
        """An algorithm could not start (for example a broken VitTrack model); `active` stays in use."""
        message = " ".join(message.split())[:220]
        index = self.algorithm_combo.findData(key)
        if index >= 0:
            self.algorithm_combo.model().item(index).setEnabled(False)
            self.algorithm_combo.setItemData(index, message, Qt.ItemDataRole.ToolTipRole)
        self._unavailable_notes.append(f"{key}: {message}")
        self.algorithm = active
        self.algorithm_combo.blockSignals(True)
        self.algorithm_combo.setCurrentIndex(max(0, self.algorithm_combo.findData(active)))
        self.algorithm_combo.blockSignals(False)
        self._update_algorithm_ui()
        self._save_settings()
        self.error_label.setText(f"{key} could not start: {message}")

    def _show_error(self, message: str) -> None:
        self.error_label.setText(f"Tracker error: {message}" if message else "")

    def _parameters_changed(self, *_args) -> None:
        if self._restoring:
            return
        self._save_settings()
        if self.video_thread is not None:
            self.video_thread.set_parameters(self._current_parameters())

    # ---- target selection
    def _begin_selection(self) -> None:
        if self.video_thread is None:
            return
        self.video_thread.begin_selection()
        self.tracking_panel.image.set_selecting(True)
        self.status_label.setText("Draw a rectangle around the target")

    def _cancel_selection(self) -> None:
        if self.video_thread is not None:
            self.video_thread.cancel_selection()
        self.tracking_panel.image.set_selecting(False)

    def _roi_selected(self, x: int, y: int, w: int, h: int) -> None:
        self.tracking_panel.image.set_selecting(False)
        if self.video_thread is not None:
            self.video_thread.set_roi((x, y, w, h))

    def _clear_target(self) -> None:
        self._cancel_selection()
        if self.video_thread is not None:
            self.video_thread.clear_target()
            self.status_label.setText("Target cleared. Select a new target.")

    # ---- source handling
    def _use_webcam(self) -> None:
        self.source_type = "camera"
        self.file_label.setText("Source: webcam")
        self._start_video_thread()

    def _use_demo(self) -> None:
        self.source_type = "file"
        self.selected_file = str(DEMO_VIDEO_PATH)
        self.file_label.setText("Source: demo video")
        self._start_video_thread()

    def _camera_index_changed(self, _value: int) -> None:
        self._save_settings()
        if self.source_type == "camera" and not self._closing and self.video_thread is not None:
            self._start_video_thread()

    def _browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image or Video", "", FILE_FILTER)
        if not file_path:
            return
        self.pending_file = file_path
        self.file_label.setText(f"Selected: {Path(file_path).name}")
        self.upload_button.setEnabled(True)
        self.status_label.setText("File selected. Click Upload to process it.")

    def _upload_selected_file(self) -> None:
        file_path = getattr(self, "pending_file", "")
        if not file_path:
            self.status_label.setText("No file selected. Click Browse first.")
            return
        self.selected_file = file_path
        self.source_type = "file"
        self._start_video_thread()

    def _toggle_pause(self) -> None:
        if self.video_thread is None:
            return
        paused = self.pause_button.text() == "Pause"
        self.video_thread.set_paused(paused)
        self.pause_button.setText("Resume" if paused else "Pause")

    def _restart_source(self) -> None:
        if self.video_thread is not None:
            self._cancel_selection()
            self.video_thread.restart_source()
            self.pause_button.setText("Pause")
            self.video_thread.set_paused(False)
            self.status_label.setText("Restarting source...")
        else:
            self._start_video_thread()

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _toggle_theme(self) -> None:
        self.theme = "light" if self.theme == "dark" else "dark"
        self._apply_theme()
        self._save_settings()

    def _apply_theme(self) -> None:
        self.setStyleSheet(DARK_STYLE if self.theme == "dark" else LIGHT_STYLE)
        self.theme_button.setText("Light Mode" if self.theme == "dark" else "Dark Mode")

    def _reset_defaults(self) -> None:
        self._restoring = True
        self.camera_spin.blockSignals(True)
        self.camera_spin.setValue(DEFAULT_CAMERA_INDEX)
        self.camera_spin.blockSignals(False)
        self.method_combo.setCurrentText(DEFAULT_METHOD)
        self.algorithm_combo.blockSignals(True)
        self.algorithm_combo.setCurrentIndex(max(0, self.algorithm_combo.findData(DEFAULT_ALGORITHM)))
        self.algorithm_combo.blockSignals(False)
        if self.algorithm != DEFAULT_ALGORITHM:
            self.algorithm = DEFAULT_ALGORITHM
            if self.video_thread is not None:
                self.video_thread.set_algorithm(DEFAULT_ALGORITHM)
            self._update_algorithm_ui()
        self.search_slider.set_value(DEFAULT_SEARCH_SCALE_TENTHS)
        self.threshold_slider.set_value(DEFAULT_SCORE_THRESHOLD_PERCENT)
        self.rate_slider.set_value(DEFAULT_UPDATE_RATE_PERCENT)
        self.update_check.setChecked(DEFAULT_UPDATE_TEMPLATE)
        self.search_check.setChecked(DEFAULT_SHOW_SEARCH_REGION)
        self.template_check.setChecked(DEFAULT_SHOW_TEMPLATE)
        self._restoring = False
        self._parameters_changed()
        self.status_label.setText("Parameters reset to defaults.")

    # ---- persistence
    def _save_settings(self) -> None:
        if not hasattr(self, "template_check"):
            return
        s = self.settings
        s.setValue("camera_index", self.camera_spin.value())
        s.setValue("theme", self.theme)
        s.setValue("method", self.method_combo.currentText())
        s.setValue("algorithm", self.algorithm)
        s.setValue("search_scale_tenths", self.search_slider.value())
        s.setValue("score_threshold_percent", self.threshold_slider.value())
        s.setValue("update_rate_percent", self.rate_slider.value())
        s.setValue("update_template", self.update_check.isChecked())
        s.setValue("show_search_region", self.search_check.isChecked())
        s.setValue("show_template", self.template_check.isChecked())
        s.sync()
        self.settings_label.setText("Settings: Saved")

    def _restore_settings(self) -> None:
        self._restoring = True
        s = self.settings
        self.camera_spin.blockSignals(True)
        self.camera_spin.setValue(s.value("camera_index", DEFAULT_CAMERA_INDEX, int))
        self.camera_spin.blockSignals(False)
        self.theme = str(s.value("theme", DEFAULT_THEME))
        method = str(s.value("method", DEFAULT_METHOD))
        self.method_combo.setCurrentText(method if method in TEMPLATE_METHODS else DEFAULT_METHOD)
        saved = str(s.value("algorithm", DEFAULT_ALGORITHM))
        info = next((a for a in self._algorithms if a.key == saved), None)
        self.algorithm = saved if info is not None and info.available else DEFAULT_ALGORITHM
        self.algorithm_combo.blockSignals(True)
        self.algorithm_combo.setCurrentIndex(max(0, self.algorithm_combo.findData(self.algorithm)))
        self.algorithm_combo.blockSignals(False)
        self._update_algorithm_ui()
        self.search_slider.set_value(int(s.value("search_scale_tenths", DEFAULT_SEARCH_SCALE_TENTHS)))
        self.threshold_slider.set_value(int(s.value("score_threshold_percent", DEFAULT_SCORE_THRESHOLD_PERCENT)))
        self.rate_slider.set_value(int(s.value("update_rate_percent", DEFAULT_UPDATE_RATE_PERCENT)))
        self.update_check.setChecked(s.value("update_template", DEFAULT_UPDATE_TEMPLATE, bool))
        self.search_check.setChecked(s.value("show_search_region", DEFAULT_SHOW_SEARCH_REGION, bool))
        self.template_check.setChecked(s.value("show_template", DEFAULT_SHOW_TEMPLATE, bool))
        self._restoring = False
        self.settings_label.setText("Settings: Restored")

    def closeEvent(self, event) -> None:
        if not self._closing:
            self._closing = True
            self._save_settings()
            self._stop_video_thread()
        event.accept()


def create_application() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APP_NAME)
    return app
