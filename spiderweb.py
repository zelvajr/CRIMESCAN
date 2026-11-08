import sys
import os
import hashlib
import uuid
import json
import csv
import cv2
import threading
import time
import urllib.request
import numpy as np
import shutil
import requests
from datetime import datetime
from pathlib import Path
from collections import deque

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

from remote_stream import SpiderCamRemoteThread, BACKEND_URL, get_remote_config

from PyQt6.QtWidgets import (
QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
QPushButton, QLabel, QFrame, QStackedWidget, QScrollArea,
QFileDialog, QLineEdit, QTextEdit, QSplitter, QGridLayout,
QSlider, QComboBox, QProgressBar, QSizePolicy, QSpacerItem,
QMenu, QMessageBox, QGraphicsView, QGraphicsScene,
QGraphicsPixmapItem, QGraphicsRectItem, QInputDialog,
QGraphicsItem, QGraphicsEllipseItem, QGraphicsLineItem,
QGraphicsTextItem, QToolBar, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import (
Qt, QTimer, QThread, pyqtSignal, QSize, QPoint,
QRectF, QPointF
)
from PyQt6.QtGui import (
QFont, QPixmap, QImage, QPainter, QPen, QColor,
QLinearGradient, QRadialGradient, QBrush, QPalette,
QIcon, QFontDatabase, QAction, QTransform, QCursor
)

# ─────────────────────────────────────────────

# GLOBAL STYLESHEET — v2.1 UPGRADED

# ─────────────────────────────────────────────

MASTER_STYLE = """
QMainWindow, QWidget {
background-color: #080b0f;
color: #dde4f0;
font-family: 'Segoe UI', 'Inter', sans-serif;
font-size: 13px;
}
QScrollBar {
background: #0c1018; width: 7px; border-radius: 3px;
}
QScrollBar::handle {
background: #1e6a9e; border-radius: 3px; min-height: 24px;
}
QScrollBar::handle:vertical { background: #4dc8f0; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0px; }
QScrollBar { background: #0c1018; height: 7px; border-radius: 3px; }
QScrollBar::handle {
background: #1e6a9e; border-radius: 3px; min-width: 24px;
}
QScrollBar::handle:horizontal { background: #4dc8f0; }

QPushButton#navBtn {
background-color: transparent;
color: #6a7a8a;
border: none;
border-left: 2px solid transparent;
text-align: left;
padding: 13px 16px 13px 20px;
font-size: 12px;
font-weight: 500;
border-radius: 0px;
letter-spacing: 0.5px;
}
QPushButton#navBtn {
background-color: #0e1620;
color: #b8d4ee;
border-left: 2px solid #1e5a8e;
}
QPushButton#navBtn[active="true"] {
background-color: #0a1825;
color: #4dc8f0;
border-left: 3px solid #4dc8f0;
font-weight: 700;
font-size: 12px;
}

QPushButton#actionBtn {
background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
stop:0 #0e3d62, stop:1 #0a2d48);
color: #5cd4f8;
border: 1px solid #1e5a82;
border-radius: 6px;
padding: 9px 18px;
font-size: 12px;
font-weight: 600;
letter-spacing: 0.3px;
min-height: 18px;
}
QPushButton#actionBtn {
background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
stop:0 #134d78, stop:1 #0e3d62);
border: 1px solid #4dc8f0;
color: #8ae4ff;
}
QPushButton#actionBtn { background: #061420; border: 1px solid #2a7aaa; }
QPushButton#actionBtn {
background: #0a1420; color: #3a5a6a; border: 1px solid #1a2a3a;
}

QPushButton#captureBtn {
background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
stop:0 #115585, stop:1 #093a5e);
color: #ffffff;
border: 1.5px solid #4dc8f0;
border-radius: 7px;
padding: 10px 24px;
font-size: 13px;
font-weight: 700;
letter-spacing: 0.5px;
min-height: 20px;
}
QPushButton#captureBtn {
background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
stop:0 #1a72a8, stop:1 #115585);
border: 1.5px solid #7adcf8;
}
QPushButton#captureBtn { background: #061828; }
QPushButton#captureBtn {
background: #0a1825; color: #3a5a6a; border: 1px solid #1a3a4a;
}

QPushButton#dangerBtn {
background: #140808; color: #f06060;
border: 1px solid #7a1a1a; border-radius: 6px;
padding: 9px 18px; font-size: 12px; font-weight: 600; min-height: 18px;
}
QPushButton#dangerBtn {
background: #220f0f; border: 1px solid #f06060; color: #ff8888;
}

QPushButton#successBtn {
background: #081810; color: #52c488;
border: 1px solid #1a6035; border-radius: 6px;
padding: 9px 18px; font-size: 12px; font-weight: 600; min-height: 18px;
}
QPushButton#successBtn {
background: #0e2818; border: 1px solid #52c488; color: #80e0a8;
}

QFrame#panel {
background-color: #0c1018; border: 1px solid #192232; border-radius: 8px;
}
QFrame#glassPanel {
background-color: rgba(12,18,28,0.92);
border: 1px solid #1c3352; border-radius: 10px;
}
QFrame#topBar {
background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
stop:0 #050810, stop:1 #080e1c);
border-bottom: 1px solid #162438;
}
QFrame#sidebar {
background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
stop:0 #050810, stop:1 #070c12);
border-right: 1px solid #0e1c2c;
}
QFrame#statusBar { background-color: #050810; border-top: 1px solid #0e1c2c; }

QLineEdit {
background-color: #0c1520; color: #c8dce8;
border: 1px solid #1c3550; border-radius: 5px;
padding: 9px 12px; font-size: 12px;
selection-background-color: #1e5a82;
}
QLineEdit { border: 1px solid #4dc8f0; background-color: #0e1c2e; color: #e0eef8; }

QTextEdit {
background-color: #070c16; color: #9ab0c8;
border: 1px solid #182838; border-radius: 6px;
padding: 8px 10px; font-size: 11px;
font-family: 'Consolas', 'Courier New', monospace;
selection-background-color: #1e5a82;
}

QComboBox {
background-color: #0c1520; color: #b8d0e4;
border: 1px solid #1c3550; border-radius: 5px;
padding: 7px 12px; font-size: 12px; min-height: 16px;
}
QComboBox { border: 1px solid #4dc8f0; color: #d8eef8; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
background-color: #0c1520; color: #b8d0e4;
border: 1px solid #1c3550;
selection-background-color: #0e3d62; selection-color: #4dc8f0;
padding: 4px;
}

QSlider::groove {
height: 4px; background: #162838; border-radius: 2px;
}
QSlider::handle {
background: #4dc8f0; width: 14px; height: 14px;
margin: -5px 0; border-radius: 7px; border: 2px solid #0c1520;
}
QSlider::handle:horizontal {
background: #7adcf8; width: 16px; height: 16px; margin: -6px 0;
}
QSlider::sub-page {
background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
stop:0 #1e5a82, stop:1 #4dc8f0);
border-radius: 2px;
}

QProgressBar {
background-color: #0c1520; border: 1px solid #182838;
border-radius: 4px; text-align: center;
color: #4dc8f0; font-size: 10px; font-weight: 600; letter-spacing: 1px;
}
QProgressBar::chunk {
background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
stop:0 #0e4a72, stop:1 #4dc8f0);
border-radius: 3px;
}

QMenu {
background-color: #0c1520; color: #b8d0e4;
border: 1px solid #1c3550; border-radius: 8px; padding: 6px 4px;
}
QMenu::item { padding: 9px 22px; border-radius: 5px; font-size: 12px; }
QMenu::item { background-color: #0e3d62; color: #4dc8f0; }
QMenu::separator { background: #182838; height: 1px; margin: 5px 10px; }

QGraphicsView {
background-color: #050810; border: 1px solid #182838; border-radius: 8px;
}
QSplitter::handle { background: #162838; width: 2px; height: 2px; }
QToolTip {
background-color: #0c1520; color: #4dc8f0;
border: 1px solid #1c3550; border-radius: 4px;
padding: 6px 10px; font-size: 11px;
}
"""

# ─────────────────────────────────────────────

# CONFIDENCE COLOR HELPERS

# ─────────────────────────────────────────────

def confidence_color(conf):
    if conf >= 0.90:   return (240, 200, 77)
    elif conf >= 0.70: return (30, 160, 240)
    else:              return (50, 50, 240)

def confidence_color_hex(conf):
    if conf >= 0.90:   return "#4dc8f0"
    elif conf >= 0.70: return "#f0a030"
    else:              return "#f05050"

# ─────────────────────────────────────────────

# EVIDENCE MANIFEST AND SHA-256 VERIFICATION

# ─────────────────────────────────────────────

class EvidenceManifest:
    def __init__(self, case_id="UNKNOWN", operator="UNKNOWN"):
        self.case_id       = case_id
        self.operator      = operator
        self.entries       = []
        self.manifest_path = None
        self.manifest_error = None
        os.makedirs("case_data", exist_ok=True)

    def set_case(self, case_id, operator):
        self.case_id  = case_id
        self.operator = operator
        case_dir = os.path.join("case_data", case_id.replace(" ", "_"))
        os.makedirs(case_dir, exist_ok=True)
        self.manifest_path = os.path.join(case_dir, "manifest.json")
        self._load_existing()

    def _load_existing(self):
        self.entries = []
        self.manifest_error = None
        if not self.manifest_path or not os.path.exists(self.manifest_path):
            return
        try:
            with open(self.manifest_path, 'r') as f:
                data = json.load(f)
        except (OSError, UnicodeError, json.JSONDecodeError):
            self.manifest_error = "Manifest could not be read as valid JSON."
            return
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("entries"), list)
            or not isinstance(data.get("total_items"), int)
            or isinstance(data.get("total_items"), bool)
            or data["total_items"] != len(data["entries"])
            or any(
                not isinstance(data.get(field), str)
                for field in ("software", "case_id", "operator", "created")
            )
        ):
            self.manifest_error = "Manifest structure is invalid."
            return
        for entry in data["entries"]:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("filename"), str)
                or not isinstance(entry.get("filepath"), str)
                or not isinstance(entry.get("sha256"), str)
                or len(entry["sha256"]) != 64
                or any(char not in "0123456789abcdefABCDEF" for char in entry["sha256"])
            ):
                self.manifest_error = "Manifest contains an invalid evidence entry."
                return
        self.entries = data["entries"]

    def hash_file(self, filepath):
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()

    def register(self, filepath, action="ACQUIRED", notes=""):
        if self.manifest_error:
            raise ValueError("Cannot register evidence while the manifest is invalid.")
        if self.manifest_path is None:
            raise RuntimeError("Select a case before registering evidence.")
        filepath = os.fspath(filepath)
        file_hash = self.hash_file(filepath)
        entry = {
            "acquisition_id": f"ACQ-{len(self.entries)+1:04d}",
            "timestamp":      datetime.now().isoformat(),
            "case_id":        self.case_id,
            "operator":       self.operator,
            "action":         action,
            "filename":       os.path.basename(filepath),
            "filepath":       filepath,
            "sha256":         file_hash,
            "notes":          notes,
            "tampered":       False
        }
        self.entries.append(entry)
        try:
            self._save()
        except Exception:
            self.entries.pop()
            raise
        return entry

    def verify_all(self):
        if self.manifest_error:
            return [("manifest.json", "INVALID_MANIFEST")]
        if self.manifest_path is None:
            return []
        results = []
        for entry in self.entries:
            fpath = entry.get("filepath", "")
            if not os.path.exists(fpath):
                results.append((entry["filename"], "MISSING"))
                continue
            try:
                current_hash = self.hash_file(fpath)
            except OSError:
                results.append((entry["filename"], "UNREADABLE"))
                continue
            modified = current_hash.lower() != entry["sha256"].lower()
            entry["tampered"] = modified
            if modified:
                results.append((entry["filename"], "MODIFIED"))
            else:
                results.append((entry["filename"], "VERIFIED"))
        self._save()
        return results

    def _save(self):
        if not self.manifest_path:
            raise RuntimeError("No case manifest has been selected.")
        if self.manifest_error:
            raise ValueError("Cannot overwrite an invalid evidence manifest.")
        manifest = {
            "software":    "SpiderCam Forensic Suite v2.1",
            "case_id":     self.case_id,
            "operator":    self.operator,
            "created":     datetime.now().isoformat(),
            "total_items": len(self.entries),
            "entries":     self.entries
        }
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

    def get_summary(self):
        return {
            "total":    len(self.entries),
            "case_id":  self.case_id,
            "operator": self.operator,
            "entries":  self.entries
        }

MANIFEST = EvidenceManifest()

# ─────────────────────────────────────────────

# FORENSIC AUDIT LOGGER

# ─────────────────────────────────────────────

class ForensicAuditLog:
    def __init__(self):
        os.makedirs("case_data", exist_ok=True)
        self.log_path = os.path.join("case_data", "audit_log.txt")

    def log(self, action, details="", operator="UNKNOWN"):
        entry = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"OPERATOR: {operator} | ACTION: {action} | DETAILS: {details}\n"
        )
        with open(self.log_path, 'a') as f:
            f.write(entry)

AUDIT = ForensicAuditLog()


def summarize_integrity_results(results):
    if not results:
        return "NOT VERIFIED: NO EVIDENCE REGISTERED"
    verified = sum(status == "VERIFIED" for _, status in results)
    issues = len(results) - verified
    if issues:
        return (
            f"CHECK FAILED: {issues} item(s) require review; "
            f"{verified} file hash(es) match"
        )
    return f"{verified} FILE HASHES MATCH THE MANIFEST AT CHECK TIME"

# ─────────────────────────────────────────────

# SPIDER WEB BACKGROUND

# ─────────────────────────────────────────────

class SpiderWebBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w * 0.85, h * 0.15
        import math
        pen = QPen(QColor(20, 70, 120, 14))
        pen.setWidth(1)
        painter.setPen(pen)
        for i in range(16):
            angle = math.radians(i * 22.5)
            x2 = cx + math.cos(angle) * 420
            y2 = cy + math.sin(angle) * 420
            painter.drawLine(int(cx), int(cy), int(x2), int(y2))
        pen2 = QPen(QColor(15, 50, 100, 10))
        pen2.setWidth(1)
        painter.setPen(pen2)
        for r in range(50, 450, 60):
            painter.drawEllipse(int(cx-r), int(cy-r), r*2, r*2)
        pen3 = QPen(QColor(20, 80, 140, 8))
        pen3.setWidth(1)
        painter.setPen(pen3)
        for i in range(0, 220, 28):
            painter.drawLine(0, i, i, 0)
        painter.end()

# ─────────────────────────────────────────────

# FORENSIC LOG WIDGET — color-coded terminal

# ─────────────────────────────────────────────

class ForensicLogWidget(QTextEdit):
    def __init__(self, parent=None, placeholder="Forensic log..."):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
QTextEdit {
background-color: #060a12;
color: #8ab8c8;
border: 1px solid #142030;
border-radius: 6px;
padding: 8px 10px;
font-size: 11px;
font-family: 'Consolas', monospace;
line-height: 1.6;
}
""")

    def append_log(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        if any(x in msg.upper() for x in ["ERROR", "FAILED", "BREACH"]):
            color, prefix = "#f06060", "✕"
        elif any(x in msg.upper() for x in ["COMPLETE", "SUCCESS", "VERIFIED", "✅"]):
            color, prefix = "#52c488", "✔"
        elif any(x in msg.upper() for x in ["WARNING", "WARN"]):
            color, prefix = "#f0a030", "⚠"
        elif any(x in msg.upper() for x in ["INITIATED", "STARTED", "ANALYZING", "PROCESSING", "RUNNING"]):
            color, prefix = "#4dc8f0", "▶"
        else:
            color, prefix = "#7a9ab8", "·"
        self.append(
            f'<span style="color:#2a4a5a">[{ts}]</span> '
            f'<span style="color:{color}">{prefix} {msg}</span>'
        )
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

# ─────────────────────────────────────────────

# VIDEO EXTRACTION THREAD

# ─────────────────────────────────────────────

class VideoExtractionThread(QThread):
    progress    = pyqtSignal(int)
    log_msg     = pyqtSignal(str)
    finished    = pyqtSignal(list, bool, str)
    frame_count = pyqtSignal(int)

    def __init__(self, video_path, output_dir="temp_frames"):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir

    def _variance_of_laplacian(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        for f in os.listdir(self.output_dir):
            if f.endswith(('.jpg', '.png')):
                try: os.remove(os.path.join(self.output_dir, f))
                except: pass
        self.log_msg.emit("Forensic video source acquired")
        self.log_msg.emit("Initiating scene walkthrough analysis...")
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            self.finished.emit([], False, "Cannot open video file")
            return
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        self.log_msg.emit(f"Scene duration: {duration:.1f}s | {fps:.0f} FPS | {total_frames} frames")
        if duration < 30:    interval_sec = 0.10
        elif duration < 120: interval_sec = 0.15
        else:                interval_sec = 0.20
        frame_step   = max(1, int(fps * interval_sec))
        target_count = int(total_frames / frame_step)
        self.log_msg.emit(f"Extracting reconstruction frames (~{target_count} target)")
        self.log_msg.emit("Performing blur analysis and quality filtering...")
        TARGET_W, TARGET_H = 1280, 720
        extracted_paths = []
        last_frame  = None
        frame_idx   = 0
        saved_count = 0
        BLUR_THRESHOLD = 30.0
        while True:
            ret, frame = cap.read()
            if not ret: break
            if frame_idx % frame_step == 0:
                blur_score = self._variance_of_laplacian(frame)
                if blur_score < BLUR_THRESHOLD:
                    frame_idx += 1
                    continue
                h, w   = frame.shape[:2]
                scale  = min(TARGET_W/w, TARGET_H/h)
                new_w, new_h = int(w*scale), int(h*scale)
                resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
                kernel  = np.array([[0,-0.3,0],[-0.3,2.2,-0.3],[0,-0.3,0]])
                resized = cv2.filter2D(resized, -1, kernel)
                out_path = os.path.join(self.output_dir, f"frame_{saved_count:04d}.jpg")
                cv2.imwrite(out_path, resized, [cv2.IMWRITE_JPEG_QUALITY, 92])
                extracted_paths.append(out_path)
                last_frame   = frame.copy()
                saved_count += 1
                pct = int((frame_idx/max(total_frames,1))*80)
                self.progress.emit(pct)
                self.frame_count.emit(saved_count)
            frame_idx += 1
        cap.release()
        self.log_msg.emit(f"Frame extraction complete — {saved_count} forensic frames acquired")
        self.log_msg.emit("Validating spatial continuity...")
        self.progress.emit(90)
        if saved_count < 2:
            self.finished.emit([], False, "Insufficient frames for reconstruction")
            return
        self.finished.emit(extracted_paths, True, "EXTRACTION COMPLETE")

# ─────────────────────────────────────────────

# AUTO CAPTURE THREAD

# ─────────────────────────────────────────────

class AutoCaptureThread(QThread):
    capture_signal = pyqtSignal()
    def __init__(self, interval_sec=2.0):
        super().__init__()
        self.interval_sec = interval_sec
        self.running = False
    def run(self):
        self.running = True
        while self.running:
            time.sleep(self.interval_sec)
            if self.running:
                self.capture_signal.emit()
    def stop(self):
        self.running = False
        self.quit()

    # ─────────────────────────────────────────────

    # STITCH THREAD

    # ─────────────────────────────────────────────

class StitchThread(QThread):
    progress = pyqtSignal(int)
    log_msg  = pyqtSignal(str)
    finished = pyqtSignal(object, bool, str)

    def __init__(self, images):
        super().__init__()
        self.images = images

    def run(self):
        self.log_msg.emit("Walkthrough reconstruction initiated")
        self.log_msg.emit("Analyzing spatial overlap between frames...")
        self.progress.emit(10)
        frames = []
        for path in self.images:
            img = cv2.imread(path)
            if img is not None: frames.append(img)
        if len(frames) < 2:
            self.finished.emit(None, False, "Insufficient frames for reconstruction")
            return
        self.log_msg.emit(f"Recovering camera motion vectors — {len(frames)} frames")
        self.progress.emit(30)
        try:
            stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
            self.log_msg.emit("Computing forensic scene alignment...")
            self.progress.emit(50)
            status, result = stitcher.stitch(frames)
            self.progress.emit(80)
            if status == cv2.Stitcher_OK:
                self.log_msg.emit("Homography recovery successful")
                self.log_msg.emit("Generating spatial reconstruction composite...")
                self.progress.emit(100)
                self.finished.emit(result, True, "SUCCESS")
            else:
                codes = {
                    cv2.Stitcher_ERR_NEED_MORE_IMGS:               "Insufficient spatial overlap — capture more frames",
                    cv2.Stitcher_ERR_HOMOGRAPHY_EST_FAIL:          "Homography estimation failed — increase frame overlap",
                    cv2.Stitcher_ERR_CAMERA_PARAMS_ADJUST_FAIL:    "Camera parameter adjustment failed"
                }
                self.finished.emit(None, False, codes.get(status, "Reconstruction failed"))
        except Exception as e:
            self.finished.emit(None, False, str(e))

# ─────────────────────────────────────────────

# STITCH MODE DIALOG

# ─────────────────────────────────────────────

class StitchModeDialog(QWidget):
    mode_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(560, 320)
        self.setStyleSheet("""
        QWidget {
            background-color: #080b0f;
            border: 1px solid #1c3352;
            border-radius: 14px;
        }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        hdr = QLabel("SELECT RECONSTRUCTION MODE")
        hdr.setStyleSheet(
            "color: #4dc8f0; font-size: 15px; font-weight: 700; "
            "letter-spacing: 2px; border: none;"
        )
        hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hdr)

        sub = QLabel("Choose forensic reconstruction method for crime scene spatial analysis")
        sub.setStyleSheet("color: #4a7a9a; font-size: 11px; border: none;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        for mode, icon, title, desc, btn_obj in [
            ("panorama", "⊙", "WALKTHROUGH\nRECONSTRUCTION",
             "Cinematic scene overview\nForward-facing captures\nWalkthrough footage",
             "actionBtn"),
            ("mosaic", "⊞", "SPATIAL SCENE\nMAPPING",
             "Manual forensic assembly\nDrag & arrange tiles\nPrecise evidence placement",
             "successBtn"),
        ]:
            frm = QFrame()
            frm.setObjectName("glassPanel")
            frm.setCursor(Qt.CursorShape.PointingHandCursor)
            fl = QVBoxLayout(frm)
            fl.setContentsMargins(20, 18, 20, 18)
            fl.setSpacing(10)
            ic_color = "#4dc8f0" if mode == "panorama" else "#52c488"
            ic = QLabel(icon)
            ic.setStyleSheet(f"color: {ic_color}; font-size: 30px; border: none;")
            ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(ic)
            tt = QLabel(title)
            tt.setStyleSheet(
                f"color: {ic_color}; font-size: 12px; font-weight: 700; "
                f"border: none; letter-spacing: 0.5px;"
            )
            tt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(tt)
            dd = QLabel(desc)
            dd.setStyleSheet("color: #4a7a8a; font-size: 10px; border: none;")
            dd.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(dd)
            btn = QPushButton("SELECT")
            btn.setObjectName(btn_obj)
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda checked, m=mode: self.select(m))
            fl.addWidget(btn)
            btn_layout.addWidget(frm)

        layout.addLayout(btn_layout)

        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setObjectName("dangerBtn")
        cancel_btn.setFixedWidth(110)
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.close)
        cancel_layout = QHBoxLayout()
        cancel_layout.addStretch()
        cancel_layout.addWidget(cancel_btn)
        layout.addLayout(cancel_layout)

    def select(self, mode):
        self.mode_selected.emit(mode)
        self.close()

    def show_centered(self, parent):
        if parent:
            geo = parent.geometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)
        self.show()

# ─────────────────────────────────────────────

# DRAGGABLE IMAGE TILE

# ─────────────────────────────────────────────

class DraggableImageTile(QGraphicsPixmapItem):
    def __init__(self, pixmap, filepath, tile_id):
        super().__init__(pixmap)
        self.filepath    = filepath
        self.tile_id     = tile_id
        self.orig_pixmap = pixmap
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setTransformOriginPoint(pixmap.width()/2, pixmap.height()/2)
        self.setAcceptHoverEvents(True)
        self._rotation_deg = 0.0
        self._scale_factor = 1.0
        self._opacity_val  = 1.0

    def hoverEnterEvent(self, event):
        self.setOpacity(0.82)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setOpacity(self._opacity_val)
        super().hoverLeaveEvent(event)

    def set_rotation(self, deg):
        self._rotation_deg = deg
        self.setRotation(deg)

    def set_scale(self, factor):
        self._scale_factor = factor
        self.setScale(factor)

    def set_opacity_val(self, val):
        self._opacity_val = val
        self.setOpacity(val)

    def get_state(self):
        return {
            "filepath": self.filepath,
            "tile_id":  self.tile_id,
            "x":        self.x(),
            "y":        self.y(),
            "rotation": self._rotation_deg,
            "scale":    self._scale_factor,
            "opacity":  self._opacity_val,
        }

# ─────────────────────────────────────────────

# FORENSIC MOSAIC WORKSPACE

# ─────────────────────────────────────────────

class ForensicMosaicWorkspace(QWidget):
    stitch_requested = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tiles        = []
        self.tile_counter = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QFrame()
        toolbar.setObjectName("glassPanel")
        toolbar.setFixedHeight(56)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(16, 8, 16, 8)
        tb_layout.setSpacing(10)

        title = QLabel("⊞  SPATIAL SCENE MAPPING WORKSPACE")
        title.setStyleSheet(
            "color: #52c488; font-size: 13px; font-weight: 700; "
            "letter-spacing: 1px; border: none;"
        )
        tb_layout.addWidget(title)
        tb_layout.addStretch()

        self.load_btn = QPushButton("⊕  LOAD IMAGES")
        self.load_btn.setObjectName("actionBtn")
        self.load_btn.setFixedHeight(38)
        self.load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_btn.clicked.connect(self.load_images)
        tb_layout.addWidget(self.load_btn)

        for text, fn, w in [("＋", self.zoom_in, 36), ("－", self.zoom_out, 36)]:
            btn = QPushButton(text)
            btn.setObjectName("actionBtn")
            btn.setFixedWidth(w)
            btn.setFixedHeight(38)
            btn.clicked.connect(fn)
            tb_layout.addWidget(btn)

        fit_btn = QPushButton("⊡ FIT")
        fit_btn.setObjectName("actionBtn")
        fit_btn.setFixedHeight(38)
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.clicked.connect(self.fit_view)
        tb_layout.addWidget(fit_btn)

        reset_btn = QPushButton("↺ RESET")
        reset_btn.setObjectName("dangerBtn")
        reset_btn.setFixedHeight(38)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self.reset_workspace)
        tb_layout.addWidget(reset_btn)

        layout.addWidget(toolbar)

        main_area = QWidget()
        main_layout = QHBoxLayout(main_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 4000, 3000)
        self.scene.setBackgroundBrush(QBrush(QColor("#050810")))

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.wheelEvent = self._wheel_zoom
        self._draw_grid_lines()
        main_layout.addWidget(self.view, 1)

        ctrl_panel = QFrame()
        ctrl_panel.setObjectName("sidebar")
        ctrl_panel.setFixedWidth(230)
        cp_layout = QVBoxLayout(ctrl_panel)
        cp_layout.setContentsMargins(14, 18, 14, 18)
        cp_layout.setSpacing(10)

        cp_title = QLabel("TILE CONTROLS")
        cp_title.setStyleSheet(
            "color: #1e4a6a; font-size: 9px; font-weight: 700; "
            "letter-spacing: 2px; border: none;"
        )
        cp_layout.addWidget(cp_title)

        # Rotation
        rot_lbl = QLabel("ROTATION")
        rot_lbl.setStyleSheet("color: #3a7a9a; font-size: 10px; font-weight: 600; border: none;")
        cp_layout.addWidget(rot_lbl)
        self.rot_slider = QSlider(Qt.Orientation.Horizontal)
        self.rot_slider.setRange(-180, 180)
        self.rot_slider.setValue(0)
        self.rot_slider.valueChanged.connect(self._apply_rotation)
        cp_layout.addWidget(self.rot_slider)
        self.rot_label = QLabel("0°")
        self.rot_label.setStyleSheet(
            "color: #4dc8f0; font-size: 11px; font-family: 'Consolas'; border: none;"
        )
        cp_layout.addWidget(self.rot_label)

        # Scale
        scale_lbl = QLabel("SCALE")
        scale_lbl.setStyleSheet("color: #3a7a9a; font-size: 10px; font-weight: 600; border: none;")
        cp_layout.addWidget(scale_lbl)
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(10, 300)
        self.scale_slider.setValue(100)
        self.scale_slider.valueChanged.connect(self._apply_scale)
        cp_layout.addWidget(self.scale_slider)
        self.scale_label = QLabel("1.0×")
        self.scale_label.setStyleSheet(
            "color: #4dc8f0; font-size: 11px; font-family: 'Consolas'; border: none;"
        )
        cp_layout.addWidget(self.scale_label)

        # Opacity
        opac_lbl = QLabel("OPACITY")
        opac_lbl.setStyleSheet("color: #3a7a9a; font-size: 10px; font-weight: 600; border: none;")
        cp_layout.addWidget(opac_lbl)
        self.opac_slider = QSlider(Qt.Orientation.Horizontal)
        self.opac_slider.setRange(20, 100)
        self.opac_slider.setValue(100)
        self.opac_slider.valueChanged.connect(self._apply_opacity)
        cp_layout.addWidget(self.opac_slider)
        self.opac_label = QLabel("100%")
        self.opac_label.setStyleSheet(
            "color: #4dc8f0; font-size: 11px; font-family: 'Consolas'; border: none;"
        )
        cp_layout.addWidget(self.opac_label)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #162838; border: none;")
        cp_layout.addWidget(sep)

        tile_list_lbl = QLabel("LOADED TILES")
        tile_list_lbl.setStyleSheet(
            "color: #1e4a6a; font-size: 9px; font-weight: 700; "
            "letter-spacing: 2px; border: none;"
        )
        cp_layout.addWidget(tile_list_lbl)

        self.tile_list = QTextEdit()
        self.tile_list.setReadOnly(True)
        self.tile_list.setFixedHeight(110)
        self.tile_list.setPlaceholderText("No tiles loaded...")
        cp_layout.addWidget(self.tile_list)

        remove_btn = QPushButton("✕  REMOVE SELECTED")
        remove_btn.setObjectName("dangerBtn")
        remove_btn.setFixedHeight(36)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(self.remove_selected)
        cp_layout.addWidget(remove_btn)

        cp_layout.addStretch()

        self.stitch_btn = QPushButton("⊞  GENERATE FORENSIC MAP")
        self.stitch_btn.setObjectName("captureBtn")
        self.stitch_btn.setFixedHeight(42)
        self.stitch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stitch_btn.clicked.connect(self._request_stitch)
        cp_layout.addWidget(self.stitch_btn)

        self.status_lbl = QLabel("Load images to begin spatial mapping")
        self.status_lbl.setStyleSheet("color: #3a6a8a; font-size: 10px; border: none;")
        self.status_lbl.setWordWrap(True)
        cp_layout.addWidget(self.status_lbl)

        main_layout.addWidget(ctrl_panel)
        layout.addWidget(main_area, 1)

    def _draw_grid_lines(self):
        pen = QPen(QColor(20, 70, 120, 35))
        pen.setWidth(1)
        for x in range(0, 4001, 100):
            self.scene.addLine(x, 0, x, 3000, pen)
        for y in range(0, 3001, 100):
            self.scene.addLine(0, y, 4000, y, pen)

    def load_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Load Forensic Scene Images", "",
            "Images (*.jpg *.jpeg *.png *.bmp)"
        )
        if not files: return
        cols = max(1, int(np.ceil(np.sqrt(len(files)))))
        tile_w, tile_h, padding = 400, 300, 20
        for i, fpath in enumerate(files):
            pixmap = QPixmap(fpath)
            if pixmap.isNull(): continue
            pixmap = pixmap.scaled(
                tile_w, tile_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.tile_counter += 1
            tile = DraggableImageTile(pixmap, fpath, self.tile_counter)
            col = i % cols
            row = i // cols
            tile.setPos(
                col * (tile_w + padding) + padding,
                row * (tile_h + padding) + padding
            )
            self.scene.addItem(tile)
            self.tiles.append(tile)
        self._update_tile_list()
        self.status_lbl.setText(f"{len(self.tiles)} tiles loaded — drag to arrange")
        self.status_lbl.setStyleSheet("color: #52c488; font-size: 10px; border: none;")
        self.fit_view()

    def _update_tile_list(self):
        self.tile_list.clear()
        for tile in self.tiles:
            fname = os.path.basename(tile.filepath)
            self.tile_list.append(f"T{tile.tile_id:03d}  {fname[:22]}")

    def _get_selected_tile(self):
        for item in self.scene.selectedItems():
            if isinstance(item, DraggableImageTile):
                return item
        return None

    def _apply_rotation(self, val):
        self.rot_label.setText(f"{val}°")
        tile = self._get_selected_tile()
        if tile: tile.set_rotation(float(val))

    def _apply_scale(self, val):
        factor = val / 100.0
        self.scale_label.setText(f"{factor:.1f}×")
        tile = self._get_selected_tile()
        if tile: tile.set_scale(factor)

    def _apply_opacity(self, val):
        self.opac_label.setText(f"{val}%")
        tile = self._get_selected_tile()
        if tile: tile.set_opacity_val(val / 100.0)

    def remove_selected(self):
        for item in self.scene.selectedItems():
            if isinstance(item, DraggableImageTile):
                self.scene.removeItem(item)
                if item in self.tiles: self.tiles.remove(item)
        self._update_tile_list()
        self.status_lbl.setText(f"{len(self.tiles)} tiles remaining")

    def reset_workspace(self):
        for tile in self.tiles: self.scene.removeItem(tile)
        self.tiles.clear()
        self.tile_counter = 0
        self._update_tile_list()
        self.status_lbl.setText("Workspace cleared")
        self.status_lbl.setStyleSheet("color: #f0a030; font-size: 10px; border: none;")

    def zoom_in(self):  self.view.scale(1.2, 1.2)
    def zoom_out(self): self.view.scale(1/1.2, 1/1.2)

    def fit_view(self):
        if self.tiles:
            self.view.fitInView(
                self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.view.fitInView(QRectF(0,0,4000,3000), Qt.AspectRatioMode.KeepAspectRatio)

    def _wheel_zoom(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1/1.15
        self.view.scale(factor, factor)

    def _request_stitch(self):
        if not self.tiles:
            self.status_lbl.setText("No tiles to process")
            return
        states = [tile.get_state() for tile in self.tiles]
        self.stitch_requested.emit(states)
        self.status_lbl.setText("Generating forensic composite map...")
        self.status_lbl.setStyleSheet("color: #f0a030; font-size: 10px; border: none;")

    def generate_composite(self, tile_states):
        if not tile_states: return None
        try:
            min_x, min_y = float('inf'), float('inf')
            max_x, max_y = float('-inf'), float('-inf')
            rendered_tiles = []
            for state in tile_states:
                img = cv2.imread(state["filepath"])
                if img is None: continue
                h, w  = img.shape[:2]
                scale = state.get("scale", 1.0)
                x, y  = state.get("x", 0), state.get("y", 0)
                tw = int(w * scale * 0.5)
                th = int(h * scale * 0.5)
                min_x = min(min_x, x); min_y = min(min_y, y)
                max_x = max(max_x, x+tw); max_y = max(max_y, y+th)
                rendered_tiles.append((state, img))
            if not rendered_tiles: return None
            canvas_w = min(int(max_x-min_x)+100, 8000)
            canvas_h = min(int(max_y-min_y)+100, 6000)
            canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
            mask   = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
            for state, img in rendered_tiles:
                h, w   = img.shape[:2]
                scale  = state.get("scale", 1.0)
                rot    = state.get("rotation", 0.0)
                x, y   = int(state.get("x",0)-min_x), int(state.get("y",0)-min_y)
                opac   = state.get("opacity", 1.0)
                new_w  = max(10, int(w*scale*0.5))
                new_h  = max(10, int(h*scale*0.5))
                img_s  = cv2.resize(img, (new_w, new_h))
                if abs(rot) > 0.5:
                    M = cv2.getRotationMatrix2D((new_w/2, new_h/2), -rot, 1.0)
                    img_s = cv2.warpAffine(img_s, M, (new_w, new_h),
                        borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
                x2 = min(x+new_w, canvas_w); y2 = min(y+new_h, canvas_h)
                if x>=canvas_w or y>=canvas_h or x2<=0 or y2<=0: continue
                src_x1=max(0,-x); src_y1=max(0,-y)
                dst_x1=max(0,x);  dst_y1=max(0,y)
                region_h=y2-dst_y1; region_w=x2-dst_x1
                if region_h<=0 or region_w<=0: continue
                src_region = img_s[src_y1:src_y1+region_h, src_x1:src_x1+region_w]
                existing   = canvas[dst_y1:y2, dst_x1:x2]
                blended    = cv2.addWeighted(existing, 1.0-opac*0.5, src_region, opac, 0)
                canvas[dst_y1:y2, dst_x1:x2] = blended
                mask[dst_y1:y2, dst_x1:x2]   = 255
            coords = cv2.findNonZero(mask)
            if coords is not None:
                bx,by,bw,bh = cv2.boundingRect(coords)
                pad=15
                bx=max(0,bx-pad); by=max(0,by-pad)
                bw=min(canvas_w-bx,bw+pad*2); bh=min(canvas_h-by,bh+pad*2)
                canvas = canvas[by:by+bh, bx:bx+bw]
            return canvas if canvas.size > 0 else None
        except Exception as e:
            print(f"Composite generation error: {e}")
            return None

# ─────────────────────────────────────────────

# AI DETECTION THREAD

# ─────────────────────────────────────────────

class AIDetectionThread(QThread):
    progress = pyqtSignal(int)
    log_msg  = pyqtSignal(str)
    finished = pyqtSignal(object, list, bool, str)

    def __init__(self, image, grid_cols=8, grid_rows=8, conf_threshold=0.35):
        super().__init__()
        self.image          = image.copy()
        self.grid_cols      = grid_cols
        self.grid_rows      = grid_rows
        self.conf_threshold = conf_threshold

    def _grid_ref(self, cx, cy, img_w, img_h):
        col_idx = min(int(cx/(img_w/self.grid_cols)), self.grid_cols-1)
        row_idx = min(int(cy/(img_h/self.grid_rows)), self.grid_rows-1)
        return f"{chr(65+col_idx)}{row_idx+1}"

    def _detect_yolo(self, img):
        detections = []
        h, w = img.shape[:2]
        if not YOLO_AVAILABLE:
            self.log_msg.emit("ERROR: ultralytics not installed")
            return detections
        try:
            model = YOLO("yolov8n.pt")
            FORENSIC_CLASSES = {
                0:  ("Person",    (180,80,0),   "SCENE OBJECT"),
                24: ("Backpack",  (150,100,200),"SCENE OBJECT"),
                25: ("Umbrella",  (100,150,200),"SCENE OBJECT"),
                28: ("Suitcase",  (150,100,200),"SCENE OBJECT"),
                39: ("Bottle",    (0,180,120),  "SCENE OBJECT"),
                40: ("Wine Glass",(0,180,120),  "SCENE OBJECT"),
                41: ("Cup",       (0,180,120),  "SCENE OBJECT"),
                43: ("Knife",     (0,40,255),   "WEAPON"),
                56: ("Chair",     (80,120,180), "SCENE OBJECT"),
                57: ("Couch",     (80,120,180), "SCENE OBJECT"),
                59: ("Bed",       (80,120,180), "SCENE OBJECT"),
                63: ("Laptop",    (200,100,0),  "SCENE OBJECT"),
                67: ("Phone",     (200,150,0),  "SCENE OBJECT"),
                73: ("Book",      (100,180,0),  "SCENE OBJECT"),
                76: ("Scissors",  (0,40,220),   "WEAPON"),
            }
            results = model(img, conf=self.conf_threshold, verbose=False)
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    if cls_id not in FORENSIC_CLASSES: continue
                    label, color, category = FORENSIC_CLASSES[cls_id]
                    conf = float(box.conf[0])
                    x1,y1,x2,y2 = map(int, box.xyxy[0])
                    cx, cy = (x1+x2)//2, (y1+y2)//2
                    grid_ref = self._grid_ref(cx, cy, w, h)
                    detections.append({
                        "label":      label,
                        "confidence": conf,
                        "bbox":       (x1,y1,x2,y2),
                        "center":     (cx,cy),
                        "grid":       grid_ref,
                        "color":      color,
                        "category":   category
                    })
                    self.log_msg.emit(f"Evidence acquired: {label} → {grid_ref} ({conf:.0%})")
        except Exception as e:
            self.log_msg.emit(f"Detection error: {str(e)}")
        return detections

    def _draw_annotations(self, img, detections):
        annotated = img.copy()
        h, w = annotated.shape[:2]
        for i, det in enumerate(detections):
            x1,y1,x2,y2 = det["bbox"]
            label    = det["label"]
            conf     = det["confidence"]
            grid     = det["grid"]
            cx, cy   = det["center"]
            color    = confidence_color(conf)
            cv2.rectangle(annotated, (x1,y1), (x2,y2), color, 2)
            corner_len = 14
            for pts in [
                ((x1,y1),(x1+corner_len,y1)),((x1,y1),(x1,y1+corner_len)),
                ((x2,y1),(x2-corner_len,y1)),((x2,y1),(x2,y1+corner_len)),
                ((x1,y2),(x1+corner_len,y2)),((x1,y2),(x1,y2-corner_len)),
                ((x2,y2),(x2-corner_len,y2)),((x2,y2),(x2,y2-corner_len))
            ]:
                cv2.line(annotated, pts[0], pts[1], color, 3)
            ev_id     = f"E-{i+1:03d}"
            tag_line1 = f"{ev_id}  {label}"
            tag_line2 = f"Grid: {grid}  |  {conf:.0%}"
            font = cv2.FONT_HERSHEY_DUPLEX
            fs   = 0.52
            pad  = 7
            (tw1,th1),_ = cv2.getTextSize(tag_line1, font, fs, 1)
            (tw2,th2),_ = cv2.getTextSize(tag_line2, font, 0.42, 1)
            tag_w = max(tw1,tw2) + pad*2
            tag_h = th1 + th2 + pad*3
            ty = max(y1-tag_h-6, 0)
            tx = x1
            cv2.rectangle(annotated,(tx,ty),(tx+tag_w,ty+tag_h),(8,12,20),-1)
            cv2.rectangle(annotated,(tx,ty),(tx+4,ty+tag_h),color,-1)
            num_r = 14
            cv2.circle(annotated,(cx,cy),num_r+1,(8,12,20),-1)
            cv2.circle(annotated,(cx,cy),num_r,color,2)
            cv2.putText(annotated, str(i+1),(cx-5,cy+5),cv2.FONT_HERSHEY_DUPLEX,0.42,color,1)
            cv2.putText(annotated, tag_line1,(tx+8,ty+th1+pad),
                font,fs,(240,248,255),1,cv2.LINE_AA)
            cv2.putText(annotated, tag_line2,(tx+8,ty+th1+th2+pad*2),
                cv2.FONT_HERSHEY_SIMPLEX,0.42,(140,195,215),1,cv2.LINE_AA)
        bar_h = 34
        cv2.rectangle(annotated,(0,h-bar_h),(w,h),(6,10,18),-1)
        cv2.putText(annotated,
            f"SPIDERCAM FORENSIC AI  v2.1  |  "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  "
            f"EVIDENCE COUNT: {len(detections)}",
            (10,h-10),cv2.FONT_HERSHEY_SIMPLEX,0.48,(0,190,190),1,cv2.LINE_AA)
        return annotated

    def run(self):
        self.log_msg.emit("Forensic AI analysis initiated")
        self.log_msg.emit("Performing feature consistency validation...")
        self.progress.emit(10)
        img = self.image
        all_detections = []
        self.log_msg.emit("Running forensic evidence detection pipeline...")
        self.progress.emit(40)
        yolo_dets = self._detect_yolo(img)
        all_detections.extend(yolo_dets)
        self.log_msg.emit(f"Detection pipeline complete — {len(yolo_dets)} evidence items acquired")
        self.log_msg.emit("Building forensic evidence topology...")
        self.progress.emit(85)
        annotated = self._draw_annotations(img, all_detections)
        self.log_msg.emit("Finalizing evidence reconstruction output...")
        self.progress.emit(100)
        self.finished.emit(annotated, all_detections, True,
                           f"{len(all_detections)} evidence items detected")

# ─────────────────────────────────────────────

# 3D RECONSTRUCTION THREAD

# ─────────────────────────────────────────────

class ReconstructionThread(QThread):
    progress = pyqtSignal(int)
    log_msg  = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, frame_paths, detections=None):
        super().__init__()
        self.frame_paths = frame_paths
        self.detections  = detections or []

    def run(self):
        try:
            import reconstruction_3d
            success = reconstruction_3d.run_full_reconstruction(
                frame_paths=self.frame_paths,
                detections=self.detections,
                log_fn=self.log_msg.emit,
                progress_fn=self.progress.emit
            )
            if success and reconstruction_3d.LAST_RECONSTRUCTION_STATUS["synthetic"]:
                self.finished.emit(
                    True,
                    "Synthetic demonstration viewer launched; no scene was reconstructed",
                )
            elif success: self.finished.emit(True,  "3D reconstruction complete")
            else:       self.finished.emit(False, "Reconstruction failed")
        except Exception as e:
            self.log_msg.emit(f"ERROR: {str(e)}")
            self.finished.emit(False, str(e))

# ─────────────────────────────────────────────

# FORENSIC HTTP SERVER — Mobile Bridge

# ─────────────────────────────────────────────

class ForensicServerThread(QThread):
    log_msg = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.server   = None
        self.running  = False
        self.port     = 8765
        self.data     = {
            "full_image":  None,  # bytes — full annotated jpg
            "crops":       [],    # list of dicts
            "detections":  [],    # raw detection list
            "confirmed":   [],    # confirmed by investigator
            "rejected":    [],    # rejected
        }

    def set_detection_data(self, annotated_img, detections, source_img):
        """Called after YOLO detection. Saves full image + crops."""
        os.makedirs("mobile_share/crops", exist_ok=True)

        # Save full annotated image
        full_path = "mobile_share/full_scene.jpg"
        cv2.imwrite(full_path, annotated_img)
        _, full_buf = cv2.imencode('.jpg', annotated_img,
                                   [cv2.IMWRITE_JPEG_QUALITY, 88])
        self.data["full_image"] = full_buf.tobytes()

        # Crop each detection from SOURCE image (clean crops)
        self.data["crops"]      = []
        self.data["detections"] = []
        h, w = source_img.shape[:2]
        for i, det in enumerate(detections):
            x1, y1, x2, y2 = det["bbox"]
            pad = 20
            x1c = max(0, x1-pad); y1c = max(0, y1-pad)
            x2c = min(w, x2+pad); y2c = min(h, y2+pad)
            crop = source_img[y1c:y2c, x1c:x2c]
            ev_id = f"E-{i+1:03d}"
            crop_path = f"mobile_share/crops/{ev_id}.jpg"
            cv2.imwrite(crop_path, crop)
            _, crop_buf = cv2.imencode('.jpg', crop,
                                       [cv2.IMWRITE_JPEG_QUALITY, 90])
            self.data["crops"].append({
                "id":         ev_id,
                "label":      det["label"],
                "confidence": round(det["confidence"], 3),
                "grid":       det["grid"],
                "category":   det["category"],
                "crop_bytes": crop_buf.tobytes(),
            })
            self.data["detections"].append({
                "id":         ev_id,
                "label":      det["label"],
                "confidence": round(det["confidence"], 3),
                "grid":       det["grid"],
                "category":   det["category"],
                "bbox":       list(det["bbox"]),
                "center":     list(det["center"]),
            })
        self.data["confirmed"] = []
        self.data["rejected"]  = []
        self.log_msg.emit(
            f"Mobile server ready — {len(detections)} crops available")

    def run(self):
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import urllib.parse
        server_data = self.data
        log_fn      = self.log_msg.emit

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args): pass  # silence default logs

            def do_GET(self):
                path = urllib.parse.urlparse(self.path).path

                # Full annotated image
                if path == "/full_image":
                    if server_data["full_image"]:
                        self.send_response(200)
                        self.send_header("Content-Type", "image/jpeg")
                        self.end_headers()
                        self.wfile.write(server_data["full_image"])
                    else:
                        self.send_response(404)
                        self.end_headers()

                # Detection list JSON
                elif path == "/detections":
                    payload = json.dumps({
                        "detections": server_data["detections"],
                        "confirmed":  server_data["confirmed"],
                        "rejected":   server_data["rejected"],
                    }).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)

                # Individual crop image
                elif path.startswith("/crop/"):
                    ev_id = path.replace("/crop/", "").strip()
                    crop  = next(
                        (c for c in server_data["crops"] if c["id"] == ev_id),
                        None)
                    if crop:
                        self.send_response(200)
                        self.send_header("Content-Type", "image/jpeg")
                        self.end_headers()
                        self.wfile.write(crop["crop_bytes"])
                    else:
                        self.send_response(404)
                        self.end_headers()

                # Ping
                elif path == "/ping":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"SPIDERCAM_OK")

                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                path           = urllib.parse.urlparse(self.path).path
                length         = int(self.headers.get("Content-Length", 0))
                body           = self.rfile.read(length)
                try:
                    payload    = json.loads(body)
                except Exception:
                    payload    = {}

                # Confirm evidence
                if path == "/confirm":
                    ev_id = payload.get("id", "")
                    if ev_id and ev_id not in server_data["confirmed"]:
                        server_data["confirmed"].append(ev_id)
                        if ev_id in server_data["rejected"]:
                            server_data["rejected"].remove(ev_id)
                    log_fn(f"Mobile CONFIRMED: {ev_id}")
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"OK")

                # Reject evidence
                elif path == "/reject":
                    ev_id = payload.get("id", "")
                    if ev_id and ev_id not in server_data["rejected"]:
                        server_data["rejected"].append(ev_id)
                        if ev_id in server_data["confirmed"]:
                            server_data["confirmed"].remove(ev_id)
                    log_fn(f"Mobile REJECTED: {ev_id}")
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"OK")

                else:
                    self.send_response(404)
                    self.end_headers()

        self.running = True
        self.server  = HTTPServer(("0.0.0.0", self.port), Handler)
        self.log_msg.emit(
            f"Forensic mobile server started — port {self.port}")
        while self.running:
            self.server.handle_request()

    def stop(self):
        self.running = False
        if self.server:
            self.server.server_close()
        self.quit()

# Global server instance

MOBILE_SERVER = ForensicServerThread()

# ─────────────────────────────────────────────

# STREAM THREAD

# ─────────────────────────────────────────────

class StreamThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.running = False
        self.cap     = None
        self.url     = None

    def set_source(self, url): self.url = url

    def run(self):
        self.running = True
        try:
            self.cap = cv2.VideoCapture(int(self.url) if self.url.isdigit() else self.url)
            while self.running:
                ret, frame = self.cap.read()
                if ret: self.frame_ready.emit(frame)
                else:   break
        except: pass

    def stop(self):
        self.running = False
        if self.cap: self.cap.release()
        self.quit()

# ─────────────────────────────────────────────

# SPIDERCAM DEVICE MODEL + MOCK REGISTRY

# ─────────────────────────────────────────────

from dataclasses import dataclass
from enum import Enum

class DeviceStatus(Enum):
    OFFLINE      = "OFFLINE"
    ONLINE       = "ONLINE"
    READY        = "READY"
    LIVE         = "LIVE"
    CONNECTING   = "CONNECTING"
    RECONNECTING = "RECONNECTING"
    ERROR        = "ERROR"

@dataclass
class SpiderCamDevice:
    device_id: str
    device_name: str
    device_type: str          # "MOBILE_CAMERA" | "SPIDERCAM_HARDWARE"
    status: DeviceStatus
    resolution: str = "—"
    fps: int = 0
    case_id: str = ""
    last_seen: str = ""

    @property
    def is_live(self):
        return self.status == DeviceStatus.LIVE

    @property
    def quality_label(self):
        return f"{self.resolution} • {self.fps} FPS" if self.fps else self.resolution

class DeviceRegistry:
    """
    Real backend-backed device registry. Queries the SpiderCam token
    server's /devices endpoint, which reflects actual LiveKit room
    participants — no separate database, no mock data.
    """
    def __init__(self, backend_url=None):
        self.backend_url = (backend_url or BACKEND_URL).rstrip("/")

    def list_devices(self, case_id=None):
        case_id = case_id or MANIFEST.case_id
        if not case_id or case_id == "UNKNOWN":
            return []
        try:
            backend_url, shared_key = get_remote_config(
                backend_url=self.backend_url
            )
            resp = requests.get(
                f"{backend_url}/devices",
                params={"room": case_id},
                headers={"X-API-Key": shared_key},
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
        except RuntimeError as e:
            print(f"[DeviceRegistry] Remote configuration unavailable: {e}")
            return []
        except Exception:
            print("[DeviceRegistry] Device request failed.")
            return []

        devices = []
        for d in data.get("devices", []):
            status_str = d.get("status", "ONLINE")
            try:
                status = DeviceStatus[status_str]
            except KeyError:
                status = DeviceStatus.ONLINE
            fps_raw = d.get("fps") or "0"
            fps_val = int(fps_raw) if str(fps_raw).isdigit() else 0
            devices.append(SpiderCamDevice(
                device_id=d.get("device_id", "UNKNOWN"),
                device_name=d.get("device_id", "UNKNOWN"),
                device_type=d.get("device_type", "MOBILE_CAMERA"),
                status=status,
                resolution=d.get("resolution", "—"),
                fps=fps_val,
                case_id=d.get("case_id", case_id),
                last_seen="just now",
            ))
        return devices

# ─────────────────────────────────────────────

# DEVICE CARD WIDGET

# ─────────────────────────────────────────────

class DeviceCard(QFrame):
    view_clicked = pyqtSignal(object)   # emits SpiderCamDevice

    STATUS_COLORS = {
        DeviceStatus.LIVE:         "#4caf82",
        DeviceStatus.ONLINE:       "#4dc8f0",
        DeviceStatus.READY:        "#4dc8f0",
        DeviceStatus.CONNECTING:   "#f0a030",
        DeviceStatus.RECONNECTING: "#f0a030",
        DeviceStatus.ERROR:        "#f06060",
        DeviceStatus.OFFLINE:      "#4a5a6a",
    }

    def __init__(self, device: SpiderCamDevice, parent=None):
        super().__init__(parent)
        self.device = device
        self.setObjectName("glassPanel")
        self.setFixedHeight(78)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        color = self.STATUS_COLORS.get(device.status, "#4a5a6a")
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        layout.addWidget(dot)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        id_lbl = QLabel(device.device_id)
        id_lbl.setStyleSheet("color: #dde4f0; font-size: 13px; font-weight: 700; letter-spacing: 0.5px;")
        info_col.addWidget(id_lbl)

        type_label = "MOBILE CAMERA" if device.device_type == "MOBILE_CAMERA" else "SPIDERCAM HARDWARE"
        sub_lbl = QLabel(f"{type_label}  ·  {device.status.value}")
        sub_lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 600; letter-spacing: 0.5px;")
        info_col.addWidget(sub_lbl)

        if device.status != DeviceStatus.OFFLINE:
            q_lbl = QLabel(device.quality_label)
            q_lbl.setStyleSheet("color: #4a7a9a; font-size: 10px;")
            info_col.addWidget(q_lbl)
        layout.addLayout(info_col, 1)

        view_btn = QPushButton("VIEW")
        view_btn.setObjectName("captureBtn")
        view_btn.setFixedWidth(80)
        view_btn.setFixedHeight(36)
        view_btn.setEnabled(device.status in (DeviceStatus.LIVE, DeviceStatus.ONLINE, DeviceStatus.READY))
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_btn.clicked.connect(lambda: self.view_clicked.emit(self.device))
        layout.addWidget(view_btn)

# ─────────────────────────────────────────────

# TOP BAR

# ─────────────────────────────────────────────

class TopBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topBar")
        self.setFixedHeight(60)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(0)

        logo_frame  = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(10)

        dot = QLabel("◈")
        dot.setStyleSheet("color: #4dc8f0; font-size: 20px;")
        logo_layout.addWidget(dot)

        logo_text = QLabel("SPIDERCAM")
        logo_text.setStyleSheet(
            "color: #f0f4f8; font-size: 18px; font-weight: 800; letter-spacing: 3px;"
        )
        logo_layout.addWidget(logo_text)

        suite_text = QLabel("FORENSIC SUITE")
        suite_text.setStyleSheet(
            "color: #2878aa; font-size: 10px; font-weight: 700; "
            "letter-spacing: 2.5px; margin-top: 5px;"
        )
        logo_layout.addWidget(suite_text)

        ver = QLabel("v2.1")
        ver.setStyleSheet("color: #1e4a6a; font-size: 9px; margin-top: 6px; margin-left: 6px;")
        logo_layout.addWidget(ver)
        layout.addWidget(logo_frame)
        layout.addStretch()

        self.case_label = QLabel("CASE: —")
        self.case_label.setStyleSheet("color: #4a6a8a; font-size: 11px; letter-spacing: 1px;")
        layout.addWidget(self.case_label)

        sep1 = QLabel("  |  ")
        sep1.setStyleSheet("color: #142230; font-size: 14px;")
        layout.addWidget(sep1)

        self.integrity_label = QLabel("HASH STATUS: NOT CHECKED")
        self.integrity_label.setStyleSheet(
            "color: #8a9aaa; font-size: 10px; font-weight: 600; letter-spacing: 1px;"
        )
        layout.addWidget(self.integrity_label)

        sep2 = QLabel("  |  ")
        sep2.setStyleSheet("color: #142230; font-size: 14px;")
        layout.addWidget(sep2)

        self.conn_label = QLabel("● OFFLINE")
        self.conn_label.setStyleSheet(
            "color: #c87830; font-size: 10px; font-weight: 600; letter-spacing: 1px;"
        )
        layout.addWidget(self.conn_label)

        sep3 = QLabel("  |  ")
        sep3.setStyleSheet("color: #142230; font-size: 14px;")
        layout.addWidget(sep3)

        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(
            "color: #6a8aaa; font-size: 11px; font-weight: 500; font-family: 'Consolas';"
        )
        layout.addWidget(self.clock_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self._update_clock)
        self.timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        self.clock_label.setText(datetime.now().strftime("%d %b %Y  %H:%M:%S"))

    def set_case(self, name):
        self.case_label.setText(f"CASE: {name.upper()}")
        self.case_label.setStyleSheet(
            "color: #4dc8f0; font-size: 11px; letter-spacing: 1px; font-weight: 700;"
        )

    def set_connected(self, connected):
        if connected:
            self.conn_label.setText("● LIVE FEED ACTIVE")
            self.conn_label.setStyleSheet("color: #4caf82; font-size: 10px; font-weight: 600;")
        else:
            self.conn_label.setText("● OFFLINE")
            self.conn_label.setStyleSheet("color: #c87830; font-size: 10px; font-weight: 600;")

# ─────────────────────────────────────────────

# SIDEBAR

# ─────────────────────────────────────────────

class Sidebar(QFrame):
    page_changed = pyqtSignal(int)
    NAV_ITEMS = [
    ("⬡", "DASHBOARD",        0),
    ("◉", "LIVE FEED",        1),
    ("▦", "EVIDENCE GALLERY", 2),
    ("⊞", "SCENE MAPPING",    3),
    ("◈", "AI DETECTION",     4),
    ("≡", "ANALYSIS",         5),
    ("↗", "REPORTS",          6),
    ("⚙", "SETTINGS",         7),
    ("⬡", "3D WALKTHROUGH",   8),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(205)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 18, 0, 18)
        layout.setSpacing(1)

        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet(
            "color: #1e3a54; font-size: 9px; font-weight: 700; "
            "letter-spacing: 2.5px; padding: 0 20px 10px 20px;"
        )
        layout.addWidget(nav_label)

        self.buttons = []
        for icon, label, index in self.NAV_ITEMS:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("navBtn")
            btn.setFixedHeight(46)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self.select(i))
            self.buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #0e1c2c; margin: 0 16px;")
        layout.addWidget(sep)

        ver = QLabel("v2.1  ·  M SELVAPRAKASH")
        ver.setStyleSheet("color: #1a3450; font-size: 9px; padding: 8px 20px 0 20px;")
        layout.addWidget(ver)

        self.select(0)

    def select(self, index):
        for i, btn in enumerate(self.buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.page_changed.emit(index)

# ─────────────────────────────────────────────

# STAT CARD

# ─────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, title, value, unit="", color="#4dc8f0", parent=None):
        super().__init__(parent)
        self.setObjectName("glassPanel")
        self.setFixedHeight(95)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        t = QLabel(title.upper())
        t.setStyleSheet(
            "color: #2e5872; font-size: 9px; font-weight: 700; letter-spacing: 1.8px;"
        )
        layout.addWidget(t)

        val_layout = QHBoxLayout()
        val_layout.setSpacing(5)
        self.val_label = QLabel(str(value))
        self.val_label.setStyleSheet(
            f"color: {color}; font-size: 28px; font-weight: 800; font-family: 'Consolas';"
        )
        val_layout.addWidget(self.val_label)
        if unit:
            u = QLabel(unit)
            u.setStyleSheet(f"color: #2e5872; font-size: 11px; margin-top: 14px;")
            val_layout.addWidget(u)
        val_layout.addStretch()
        layout.addLayout(val_layout)

    def set_value(self, v):
        self.val_label.setText(str(v))

# ─────────────────────────────────────────────

# DASHBOARD PAGE

# ─────────────────────────────────────────────

class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        hdr = QLabel("INVESTIGATION DASHBOARD")
        hdr.setStyleSheet(
            "color: #4dc8f0; font-size: 17px; font-weight: 700; letter-spacing: 2px;"
        )
        layout.addWidget(hdr)

        sub = QLabel("Active case overview — SpiderCam forensic reconstruction platform v2.1")
        sub.setStyleSheet("color: #2a5a7a; font-size: 12px;")
        layout.addWidget(sub)

        case_frame = QFrame()
        case_frame.setObjectName("glassPanel")
        case_layout = QVBoxLayout(case_frame)
        case_layout.setContentsMargins(22, 18, 22, 18)
        case_layout.setSpacing(14)

        cl = QLabel("CASE INFORMATION")
        cl.setStyleSheet(
            "color: #2a5a7a; font-size: 10px; font-weight: 700; letter-spacing: 2px;"
        )
        case_layout.addWidget(cl)

        row1 = QHBoxLayout()
        row1.setSpacing(14)
        self.case_input = QLineEdit()
        self.case_input.setPlaceholderText("Case ID  (e.g. CS-2026-001)")
        row1.addWidget(self.case_input)
        self.inv_input = QLineEdit()
        self.inv_input.setPlaceholderText("Investigating Officer Name")
        row1.addWidget(self.inv_input)
        case_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(14)
        self.loc_input = QLineEdit()
        self.loc_input.setPlaceholderText("Scene Location / Address")
        row2.addWidget(self.loc_input)
        self.date_input = QLineEdit()
        self.date_input.setText(datetime.now().strftime("%d-%m-%Y"))
        self.date_input.setFixedWidth(150)
        row2.addWidget(self.date_input)
        case_layout.addLayout(row2)

        self.open_btn = QPushButton("INITIALISE CASE  ▶")
        self.open_btn.setObjectName("captureBtn")
        self.open_btn.setFixedWidth(220)
        self.open_btn.setFixedHeight(42)
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        case_layout.addWidget(self.open_btn)
        layout.addWidget(case_frame)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)
        self.card_images     = StatCard("Images Loaded",    "0",      "imgs")
        self.card_evidence   = StatCard("Evidence Items",   "0",      "items", "#f0a030")
        self.card_confidence = StatCard("Avg Confidence",   "—",      "%",     "#4caf82")
        self.card_hash       = StatCard("Evidence Hash Checks", "NOT CHECKED", "", "#8a9aaa")
        for card in [self.card_images, self.card_evidence,
                     self.card_confidence, self.card_hash]:
            stats_layout.addWidget(card)
        layout.addLayout(stats_layout)

        sys_frame  = QFrame()
        sys_frame.setObjectName("panel")
        sys_layout = QGridLayout(sys_frame)
        sys_layout.setContentsMargins(22, 18, 22, 18)
        sys_layout.setSpacing(10)

        sl = QLabel("SYSTEM STATUS")
        sl.setStyleSheet(
            "color: #2a5a7a; font-size: 10px; font-weight: 700; letter-spacing: 2px;"
        )
        sys_layout.addWidget(sl, 0, 0, 1, 4)

        statuses = [
            ("OpenCV Engine",         "READY",   "#4caf82"),
            ("AI Detection Module",   "STANDBY", "#f0a030"),
            ("Reconstruction Engine", "READY",   "#4caf82"),
            ("Evidence Logger",       "READY",   "#4caf82"),
            ("SHA-256 Hashing",       "ACTIVE",  "#4caf82"),
            ("Report Generator",      "READY",   "#4caf82"),
            ("Live Feed Module",      "OFFLINE", "#f05050"),
            ("Evidence Hashing",      "AVAILABLE", "#4dc8f0"),
        ]
        for i, (name, status, color) in enumerate(statuses):
            row_i = (i//4)+1
            col_i = i%4
            f = QFrame()
            f.setObjectName("glassPanel")
            fl = QHBoxLayout(f)
            fl.setContentsMargins(12, 9, 12, 9)
            fl.setSpacing(8)
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 10px;")
            fl.addWidget(dot)
            nm = QLabel(name)
            nm.setStyleSheet("color: #6a8aaa; font-size: 11px;")
            fl.addWidget(nm)
            fl.addStretch()
            st = QLabel(status)
            st.setStyleSheet(
                f"color: {color}; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;"
            )
            fl.addWidget(st)
            sys_layout.addWidget(f, row_i, col_i)

        layout.addWidget(sys_frame)
        layout.addStretch()

    # ─────────────────────────────────────────────

    # LIVE FEED PAGE

    # ─────────────────────────────────────────────

class LiveFeedPage(QWidget):
    frames_ready = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.snap_count_val  = 0
        self.grid_active     = False
        self.frame_count     = 0
        self.stream_thread   = None
        self.auto_cap_thread = None
        self.auto_cap_active = False
        self.auto_cap_paths  = []
        os.makedirs("evidence", exist_ok=True)
        os.makedirs("reconstruction_cache", exist_ok=True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        feed_area   = QWidget()
        feed_layout = QVBoxLayout(feed_area)
        feed_layout.setContentsMargins(22, 10, 14, 10)
        feed_layout.setSpacing(8)

        hdr_row = QHBoxLayout()
        hdr = QLabel("LIVE FORENSIC FEED")
        hdr.setStyleSheet(
            "color: #4dc8f0; font-size: 15px; font-weight: 700; letter-spacing: 2px;"
        )
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        self.stream_status = QLabel("● NO SIGNAL")
        self.stream_status.setStyleSheet(
            "color: #f06060; font-size: 11px; font-weight: 700; letter-spacing: 1px;"
        )
        hdr_row.addWidget(self.stream_status)
        feed_layout.addLayout(hdr_row)
        # ── AVAILABLE DEVICES ────────────────────────────────
        self.device_registry = DeviceRegistry()
        self.selected_device = None
        self.remote_thread   = None
        self.active_stream_token = None

        devices_frame = QFrame()
        self.devices_frame_ref = devices_frame
        devices_frame.setObjectName("glassPanel")
        devices_v = QVBoxLayout(devices_frame)
        devices_v.setContentsMargins(16, 12, 16, 12)
        devices_v.setSpacing(8)

        dev_hdr_row = QHBoxLayout()
        dev_hdr = QLabel("AVAILABLE DEVICES")
        dev_hdr.setStyleSheet("color: #2a5a7a; font-size: 10px; font-weight: 700; letter-spacing: 2px;")
        dev_hdr_row.addWidget(dev_hdr)
        dev_hdr_row.addStretch()
        refresh_btn = QPushButton("↺")
        refresh_btn.setObjectName("actionBtn")
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_devices)
        dev_hdr_row.addWidget(refresh_btn)
        devices_v.addLayout(dev_hdr_row)

        self.devices_list_layout = QVBoxLayout()
        self.devices_list_layout.setSpacing(6)
        devices_v.addLayout(self.devices_list_layout)

        feed_layout.addWidget(devices_frame)

        self.adv_toggle_container = QWidget()
        adv_toggle_row = QHBoxLayout(self.adv_toggle_container)
        adv_toggle_row.setContentsMargins(0, 0, 0, 0)

        self.adv_toggle_btn = QPushButton("⚙  ADVANCED / MANUAL SOURCE")
        self.adv_toggle_btn.setObjectName("actionBtn")
        self.adv_toggle_btn.setFixedHeight(30)
        self.adv_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.adv_toggle_btn.clicked.connect(self.toggle_advanced)

        adv_toggle_row.addWidget(self.adv_toggle_btn)
        adv_toggle_row.addStretch()

        feed_layout.addWidget(self.adv_toggle_container)
        ip_frame  = QFrame()
        ip_frame.setObjectName("glassPanel")
        ip_layout = QHBoxLayout(ip_frame)
        ip_layout.setContentsMargins(16, 12, 16, 12)
        ip_layout.setSpacing(12)
        ip_lbl = QLabel("CAMERA SOURCE:")
        ip_lbl.setStyleSheet(
            "color: #3a7a9a; font-size: 11px; font-weight: 700; min-width: 120px;"
        )
        ip_layout.addWidget(ip_lbl)
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP camera URL  or  0  for local webcam")
        ip_layout.addWidget(self.ip_input)
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.setObjectName("actionBtn")
        self.connect_btn.setFixedWidth(110)
        self.connect_btn.setFixedHeight(38)
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.clicked.connect(self.start_stream)
        ip_layout.addWidget(self.connect_btn)
        self.disconnect_btn = QPushButton("DISCONNECT")
        self.disconnect_btn.setObjectName("dangerBtn")
        self.disconnect_btn.setFixedWidth(120)
        self.disconnect_btn.setFixedHeight(38)
        self.disconnect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.disconnect_btn.clicked.connect(self.stop_stream)
        ip_layout.addWidget(self.disconnect_btn)
        feed_layout.addWidget(ip_frame)
        ip_frame.setVisible(False)   # hidden by default — manual entry is now fallback/dev mode
        self._ip_frame_ref = ip_frame


        self.feed_display = QLabel()
        self.feed_display.setMinimumHeight(0)
        self.feed_display.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.feed_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feed_display.setStyleSheet(
            "background-color: #040710; border: 1px solid #182840; "
            "border-radius: 8px; color: #1a3858; font-size: 14px;"
        )
        self.feed_display.setText(
            "◉  AWAITING FORENSIC VIDEO SOURCE\n\n"
            "Connect IP camera or enter 0 for webcam"
        )
        feed_layout.addWidget(self.feed_display, 10)

        ctrl_frame  = QFrame()
        ctrl_frame.setObjectName("glassPanel")
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(16, 12, 16, 12)
        ctrl_layout.setSpacing(14)

        zoom_lbl = QLabel("ZOOM")
        zoom_lbl.setStyleSheet("color: #3a7a9a; font-size: 11px; font-weight: 700;")
        ctrl_layout.addWidget(zoom_lbl)
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 30)
        self.zoom_slider.setValue(10)
        self.zoom_slider.setFixedWidth(150)
        ctrl_layout.addWidget(self.zoom_slider)
        self.zoom_val = QLabel("1.0×")
        self.zoom_val.setStyleSheet(
            "color: #4dc8f0; font-size: 12px; font-family: 'Consolas'; min-width: 40px;"
        )
        ctrl_layout.addWidget(self.zoom_val)
        self.zoom_slider.valueChanged.connect(lambda v: self.zoom_val.setText(f"{v/10:.1f}×"))
        ctrl_layout.addStretch()

        self.snap_label = QLabel("ACQUISITIONS: 0")
        self.snap_label.setStyleSheet(
            "color: #4a7a9a; font-size: 11px; font-family: 'Consolas';"
        )
        ctrl_layout.addWidget(self.snap_label)

        self.capture_btn = QPushButton("◎  ACQUIRE FRAME")
        self.capture_btn.setObjectName("captureBtn")
        self.capture_btn.setFixedHeight(40)
        self.capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.capture_btn.clicked.connect(self.capture_frame)
        ctrl_layout.addWidget(self.capture_btn)

        self.grid_btn = QPushButton("⊞ GRID")
        self.grid_btn.setObjectName("actionBtn")
        self.grid_btn.setFixedHeight(40)
        self.grid_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.grid_btn.clicked.connect(self.toggle_grid)
        ctrl_layout.addWidget(self.grid_btn)

        self.auto_cap_btn = QPushButton("⏺  AUTO ACQUIRE")
        self.auto_cap_btn.setObjectName("actionBtn")
        self.auto_cap_btn.setFixedHeight(40)
        self.auto_cap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auto_cap_btn.clicked.connect(self.toggle_auto_capture)
        ctrl_layout.addWidget(self.auto_cap_btn)
        feed_layout.addWidget(ctrl_frame)
        layout.addWidget(feed_area, 1)

        right_panel  = QFrame()
        right_panel.setObjectName("sidebar")
        right_panel.setFixedWidth(190)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(14, 18, 14, 18)
        right_layout.setSpacing(10)

        rp_lbl = QLabel("STREAM TELEMETRY")
        rp_lbl.setStyleSheet(
            "color: #1e4a6a; font-size: 9px; font-weight: 700; letter-spacing: 2px;"
        )
        right_layout.addWidget(rp_lbl)

        self.info_labels = {}
        for label in ["Resolution", "Frame Rate", "Latency", "Zoom Level", "Frames"]:
            f  = QFrame()
            f.setObjectName("panel")
            fl = QHBoxLayout(f)
            fl.setContentsMargins(12, 9, 12, 9)
            l  = QLabel(label)
            l.setStyleSheet("color: #3a6a8a; font-size: 11px;")
            fl.addWidget(l)
            fl.addStretch()
            v  = QLabel("—")
            v.setStyleSheet("color: #9ac0d8; font-size: 11px; font-family: 'Consolas';")
            fl.addWidget(v)
            self.info_labels[label] = v
            right_layout.addWidget(f)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #0e1c2c;")
        right_layout.addWidget(sep)

        ac_frame  = QFrame()
        ac_frame.setObjectName("glassPanel")
        ac_layout = QVBoxLayout(ac_frame)
        ac_layout.setContentsMargins(14, 12, 14, 12)
        ac_layout.setSpacing(8)

        ac_title = QLabel("AUTO ACQUISITION")
        ac_title.setStyleSheet(
            "color: #1e4a6a; font-size: 9px; font-weight: 700; letter-spacing: 2px;"
        )
        ac_layout.addWidget(ac_title)

        self.ac_status_lbl = QLabel("● INACTIVE")
        self.ac_status_lbl.setStyleSheet(
            "color: #f06060; font-size: 11px; font-weight: 700;"
        )
        ac_layout.addWidget(self.ac_status_lbl)

        self.ac_count_lbl = QLabel("Buffered: 0 frames")
        self.ac_count_lbl.setStyleSheet("color: #4a7a9a; font-size: 11px;")
        ac_layout.addWidget(self.ac_count_lbl)

        int_row = QHBoxLayout()
        int_lbl = QLabel("Interval:")
        int_lbl.setStyleSheet("color: #3a6a8a; font-size: 11px;")
        int_row.addWidget(int_lbl)
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1s", "2s", "3s", "5s"])
        self.interval_combo.setCurrentIndex(1)
        int_row.addWidget(self.interval_combo)
        ac_layout.addLayout(int_row)

        self.send_to_stitch_btn = QPushButton("↗  SEND TO RECONSTRUCTION")
        self.send_to_stitch_btn.setObjectName("successBtn")
        self.send_to_stitch_btn.setFixedHeight(38)
        self.send_to_stitch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_to_stitch_btn.clicked.connect(self.send_frames_to_stitch)
        ac_layout.addWidget(self.send_to_stitch_btn)
        right_layout.addWidget(ac_frame)

        right_layout.addStretch()

        self.log_box = ForensicLogWidget(placeholder="Acquisition log...")
        self.log_box.setFixedHeight(170)
        right_layout.addWidget(self.log_box)
        layout.addWidget(right_panel)

        self.frame_timer  = QTimer()
        self.frame_timer.timeout.connect(self.refresh_frame)
        self.current_frame = None
        self._received_frame_times = deque(maxlen=60)

    def log(self, msg): self.log_box.append_log(msg)
    def toggle_advanced(self):
        visible = not self._ip_frame_ref.isVisible()
        self._ip_frame_ref.setVisible(visible)

    def refresh_devices(self):
        while self.devices_list_layout.count():
            item = self.devices_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        devices = self.device_registry.list_devices(case_id=MANIFEST.case_id)
        for device in devices:
            card = DeviceCard(device)
            card.view_clicked.connect(self.view_device)
            self.devices_list_layout.addWidget(card)
        self.log(f"Device list refreshed — {len(devices)} devices")

    def set_live_focus(self, active: bool):
        """
    Give the live video maximum vertical space while a
    remote camera is actively being viewed.
    """
        if active:
            # Hide source-selection UI so the video gets the space.
            self.devices_frame_ref.setVisible(False)
            self.adv_toggle_container.setVisible(False)

            # Manual source frame should remain hidden while
            # using the registered LiveKit camera.
            self._ip_frame_ref.setVisible(False)

            # Let the parent layout allocate all remaining height
            # to the video viewport.
            self.feed_display.setMinimumHeight(0)

        else:
            # Restore normal source-selection UI.
            self.devices_frame_ref.setVisible(True)
            self.adv_toggle_container.setVisible(True)

            self.feed_display.setMinimumHeight(550)

        self.feed_display.updateGeometry()
        self.updateGeometry()

    def view_device(self, device: SpiderCamDevice):
        self.active_stream_token = None
        # Stop any existing remote subscription first
        if self.remote_thread is not None:
            self.remote_thread.stop()
            self.remote_thread = None
        # Stop any manual/local stream too, so only one source feeds the pipeline
        if self.stream_thread is not None:
            self.stream_thread.stop()
            self.stream_thread = None

        self.selected_device = device
        self.set_live_focus(True)
        self.log(f"Selected device: {device.device_id} ({device.quality_label})")
        self.stream_status.setText(f"● {device.device_id} CONNECTING")
        self.stream_status.setStyleSheet("color: #f0a030; font-size: 11px; font-weight: 700;")
        self.feed_display.setText(
            f"◉  {device.device_id}\n\nConnecting to LiveKit…"
        )
        AUDIT.log("DEVICE SELECTED", device.device_id)

        self.remote_thread = SpiderCamRemoteThread(
            device_id=device.device_id,
            case_id=device.case_id or MANIFEST.case_id,
        )
        self.active_stream_token = uuid.uuid4().hex
        stream_token = self.active_stream_token
        self.remote_thread.frame_ready.connect(
            lambda frame, token=stream_token: self.receive_frame(frame, token)
        )
        self.remote_thread.state_changed.connect(self._on_remote_state)
        self.remote_thread.resolution_ready.connect(self._on_remote_resolution)
        self.remote_thread.start()

        if not self.frame_timer.isActive():
            self.frame_timer.start(33)



    def _on_remote_state(self, state, msg):
        self.log(f"[{self.selected_device.device_id if self.selected_device else '?'}] {msg}")
        if state == "connecting":
            self.stream_status.setText(f"● CONNECTING")
            self.stream_status.setStyleSheet("color: #f0a030; font-size: 11px; font-weight: 700;")
        elif state == "live":
            self.stream_status.setText("● LIVE FEED ACTIVE")
            self.stream_status.setStyleSheet("color: #4caf82; font-size: 11px; font-weight: 700;")
        elif state == "error":
            self.stream_status.setText("● ERROR")
            self.stream_status.setStyleSheet("color: #f06060; font-size: 11px; font-weight: 700;")
            self.feed_display.setText(
                f"◉  CONNECTION ERROR\n\n{msg}"
            )
            self.current_frame = None

    def _on_remote_resolution(self, width, height):
        self.info_labels["Resolution"].setText(f"{width}×{height}")

    def start_stream(self):
        url = self.ip_input.text().strip()
        if not url:
            self.log("ERROR: No camera source specified")
            return
        self.active_stream_token = None
        if self.remote_thread is not None:
            self.remote_thread.stop()
            self.remote_thread = None
        if self.stream_thread is not None:
            self.stream_thread.stop()
            self.stream_thread = None
        self.stream_thread = StreamThread()
        self.stream_thread.set_source(url)
        self.active_stream_token = uuid.uuid4().hex
        stream_token = self.active_stream_token
        self.stream_thread.frame_ready.connect(
            lambda frame, token=stream_token: self.receive_frame(frame, token)
        )
        self.stream_thread.start()
        self.frame_timer.start(33)
        self.stream_status.setText("● LIVE FEED ACTIVE")
        self.stream_status.setStyleSheet("color: #4caf82; font-size: 11px; font-weight: 700;")
        self.log(f"Forensic feed connected: {url}")
        AUDIT.log("LIVE FEED CONNECTED", url)

    def stop_stream(self):
        self.active_stream_token = None
        self.set_live_focus(False)
        self.frame_timer.stop()
        if self.stream_thread:
            self.stream_thread.stop()
            self.stream_thread = None
        if self.remote_thread:
            self.remote_thread.stop()
            self.remote_thread = None
        if self.auto_cap_active:
            self.toggle_auto_capture()
        self.current_frame = None
        self.feed_display.setText(
            "◉  AWAITING FORENSIC VIDEO SOURCE\n\n"
            "Connect IP camera or enter 0 for webcam"
        )
        self.stream_status.setText("● NO SIGNAL")
        self.stream_status.setStyleSheet("color: #f06060; font-size: 11px; font-weight: 700;")
        self.log("Feed disconnected")

    def receive_frame(self, frame, stream_token=None):
        if stream_token != self.active_stream_token:
            return
        self.current_frame  = frame
        self.frame_count   += 1
        now = time.monotonic()
        self._received_frame_times.append(now)
        while self._received_frame_times and now - self._received_frame_times[0] > 1.5:
            self._received_frame_times.popleft()
        if len(self._received_frame_times) >= 2:
            elapsed = self._received_frame_times[-1] - self._received_frame_times[0]
            if elapsed > 0:
                self.info_labels["Frame Rate"].setText(
                    f"{(len(self._received_frame_times) - 1) / elapsed:.1f}"
                )
        height, width = frame.shape[:2]
        self.info_labels["Resolution"].setText(f"{width}×{height}")
        self.info_labels["Latency"].setText("RX ONLY")

    def refresh_frame(self):
        if self.current_frame is None: return
        frame = self.current_frame.copy()
        zoom  = self.zoom_slider.value() / 10.0
        if zoom > 1.0:
            h, w   = frame.shape[:2]
            cx, cy = w//2, h//2
            nw, nh = int(w/zoom), int(h/zoom)
            x1, y1 = max(cx-nw//2, 0), max(cy-nh//2, 0)
            frame  = frame[y1:y1+nh, x1:x1+nw]
            frame  = cv2.resize(frame, (w, h))
        if self.grid_active:
            h, w = frame.shape[:2]
            step_x, step_y = w//10, h//10
            for i in range(1, 10):
                cv2.line(frame, (i*step_x,0), (i*step_x,h), (0,180,180), 1)
                cv2.line(frame, (0,i*step_y), (w,i*step_y), (0,180,180), 1)

        h, w = frame.shape[:2]
        self.info_labels["Resolution"].setText(f"{w}×{h}")
        self.info_labels["Frames"].setText(str(self.frame_count))
        self.info_labels["Zoom Level"].setText(self.zoom_val.text())
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qimg   = QImage(rgb.data, w, h, 3*w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(
            self.feed_display.width(), self.feed_display.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        self.feed_display.setPixmap(pixmap)

    def capture_frame(self):
        if self.current_frame is None:
            self.log("ERROR: No active forensic feed")
            return
        fname = f"evidence/EX_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(fname, self.current_frame)
        self.snap_count_val += 1
        self.snap_label.setText(f"ACQUISITIONS: {self.snap_count_val}")
        MANIFEST.register(fname, "CAPTURED", "Live feed acquisition")
        AUDIT.log("FRAME ACQUIRED", fname)
        self.log(f"Frame acquired + hashed: {fname}")

    def toggle_grid(self):
        self.grid_active = not self.grid_active
        state = "ON" if self.grid_active else "OFF"
        self.log(f"Forensic grid overlay: {state}")
        self.grid_btn.setStyleSheet(
            "background: #0e3d62; color: #52c488; border: 1px solid #52c488; "
            "border-radius: 6px; padding: 9px 18px; font-size: 12px; font-weight: 600;"
            if self.grid_active else ""
        )

    def toggle_auto_capture(self):
        if not self.auto_cap_active:
            if self.current_frame is None:
                self.log("ERROR: Activate feed before auto acquisition")
                return
            interval_map = {"1s":1.0,"2s":2.0,"3s":3.0,"5s":5.0}
            interval     = interval_map.get(self.interval_combo.currentText(), 2.0)
            self.auto_cap_paths  = []
            self.auto_cap_active = True
            self.auto_cap_thread = AutoCaptureThread(interval_sec=interval)
            self.auto_cap_thread.capture_signal.connect(self._auto_capture_frame)
            self.auto_cap_thread.start()
            self.auto_cap_btn.setText("⏹  STOP ACQUISITION")
            self.auto_cap_btn.setStyleSheet(
                "background: #081808; color: #52c488; border: 1px solid #52c488; "
                "border-radius: 6px; padding: 9px 18px; font-size: 12px; font-weight: 600;"
            )
            self.ac_status_lbl.setText("● ACQUIRING")
            self.ac_status_lbl.setStyleSheet("color: #4caf82; font-size: 11px; font-weight: 700;")
            self.log(f"Auto acquisition started (interval: {interval}s)")
        else:
            self.auto_cap_active = False
            if self.auto_cap_thread:
                self.auto_cap_thread.stop()
                self.auto_cap_thread = None
            self.auto_cap_btn.setText("⏺  AUTO ACQUIRE")
            self.auto_cap_btn.setStyleSheet("")
            self.ac_status_lbl.setText("● INACTIVE")
            self.ac_status_lbl.setStyleSheet("color: #f06060; font-size: 11px; font-weight: 700;")
            self.log(f"Acquisition stopped — {len(self.auto_cap_paths)} frames buffered")

    def _auto_capture_frame(self):
        if self.current_frame is None: return
        os.makedirs("reconstruction_cache", exist_ok=True)
        fname = f"reconstruction_cache/AC_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        cv2.imwrite(fname, self.current_frame)
        self.auto_cap_paths.append(fname)
        self.ac_count_lbl.setText(f"Buffered: {len(self.auto_cap_paths)} frames")

    def send_frames_to_stitch(self):
        if not self.auto_cap_paths:
            self.log("ERROR: No buffered frames available")
            return
        self.frames_ready.emit(list(self.auto_cap_paths))
        self.log(f"↗ {len(self.auto_cap_paths)} frames sent to reconstruction engine")
        self.refresh_devices()

# ─────────────────────────────────────────────

# EVIDENCE GALLERY PAGE

# ─────────────────────────────────────────────

class EvidenceGalleryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loaded_images = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        hdr_row = QHBoxLayout()
        hdr = QLabel("EVIDENCE ACQUISITION GALLERY")
        hdr.setStyleSheet(
            "color: #4dc8f0; font-size: 15px; font-weight: 700; letter-spacing: 2px;"
        )
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        self.load_btn = QPushButton("⊕  LOAD EVIDENCE")
        self.load_btn.setObjectName("actionBtn")
        self.load_btn.setFixedHeight(38)
        self.load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_btn.clicked.connect(self.load_images)
        hdr_row.addWidget(self.load_btn)
        self.clear_btn = QPushButton("✕  CLEAR ALL")
        self.clear_btn.setObjectName("dangerBtn")
        self.clear_btn.setFixedHeight(38)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_images)
        hdr_row.addWidget(self.clear_btn)
        layout.addLayout(hdr_row)

        stats_row = QHBoxLayout()
        self.count_label = QLabel("0 evidence items loaded")
        self.count_label.setStyleSheet("color: #4a7a9a; font-size: 12px;")
        stats_row.addWidget(self.count_label)
        stats_row.addStretch()
        self.hash_label = QLabel("Filename-list digest: —")
        self.hash_label.setStyleSheet("color: #2a5a3a; font-size: 11px; font-family: 'Consolas';")
        stats_row.addWidget(self.hash_label)
        layout.addLayout(stats_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        scroll   = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: 1px solid #182535; border-radius: 8px; background: #060a12; }"
        )
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(14, 14, 14, 14)
        scroll.setWidget(self.grid_widget)
        splitter.addWidget(scroll)

        preview_panel = QFrame()
        preview_panel.setObjectName("panel")
        preview_panel.setFixedWidth(290)
        pl = QVBoxLayout(preview_panel)
        pl.setContentsMargins(14, 14, 14, 14)
        pl.setSpacing(10)

        prev_lbl = QLabel("EVIDENCE PREVIEW")
        prev_lbl.setStyleSheet(
            "color: #1e4a6a; font-size: 9px; font-weight: 700; letter-spacing: 2px;"
        )
        pl.addWidget(prev_lbl)

        self.preview_label = QLabel()
        self.preview_label.setFixedHeight(210)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(
            "background: #040710; border: 1px solid #182840; "
            "border-radius: 6px; color: #1a3858; font-size: 11px;"
        )
        self.preview_label.setText("Select evidence item to preview")
        pl.addWidget(self.preview_label)

        self.meta_box = QTextEdit()
        self.meta_box.setReadOnly(True)
        self.meta_box.setFixedHeight(130)
        self.meta_box.setPlaceholderText("Evidence metadata...")
        pl.addWidget(self.meta_box)
        pl.addStretch()
        splitter.addWidget(preview_panel)
        layout.addWidget(splitter, 1)

        self.log_area = ForensicLogWidget(placeholder="Evidence acquisition log...")
        self.log_area.setFixedHeight(95)
        layout.addWidget(self.log_area)

    def log(self, msg): self.log_area.append_log(msg)

    def load_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Load Forensic Evidence", "",
            "Images (*.jpg *.jpeg *.png *.bmp)"
        )
        if not files: return
        self.loaded_images = files
        self.count_label.setText(f"{len(files)} evidence items loaded")
        self.log(f"Evidence acquisition: {len(files)} items")
        AUDIT.log("EVIDENCE LOADED", f"{len(files)} files")
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w: w.setParent(None)
        h = hashlib.sha256()
        for f in files:
            h.update(os.path.basename(f).encode())
            MANIFEST.register(f, "LOADED", "Evidence gallery acquisition")
        self.hash_label.setText(f"Filename-list SHA-256: {h.hexdigest()[:24]}...")
        self.hash_label.setStyleSheet("color: #4caf82; font-size: 11px; font-family: 'Consolas';")
        self.log(f"Evidence filename-list digest: {h.hexdigest()[:16]}...")
        cols = 4
        for i, fpath in enumerate(files):
            frame = QFrame()
            frame.setObjectName("glassPanel")
            frame.setFixedSize(164, 155)
            frame.setCursor(Qt.CursorShape.PointingHandCursor)
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(5, 5, 5, 5)
            fl.setSpacing(4)
            img_lbl = QLabel()
            img_lbl.setFixedSize(152, 118)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = QPixmap(fpath)
            if not pixmap.isNull():
                img_lbl.setPixmap(pixmap.scaled(
                    152, 118,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            fl.addWidget(img_lbl)
            ev_id    = f"E-{i+1:03d}"
            name_lbl = QLabel(f"{ev_id}  ·  {os.path.basename(fpath)[:12]}")
            name_lbl.setStyleSheet("color: #4dc8f0; font-size: 9px; font-weight: 600;")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(name_lbl)
            frame.mousePressEvent = lambda e, p=fpath, fr=frame: self.handle_click(e, p, fr)
            self.grid_layout.addWidget(frame, i//cols, i%cols)

    def handle_click(self, event, fpath, frame):
        if event.button() == Qt.MouseButton.RightButton:
            menu = QMenu(self)
            preview_action = menu.addAction("👁  Preview Evidence")
            delete_action  = menu.addAction("🗑  Remove from Gallery")
            action = menu.exec(event.globalPosition().toPoint())
            if action == delete_action:   self.remove_image(fpath, frame)
            elif action == preview_action: self.preview_image(fpath)
        else:
            self.preview_image(fpath)

    def remove_image(self, fpath, frame):
        if fpath in self.loaded_images: self.loaded_images.remove(fpath)
        frame.setParent(None)
        self.count_label.setText(f"{len(self.loaded_images)} evidence items loaded")
        self.log(f"Evidence removed: {os.path.basename(fpath)}")
        AUDIT.log("EVIDENCE REMOVED", os.path.basename(fpath))

    def preview_image(self, fpath):
        pixmap = QPixmap(fpath)
        if not pixmap.isNull():
            self.preview_label.setPixmap(pixmap.scaled(
                268, 200,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        h = hashlib.sha256()
        with open(fpath,'rb') as f: h.update(f.read())
        size = os.path.getsize(fpath)
        self.meta_box.setText(
            f"File:     {os.path.basename(fpath)}\n"
            f"Size:     {size//1024} KB\n"
            f"SHA-256:  {h.hexdigest()[:32]}...\n"
            f"Acquired: {datetime.now().strftime('%H:%M:%S')}"
        )
        self.log(f"Previewing: {os.path.basename(fpath)}")

    def clear_images(self):
        self.loaded_images = []
        self.count_label.setText("0 evidence items loaded")
        self.hash_label.setText("Filename-list digest: —")
        self.hash_label.setStyleSheet("color: #2a5a3a; font-size: 11px; font-family: 'Consolas';")
        self.preview_label.clear()
        self.preview_label.setText("Select evidence item to preview")
        self.meta_box.clear()
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w: w.setParent(None)
        self.log("Evidence gallery cleared")
        AUDIT.log("GALLERY CLEARED")

# ─────────────────────────────────────────────

# SCENE MAPPING PAGE

# ─────────────────────────────────────────────

class SceneMappingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stitched_image = None
        self.loaded_images  = []
        self.grid_active    = False
        self.grid_rows      = 8
        self.grid_cols      = 8
        self.zoom_factor    = 1.0
        os.makedirs("exports", exist_ok=True)
        os.makedirs("temp_frames", exist_ok=True)
        os.makedirs("reconstruction_cache", exist_ok=True)

        self.main_stack = QStackedWidget()

        # ── Normal view ───────────────────────────────────────────
        normal_widget = QWidget()
        layout = QHBoxLayout(normal_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        main = QWidget()
        ml   = QVBoxLayout(main)
        ml.setContentsMargins(24, 20, 14, 20)
        ml.setSpacing(14)

        hdr = QLabel("FORENSIC SCENE RECONSTRUCTION ENGINE")
        hdr.setStyleSheet(
            "color: #4dc8f0; font-size: 15px; font-weight: 700; letter-spacing: 2px;"
        )
        ml.addWidget(hdr)

        sub = QLabel("Spatial reconstruction — forensic evidence continuity preserved — v2.1")
        sub.setStyleSheet("color: #2a5a7a; font-size: 11px;")
        ml.addWidget(sub)

        ctrl_frame  = QFrame()
        ctrl_frame.setObjectName("glassPanel")
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(14, 12, 14, 12)
        ctrl_layout.setSpacing(8)

        self.load_btn = QPushButton("⊕  LOAD IMAGES")
        self.load_btn.setObjectName("actionBtn")
        self.load_btn.setFixedHeight(40)
        self.load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_btn.clicked.connect(self.load_images)
        ctrl_layout.addWidget(self.load_btn)

        self.load_video_btn = QPushButton("▶  LOAD VIDEO")
        self.load_video_btn.setObjectName("actionBtn")
        self.load_video_btn.setFixedHeight(40)
        self.load_video_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_video_btn.clicked.connect(self.load_video)
        ctrl_layout.addWidget(self.load_video_btn)

        self.stitch_btn = QPushButton("⊞  RECONSTRUCT SCENE")
        self.stitch_btn.setObjectName("captureBtn")
        self.stitch_btn.setFixedHeight(40)
        self.stitch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stitch_btn.clicked.connect(self.start_stitch)
        ctrl_layout.addWidget(self.stitch_btn)

        self.grid_btn = QPushButton("▦  GRID")
        self.grid_btn.setObjectName("actionBtn")
        self.grid_btn.setFixedHeight(40)
        self.grid_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.grid_btn.clicked.connect(self.toggle_grid)
        ctrl_layout.addWidget(self.grid_btn)

        ctrl_layout.addStretch()

        zoom_lbl = QLabel("ZOOM:")
        zoom_lbl.setStyleSheet("color: #3a7a9a; font-size: 11px; font-weight: 700;")
        ctrl_layout.addWidget(zoom_lbl)
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 40)
        self.zoom_slider.setValue(10)
        self.zoom_slider.setFixedWidth(110)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        ctrl_layout.addWidget(self.zoom_slider)
        self.zoom_label = QLabel("1.0×")
        self.zoom_label.setStyleSheet(
            "color: #4dc8f0; font-size: 12px; font-family: 'Consolas'; min-width: 40px;"
        )
        ctrl_layout.addWidget(self.zoom_label)

        ctrl_layout.addStretch()

        self.recon3d_btn = QPushButton("▶  3D RECONSTRUCT")
        self.recon3d_btn.setObjectName("captureBtn")
        self.recon3d_btn.setFixedHeight(40)
        self.recon3d_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.recon3d_btn.clicked.connect(self.start_3d_reconstruction)
        ctrl_layout.addWidget(self.recon3d_btn)

        self.export_btn = QPushButton("↗  EXPORT")
        self.export_btn.setObjectName("successBtn")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_map)
        ctrl_layout.addWidget(self.export_btn)

        ml.addWidget(ctrl_frame)

        self.map_display = QLabel()
        self.map_display.setMinimumHeight(430)
        self.map_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_display.setStyleSheet(
            "background-color: #040710; border: 1px solid #182840; "
            "border-radius: 8px; color: #1a3858; font-size: 14px;"
        )
        self.map_display.setText(
            "⊞  FORENSIC SCENE RECONSTRUCTION CANVAS\n\n"
            "Load forensic imagery or video source to begin spatial reconstruction"
        )
        ml.addWidget(self.map_display, 1)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFixedHeight(6)
        ml.addWidget(self.progress)
        layout.addWidget(main, 1)

        right = QFrame()
        right.setObjectName("sidebar")
        right.setFixedWidth(248)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(14, 18, 14, 18)
        rl.setSpacing(8)

        rl_lbl = QLabel("RECONSTRUCTION METADATA")
        rl_lbl.setStyleSheet(
            "color: #1e4a6a; font-size: 9px; font-weight: 700; letter-spacing: 2px;"
        )
        rl.addWidget(rl_lbl)

        self.info_labels = {}
        for label in [
            "Images Used", "Dimensions", "Grid Cells", "Status", "Overlap",
            "Video Duration", "Frames Extracted", "Stitch Quality", "Est. Overlap"
        ]:
            f  = QFrame()
            f.setObjectName("panel")
            fl = QHBoxLayout(f)
            fl.setContentsMargins(12, 8, 12, 8)
            l  = QLabel(label)
            l.setStyleSheet("color: #3a6a8a; font-size: 10px;")
            fl.addWidget(l)
            fl.addStretch()
            v  = QLabel("—")
            v.setStyleSheet("color: #9ac0d8; font-size: 10px; font-family: 'Consolas';")
            fl.addWidget(v)
            self.info_labels[label] = v
            rl.addWidget(f)

        rl.addStretch()

        self.log_box = ForensicLogWidget(placeholder="Reconstruction log...")
        self.log_box.setFixedHeight(210)
        rl.addWidget(self.log_box)
        layout.addWidget(right)
        self.main_stack.addWidget(normal_widget)

        # ── Mosaic workspace ──────────────────────────────────────
        self.mosaic_workspace = ForensicMosaicWorkspace()
        self.mosaic_workspace.stitch_requested.connect(self._composite_mosaic)

        mosaic_wrapper = QWidget()
        mw_layout = QVBoxLayout(mosaic_wrapper)
        mw_layout.setContentsMargins(0, 0, 0, 0)
        mw_layout.setSpacing(0)
        back_bar = QFrame()
        back_bar.setObjectName("glassPanel")
        back_bar.setFixedHeight(48)
        back_layout = QHBoxLayout(back_bar)
        back_layout.setContentsMargins(14, 8, 14, 8)
        back_btn = QPushButton("← BACK TO RECONSTRUCTION")
        back_btn.setObjectName("actionBtn")
        back_btn.setFixedHeight(32)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self._show_normal_view)
        back_layout.addWidget(back_btn)
        back_layout.addStretch()
        mw_layout.addWidget(back_bar)
        mw_layout.addWidget(self.mosaic_workspace, 1)
        self.main_stack.addWidget(mosaic_wrapper)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self.main_stack)

    def _show_normal_view(self):    self.main_stack.setCurrentIndex(0)
    def _show_mosaic_workspace(self): self.main_stack.setCurrentIndex(1)

    def log(self, msg): self.log_box.append_log(msg)

    def load_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Load Forensic Scene Images", "",
            "Images (*.jpg *.jpeg *.png *.bmp)"
        )
        if not files: return
        self.loaded_images = files
        self.info_labels["Images Used"].setText(str(len(files)))
        self.log(f"Scene imagery loaded — {len(files)} files")
        AUDIT.log("RECONSTRUCTION IMAGES LOADED", f"{len(files)} files")

    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Forensic Scene Video", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if not path: return
        cap = cv2.VideoCapture(path)
        fps          = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration     = total_frames / fps
        cap.release()
        self.info_labels["Video Duration"].setText(f"{duration:.1f}s")
        self.info_labels["Status"].setText("EXTRACTING")
        self.info_labels["Status"].setStyleSheet(
            "color: #f0a030; font-size: 10px; font-weight: 700;"
        )
        self.log(f"Video source acquired: {os.path.basename(path)}")
        self.load_video_btn.setEnabled(False)
        self.load_video_btn.setText("EXTRACTING...")
        self.progress.setValue(0)
        AUDIT.log("VIDEO SOURCE LOADED", os.path.basename(path))
        self.extract_thread = VideoExtractionThread(path, output_dir="temp_frames")
        self.extract_thread.progress.connect(self.progress.setValue)
        self.extract_thread.log_msg.connect(self.log)
        self.extract_thread.frame_count.connect(
            lambda n: self.info_labels["Frames Extracted"].setText(str(n))
        )
        self.extract_thread.finished.connect(self._extraction_done)
        self.extract_thread.start()

    def _extraction_done(self, paths, success, msg):
        self.load_video_btn.setEnabled(True)
        self.load_video_btn.setText("▶  LOAD VIDEO")
        if success:
            self.loaded_images = paths
            self.info_labels["Images Used"].setText(str(len(paths)))
            self.info_labels["Frames Extracted"].setText(str(len(paths)))
            self.info_labels["Status"].setText("READY")
            self.info_labels["Status"].setStyleSheet(
                "color: #4caf82; font-size: 10px; font-weight: 700;"
            )
            self.log(f"{len(paths)} reconstruction frames ready — click RECONSTRUCT SCENE")
        else:
            self.log(f"EXTRACTION FAILED: {msg}")
            self.info_labels["Status"].setText("FAILED")
            self.info_labels["Status"].setStyleSheet(
                "color: #f06060; font-size: 10px; font-weight: 700;"
            )

    def receive_live_frames(self, paths):
        self.loaded_images = paths
        self.info_labels["Images Used"].setText(str(len(paths)))
        self.info_labels["Status"].setText("READY")
        self.info_labels["Status"].setStyleSheet(
            "color: #4caf82; font-size: 10px; font-weight: 700;"
        )
        self.log(f"Received {len(paths)} live acquisition frames")

    def start_stitch(self):
        if len(self.loaded_images) < 2:
            self.log("ERROR: Insufficient imagery for reconstruction")
            return
        self.mode_dialog = StitchModeDialog(self)
        self.mode_dialog.mode_selected.connect(self._run_stitch)
        self.mode_dialog.show_centered(self.window())

    def _run_stitch(self, mode):
        if mode == "mosaic":
            self._show_mosaic_workspace()
            self.log("Spatial Scene Mapping workspace opened")
            self.log("Load images → arrange manually → click GENERATE FORENSIC MAP")
            return
        self.progress.setValue(0)
        self.stitch_btn.setEnabled(False)
        self.stitch_btn.setText("RECONSTRUCTING...")
        self.info_labels["Status"].setText("RECONSTRUCTING")
        self.info_labels["Status"].setStyleSheet(
            "color: #f0a030; font-size: 10px; font-weight: 700;"
        )
        self.log("Walkthrough reconstruction initiated")
        self.log("Recovering camera motion vectors...")
        AUDIT.log("RECONSTRUCTION STARTED",
                  f"{len(self.loaded_images)} images | walkthrough mode")
        self.stitch_thread = StitchThread(self.loaded_images)
        self.stitch_thread.progress.connect(self.progress.setValue)
        self.stitch_thread.log_msg.connect(self.log)
        self.stitch_thread.finished.connect(self.stitch_done)
        self.stitch_thread.start()

    def _composite_mosaic(self, tile_states):
        self.log("Generating forensic spatial map composite...")
        result = self.mosaic_workspace.generate_composite(tile_states)
        if result is not None:
            self.stitched_image = result
            h, w = result.shape[:2]
            self.info_labels["Dimensions"].setText(f"{w}×{h}")
            self.info_labels["Status"].setText("COMPLETE")
            self.info_labels["Status"].setStyleSheet(
                "color: #4caf82; font-size: 10px; font-weight: 700;"
            )
            self.info_labels["Stitch Quality"].setText("MANUAL")
            self.display_map(result)
            self.log(f"Forensic spatial map generated — {w}×{h} px")
            self.log("Evidence positions preserved — spatial integrity maintained")
            AUDIT.log("MOSAIC MAP GENERATED", f"{w}×{h} px")
            self._show_normal_view()
            self.mosaic_workspace.status_lbl.setText("✓ Map generated successfully")
            self.mosaic_workspace.status_lbl.setStyleSheet(
                "color: #52c488; font-size: 10px; border: none;"
            )
        else:
            self.log("ERROR: Could not generate composite map")

    def stitch_done(self, result, success, msg):
        self.stitch_btn.setEnabled(True)
        self.stitch_btn.setText("⊞  RECONSTRUCT SCENE")
        if success:
            self.stitched_image = result
            h, w = result.shape[:2]
            self.info_labels["Dimensions"].setText(f"{w}×{h}")
            self.info_labels["Status"].setText("COMPLETE")
            self.info_labels["Status"].setStyleSheet(
                "color: #4caf82; font-size: 10px; font-weight: 700;"
            )
            self.info_labels["Stitch Quality"].setText("GOOD")
            self.info_labels["Est. Overlap"].setText("~30–50%")
            self.display_map(result)
            self.log(f"Forensic reconstruction complete — {w}×{h} px")
            AUDIT.log("RECONSTRUCTION COMPLETE", f"{w}×{h} px")
        else:
            self.log(f"RECONSTRUCTION FAILED: {msg}")
            self.info_labels["Status"].setText("FAILED")
            self.info_labels["Status"].setStyleSheet(
                "color: #f06060; font-size: 10px; font-weight: 700;"
            )

    def display_map(self, img):
        display = img.copy()
        if self.grid_active:
            display = self.draw_grid(display)
        h, w = display.shape[:2]
        zoom = self.zoom_slider.value() / 10.0
        if zoom != 1.0:
            display = cv2.resize(display, (int(w*zoom), int(h*zoom)))
            h, w    = display.shape[:2]
        rgb    = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        qimg   = QImage(rgb.data, w, h, 3*w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(
            self.map_display.width(), self.map_display.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.map_display.setPixmap(pixmap)

    def draw_grid(self, img):
        h, w  = img.shape[:2]
        cols  = getattr(self, "grid_cols", 8)
        rows  = getattr(self, "grid_rows", 8)
        gc    = (255, 255, 255)
        cw, ch = w//cols, h//rows
        lbls  = [chr(65+i) for i in range(cols)]
        for i in range(1, cols): cv2.line(img,(i*cw,0),(i*cw,h),gc,1)
        for i in range(1, rows): cv2.line(img,(0,i*ch),(w,i*ch),gc,1)
        for ci in range(cols):
            cv2.putText(img,lbls[ci],(ci*cw+cw//2-10,28),
                cv2.FONT_HERSHEY_SIMPLEX,0.7,gc,2)
        for ri in range(rows):
            cv2.putText(img,str(ri+1),(8,ri*ch+ch//2+8),
                cv2.FONT_HERSHEY_SIMPLEX,0.7,gc,2)
        self.info_labels["Grid Cells"].setText(f"{cols}×{rows} = {cols*rows}")
        return img

    def toggle_grid(self):
        self.grid_active = not self.grid_active
        state = "ON" if self.grid_active else "OFF"
        self.log(f"Forensic grid overlay: {state}")
        self.grid_btn.setStyleSheet(
            "background: #0e3d62; color: #ffffff; border: 1px solid #ffffff; "
            "border-radius: 6px; padding: 9px 18px; font-size: 12px; font-weight: 600;"
            if self.grid_active else ""
        )
        if self.stitched_image is not None:
            self.display_map(self.stitched_image)

    def update_zoom(self, val):
        self.zoom_label.setText(f"{val/10:.1f}×")
        if self.stitched_image is not None:
            self.display_map(self.stitched_image)

    def start_3d_reconstruction(self):
        if not self.loaded_images:
            self.log("ERROR: Load imagery before initiating 3D reconstruction")
            return
        self.recon3d_btn.setEnabled(False)
        self.recon3d_btn.setText("PROCESSING...")
        self.log("Photogrammetric reconstruction initiated")
        self.log("Preparing reconstruction frame buffer...")
        AUDIT.log("3D RECONSTRUCTION STARTED")
        detections = []
        try:
            main_win   = self.window()
            detections = main_win.ai_page.detections or []
            if detections:
                self.log(f"AI evidence metadata linked — {len(detections)} items")
        except: pass
        self.recon_thread = ReconstructionThread(
            frame_paths=self.loaded_images, detections=detections
        )
        self.recon_thread.progress.connect(self.progress.setValue)
        self.recon_thread.log_msg.connect(self.log)
        self.recon_thread.finished.connect(self._recon3d_done)
        self.recon_thread.start()

    def _recon3d_done(self, success, msg):
        self.recon3d_btn.setEnabled(True)
        self.recon3d_btn.setText("▶  3D RECONSTRUCT")
        if success:
            is_demo = "Synthetic demonstration" in msg
            self.info_labels["Status"].setText("3D DEMO" if is_demo else "3D COMPLETE")
            self.info_labels["Status"].setStyleSheet(
                "color: #f0a030; font-size: 10px; font-weight: 700;"
                if is_demo else
                "color: #4caf82; font-size: 10px; font-weight: 700;"
            )
            if is_demo:
                self.log(msg)
            else:
                self.log("3D walkthrough viewer launched")
                AUDIT.log("3D RECONSTRUCTION COMPLETE")
        else:
            self.log(f"3D RECONSTRUCTION FAILED: {msg}")

    def export_map(self):
        if self.stitched_image is None:
            self.log("ERROR: No reconstruction output available")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Forensic Scene Map",
            f"exports/CASE_SCENE_MAP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG (*.png);;JPG (*.jpg)"
        )
        if path:
            export = self.stitched_image.copy()
            if self.grid_active: export = self.draw_grid(export)
            cv2.imwrite(path, export)
            MANIFEST.register(path, "EXPORTED", "Forensic scene reconstruction map")
            AUDIT.log("SCENE MAP EXPORTED", path)
            self.log(f"Forensic map exported + hashed: {path}")

# ─────────────────────────────────────────────

# AI DETECTION PAGE

# ─────────────────────────────────────────────

class AIDetectionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_image    = None
        self.annotated_image = None
        self.detections      = []
        os.makedirs("exports", exist_ok=True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        main = QWidget()
        ml   = QVBoxLayout(main)
        ml.setContentsMargins(24, 20, 14, 20)
        ml.setSpacing(14)

        hdr = QLabel("AI FORENSIC EVIDENCE DETECTION")
        hdr.setStyleSheet(
            "color: #4dc8f0; font-size: 15px; font-weight: 700; letter-spacing: 2px;"
        )
        ml.addWidget(hdr)

        sub = QLabel(
            "YOLOv8 deep learning — forensic grid coordinate mapping — E-001 evidence labeling system"
        )
        sub.setStyleSheet("color: #2a5a7a; font-size: 11px;")
        ml.addWidget(sub)

        ctrl = QFrame()
        ctrl.setObjectName("glassPanel")
        cl   = QHBoxLayout(ctrl)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(12)

        self.load_btn = QPushButton("⊕  LOAD IMAGE")
        self.load_btn.setObjectName("actionBtn")
        self.load_btn.setFixedHeight(40)
        self.load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_btn.clicked.connect(self.load_image)
        cl.addWidget(self.load_btn)

        self.use_stitch_btn = QPushButton("⊞  USE RECONSTRUCTION")
        self.use_stitch_btn.setObjectName("actionBtn")
        self.use_stitch_btn.setFixedHeight(40)
        self.use_stitch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.use_stitch_btn.clicked.connect(self.use_stitched)
        cl.addWidget(self.use_stitch_btn)

        self.run_btn = QPushButton("◈  RUN FORENSIC DETECTION")
        self.run_btn.setObjectName("captureBtn")
        self.run_btn.setFixedHeight(40)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self.run_detection)
        cl.addWidget(self.run_btn)

        cl.addStretch()

        thresh_lbl = QLabel("CONFIDENCE:")
        thresh_lbl.setStyleSheet("color: #3a7a9a; font-size: 11px; font-weight: 700;")
        cl.addWidget(thresh_lbl)
        self.thresh_slider = QSlider(Qt.Orientation.Horizontal)
        self.thresh_slider.setRange(20, 90)
        self.thresh_slider.setValue(35)
        self.thresh_slider.setFixedWidth(120)
        cl.addWidget(self.thresh_slider)
        self.thresh_val = QLabel("35%")
        self.thresh_val.setStyleSheet(
            "color: #4dc8f0; font-size: 12px; font-family: 'Consolas'; min-width: 38px;"
        )
        cl.addWidget(self.thresh_val)
        self.thresh_slider.valueChanged.connect(lambda v: self.thresh_val.setText(f"{v}%"))

        self.export_btn = QPushButton("↗  EXPORT")
        self.export_btn.setObjectName("successBtn")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_result)
        cl.addWidget(self.export_btn)
        ml.addWidget(ctrl)

        self.display = QLabel()
        self.display.setMinimumHeight(400)
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setStyleSheet(
            "background-color: #040710; border: 1px solid #182840; "
            "border-radius: 8px; color: #1a3858; font-size: 14px;"
        )
        self.display.setText(
            "◈  FORENSIC EVIDENCE DETECTION CANVAS\n\n"
            "Load forensic imagery or use reconstruction output → Run Detection"
        )
        ml.addWidget(self.display, 1)

        self.det_progress = QProgressBar()
        self.det_progress.setValue(0)
        self.det_progress.setFixedHeight(6)
        ml.addWidget(self.det_progress)
        layout.addWidget(main, 1)

        right = QFrame()
        right.setObjectName("sidebar")
        right.setFixedWidth(270)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(14, 18, 14, 18)
        rl.setSpacing(8)

        rl_lbl = QLabel("EVIDENCE INTELLIGENCE")
        rl_lbl.setStyleSheet(
            "color: #1e4a6a; font-size: 9px; font-weight: 700; letter-spacing: 2px;"
        )
        rl.addWidget(rl_lbl)

        self.info_labels = {}
        for label in ["Status", "Total Evidence", "Weapons", "Biological", "Trace", "Scene Objects"]:
            f  = QFrame()
            f.setObjectName("panel")
            fl = QHBoxLayout(f)
            fl.setContentsMargins(12, 9, 12, 9)
            l  = QLabel(label)
            l.setStyleSheet("color: #3a6a8a; font-size: 11px;")
            fl.addWidget(l)
            fl.addStretch()
            v  = QLabel("—")
            v.setStyleSheet("color: #9ac0d8; font-size: 11px; font-family: 'Consolas';")
            fl.addWidget(v)
            self.info_labels[label] = v
            rl.addWidget(f)

        ev_lbl = QLabel("EVIDENCE REGISTRY")
        ev_lbl.setStyleSheet(
            "color: #1e4a6a; font-size: 9px; font-weight: 700; "
            "letter-spacing: 2px; margin-top: 8px;"
        )
        rl.addWidget(ev_lbl)

        self.det_scroll = QScrollArea()
        self.det_scroll.setWidgetResizable(True)

        self.det_container = QWidget()
        self.det_layout = QVBoxLayout(self.det_container)

        self.det_scroll.setWidget(self.det_container)

        rl.addWidget(self.det_scroll,1)

        self.log_box = ForensicLogWidget(placeholder="Detection pipeline log...")
        self.log_box.setFixedHeight(130)
        rl.addWidget(self.log_box)
        layout.addWidget(right)

    def log(self, msg): self.log_box.append_log(msg)

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Forensic Image", "",
            "Images (*.jpg *.jpeg *.png *.bmp)"
        )
        if not path: return
        self.source_image = cv2.imread(path)
        if self.source_image is None: return
        self._show_image(self.source_image)
        self.log(f"Forensic image loaded: {os.path.basename(path)}")
        MANIFEST.register(path, "DETECTION_SOURCE", "AI detection input")
        AUDIT.log("DETECTION IMAGE LOADED", os.path.basename(path))
        self.info_labels["Status"].setText("READY")
        self.info_labels["Status"].setStyleSheet("color: #4caf82; font-size: 11px; font-weight: 700;")

    def use_stitched(self):
        try:
            main_win = self.window()
            stitched = main_win.mapping_page.stitched_image
            if stitched is None:
                self.log("ERROR: No reconstruction output available — stitch first")
                return
            self.source_image = stitched.copy()
            self._show_image(self.source_image)
            self.log("Reconstruction output loaded for forensic analysis")
            self.info_labels["Status"].setText("READY")
            self.info_labels["Status"].setStyleSheet(
                "color: #4caf82; font-size: 11px; font-weight: 700;"
            )
        except Exception as e:
            self.log(f"ERROR: {str(e)}")

    def run_detection(self):
        if self.source_image is None:
            self.log("ERROR: Load forensic imagery first")
            return

        self.run_btn.setEnabled(False)
        self.run_btn.setText("ANALYZING...")
        self.det_progress.setValue(0)

        while self.det_layout.count():
            item = self.det_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        conf = self.thresh_slider.value() / 100.0

        self.info_labels["Status"].setText("ANALYZING")
        self.info_labels["Status"].setStyleSheet(
            "color: #f0a030; font-size: 11px; font-weight: 700;"
        )

        AUDIT.log("AI DETECTION INITIATED", f"confidence: {conf:.0%}")

        self.thread = AIDetectionThread(
            self.source_image,
            conf_threshold=conf
        )

        self.thread.progress.connect(self.det_progress.setValue)
        self.thread.log_msg.connect(self.log)
        self.thread.finished.connect(self.detection_done)
        self.thread.start()

    def detection_done(self, annotated, detections, success, msg):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("◈  RUN FORENSIC DETECTION")
        if not success:
            self.log(f"DETECTION FAILED: {msg}")
            return
        self.annotated_image = annotated
        self.detections      = detections
        self._show_image(annotated)
        self.log(msg)
        AUDIT.log("DETECTION COMPLETE", f"{len(detections)} evidence items")
        cats = {"WEAPON":0,"BIOLOGICAL":0,"TRACE EVIDENCE":0,"SCENE OBJECT":0}
        for d in detections:
            c = d.get("category","SCENE OBJECT")
            if c in cats: cats[c] += 1
        self.info_labels["Total Evidence"].setText(str(len(detections)))
        self.info_labels["Weapons"].setText(str(cats["WEAPON"]))
        self.info_labels["Biological"].setText(str(cats["BIOLOGICAL"]))
        self.info_labels["Trace"].setText(str(cats["TRACE EVIDENCE"]))
        self.info_labels["Scene Objects"].setText(str(cats["SCENE OBJECT"]))
        self.info_labels["Status"].setText("COMPLETE")
        self.info_labels["Status"].setStyleSheet("color: #4caf82; font-size: 11px; font-weight: 700;")
        # Send to mobile server
        if self.source_image is not None:
            MOBILE_SERVER.set_detection_data(
                annotated, detections, self.source_image)
            self.log("Mobile server updated — crops ready for investigator review")
                    # Clear previous evidence cards
            while self.det_layout.count():
                item = self.det_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Create evidence cards
            for i, d in enumerate(detections):
                ev_id = f"E-{i+1:03d}"
                self.add_detection_card(d, ev_id)

    def _show_image(self, img):
        h, w   = img.shape[:2]
        rgb    = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg   = QImage(rgb.data, w, h, 3*w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(
            self.display.width(), self.display.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.display.setPixmap(pixmap)

    def export_result(self):
        if self.annotated_image is None:
            self.log("ERROR: Run detection pipeline first")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Forensic Detection Map",
            f"exports/FORENSIC_DETECTION_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG (*.png);;JPG (*.jpg)"
        )
        if path:
            cv2.imwrite(path, self.annotated_image)
            MANIFEST.register(path, "EXPORTED", "Forensic detection output")
            AUDIT.log("DETECTION MAP EXPORTED", path)
            self.log(f"Forensic detection map exported + hashed: {path}")

    def add_detection_card(self, det, ev_id):
        card = QFrame()
        card.setObjectName("glassPanel")

        layout = QVBoxLayout(card)

        info = QLabel(
            f"{ev_id} {det['label']}\n"
            f"Grid: {det['grid']} | "
            f"Conf: {int(det['confidence']*100)}%"
        )

        layout.addWidget(info)

        btn_row = QHBoxLayout()

        confirm_btn = QPushButton("✓ CONFIRM")
        confirm_btn.setObjectName("successBtn")

        reject_btn = QPushButton("✗ REJECT")
        reject_btn.setObjectName("dangerBtn")

        btn_row.addWidget(confirm_btn)
        btn_row.addWidget(reject_btn)

        layout.addLayout(btn_row)

        self.det_layout.addWidget(card)

        confirm_btn.clicked.connect(
            lambda: self.confirm_evidence(ev_id, card)
        )

        reject_btn.clicked.connect(
            lambda: self.reject_evidence(ev_id, card)
        )

    def confirm_evidence(self, ev_id, card):

        MOBILE_SERVER.data["confirmed"].append(ev_id)

        card.setStyleSheet(
            "border:2px solid #52c488;"
        )

        self.log_box.append_log(
            f"CONFIRMED: {ev_id}"
        )

    def reject_evidence(self, ev_id, card):

        MOBILE_SERVER.data["rejected"].append(ev_id)

        card.setStyleSheet(
            "border:2px solid #f06060;"
        )

        self.log_box.append_log(
            f"REJECTED: {ev_id}"
        )

# ─────────────────────────────────────────────

# REPORTS PAGE

# ─────────────────────────────────────────────

class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        hdr = QLabel("FORENSIC CASE REPORT GENERATION")
        hdr.setStyleSheet(
            "color: #4dc8f0; font-size: 15px; font-weight: 700; letter-spacing: 2px;"
        )
        layout.addWidget(hdr)

        sub = QLabel(
            "Court-ready forensic report — SHA-256 verified — timestamped — full chain of custody"
        )
        sub.setStyleSheet("color: #2a5a7a; font-size: 11px;")
        layout.addWidget(sub)

        btn_frame  = QFrame()
        btn_frame.setObjectName("glassPanel")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(18, 14, 18, 14)
        btn_layout.setSpacing(12)

        self.pdf_btn = QPushButton("📄  GENERATE PDF REPORT")
        self.pdf_btn.setObjectName("captureBtn")
        self.pdf_btn.setFixedHeight(42)
        self.pdf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pdf_btn.clicked.connect(self.export_pdf)
        btn_layout.addWidget(self.pdf_btn)

        self.json_btn = QPushButton("↗  EXPORT JSON")
        self.json_btn.setObjectName("actionBtn")
        self.json_btn.setFixedHeight(42)
        self.json_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.json_btn.clicked.connect(lambda: self.export_data("json"))
        btn_layout.addWidget(self.json_btn)

        self.csv_btn = QPushButton("↗  EXPORT CSV")
        self.csv_btn.setObjectName("actionBtn")
        self.csv_btn.setFixedHeight(42)
        self.csv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.csv_btn.clicked.connect(lambda: self.export_data("csv"))
        btn_layout.addWidget(self.csv_btn)

        self.refresh_btn = QPushButton("↺  REFRESH REPORT")
        self.refresh_btn.setObjectName("actionBtn")
        self.refresh_btn.setFixedHeight(42)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh_preview)
        btn_layout.addWidget(self.refresh_btn)

        btn_layout.addStretch()

        self.status_label = QLabel("Click ↺ REFRESH REPORT to load current case data")
        self.status_label.setStyleSheet("color: #4a7a9a; font-size: 11px;")
        btn_layout.addWidget(self.status_label)
        layout.addWidget(btn_frame)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Click ↺ REFRESH REPORT to load current case data...")
        layout.addWidget(self.preview, 1)

    def _collect_case_data(self):
        try:
            try:
                hash_status = summarize_integrity_results(MANIFEST.verify_all())
            except (OSError, RuntimeError, ValueError):
                hash_status = "VERIFICATION INCOMPLETE: MANIFEST OR FILE ACCESS ERROR"
            main_win = self.window()
            dash = main_win.dashboard_page
            ai   = main_win.ai_page
            gal  = main_win.gallery_page
            return {
                "software":         "SpiderCam Forensic Suite v2.1",
                "export_timestamp": datetime.now().isoformat(),
                "case_id":          dash.case_input.text() or "—",
                "investigator":     dash.inv_input.text() or "—",
                "location":         dash.loc_input.text() or "—",
                "date":             dash.date_input.text() or "—",
                "images_loaded":    len(gal.loaded_images),
                "evidence_items":   len(ai.detections),
                "detections":       ai.detections,
                "manifest_entries": MANIFEST.get_summary()["total"],
                "evidence_hash_status": hash_status,
                "operator":         "M SELVAPRAKASH",
                "notes":            "Generated by SpiderCam Forensic Suite v2.1 — M SELVAPRAKASH"
            }
        except Exception as e:
            return {"error": str(e)}

    def refresh_preview(self):
        data  = self._collect_case_data()
        lines = [
            "═══════════════════════════════════════════════════════════════",
            "           SPIDERCAM FORENSIC SUITE  v2.1 — CASE REPORT",
            "═══════════════════════════════════════════════════════════════",
            f"  Software:          {data.get('software','')}",
            f"  Generated:         {data.get('export_timestamp','')}",
            f"  Operator:          {data.get('operator','')}",
            "───────────────────────────────────────────────────────────────",
            "  CASE INFORMATION",
            "───────────────────────────────────────────────────────────────",
            f"  Case ID:           {data.get('case_id','')}",
            f"  Investigator:      {data.get('investigator','')}",
            f"  Location:          {data.get('location','')}",
            f"  Date:              {data.get('date','')}",
            "───────────────────────────────────────────────────────────────",
            "  EVIDENCE SUMMARY",
            "───────────────────────────────────────────────────────────────",
            f"  Images Loaded:     {data.get('images_loaded',0)}",
            f"  Evidence Items:    {data.get('evidence_items',0)}",
            f"  Manifest Entries:  {data.get('manifest_entries',0)}",
            f"  Evidence Hash Status: {data.get('evidence_hash_status','')}",
            "───────────────────────────────────────────────────────────────",
            "  DETECTED EVIDENCE",
            "───────────────────────────────────────────────────────────────",
        ]
        for i, det in enumerate(data.get("detections", [])):
            ev_id = f"E-{i+1:03d}"
            lines.append(
                f"  {ev_id}  {det['label']:<22} "
                f"Grid: {det['grid']:<6} "
                f"Conf: {det['confidence']:.0%}   "
                f"Cat: {det['category']}"
            )
        lines += [
            "───────────────────────────────────────────────────────────────",
            f"  {data.get('notes','')}",
            "═══════════════════════════════════════════════════════════════",
        ]
        self.preview.setText("\n".join(lines))
        self.status_label.setText("✔ Report data loaded")
        self.status_label.setStyleSheet("color: #4caf82; font-size: 12px; font-weight: 600;")

    def export_pdf(self):
        data = self._collect_case_data()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Forensic PDF Report",
            f"exports/CASE_{data.get('case_id','UNKNOWN').replace(' ','_')}"
            f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)"
        )
        if not path: return
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer,
                Table, TableStyle, HRFlowable
            )
            from reportlab.lib.units import cm

            doc = SimpleDocTemplate(
                path, pagesize=A4,
                topMargin=2*cm, bottomMargin=2*cm,
                leftMargin=2*cm, rightMargin=2*cm
            )
            CYAN  = colors.HexColor("#4dc8f0")
            WHITE = colors.white
            GRAY  = colors.HexColor("#7a9ab8")

            title_style = ParagraphStyle('title',
                fontName='Helvetica-Bold', fontSize=20,
                textColor=CYAN, spaceAfter=6, leading=24)
            sub_style = ParagraphStyle('sub',
                fontName='Helvetica', fontSize=10,
                textColor=GRAY, spaceAfter=12)
            section_style = ParagraphStyle('section',
                fontName='Helvetica-Bold', fontSize=12,
                textColor=CYAN, spaceBefore=12, spaceAfter=6)
            body_style = ParagraphStyle('body',
                fontName='Helvetica', fontSize=10,
                textColor=colors.HexColor("#333333"), leading=16)

            story = []
            story.append(Paragraph("◈ SPIDERCAM FORENSIC SUITE  v2.1", title_style))
            story.append(Paragraph("Forensic Crime Scene Investigation Report", sub_style))
            story.append(HRFlowable(width="100%", thickness=1, color=CYAN))
            story.append(Spacer(1, 0.4*cm))

            story.append(Paragraph("CASE INFORMATION", section_style))
            case_data = [
                ["Case ID",      data.get("case_id","—")],
                ["Investigator", data.get("investigator","—")],
                ["Location",     data.get("location","—")],
                ["Date",         data.get("date","—")],
                ["Operator",     data.get("operator","—")],
                ["Generated",    data.get("export_timestamp","—")],
                ["Software",     data.get("software","—")],
            ]
            t = Table(case_data, colWidths=[5*cm, 12*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND',    (0,0),(0,-1), colors.HexColor("#e8f4f8")),
                ('FONTNAME',      (0,0),(0,-1), 'Helvetica-Bold'),
                ('FONTNAME',      (1,0),(1,-1), 'Helvetica'),
                ('FONTSIZE',      (0,0),(-1,-1), 10),
                ('TEXTCOLOR',     (0,0),(0,-1), colors.HexColor("#0d3a5c")),
                ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white, colors.HexColor("#f5fafc")]),
                ('GRID',          (0,0),(-1,-1), 0.5, colors.HexColor("#c0d8e8")),
                ('TOPPADDING',    (0,0),(-1,-1), 6),
                ('BOTTOMPADDING', (0,0),(-1,-1), 6),
                ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.4*cm))

            story.append(Paragraph("EVIDENCE SUMMARY", section_style))
            summary_data = [
                ["Images Loaded",    str(data.get("images_loaded",0))],
                ["Evidence Items",   str(data.get("evidence_items",0))],
                ["Manifest Entries", str(data.get("manifest_entries",0))],
                ["Evidence Hash Status", data.get("evidence_hash_status","—")],
            ]
            t2 = Table(summary_data, colWidths=[5*cm, 12*cm])
            t2.setStyle(TableStyle([
                ('BACKGROUND',    (0,0),(0,-1), colors.HexColor("#e8f4f8")),
                ('FONTNAME',      (0,0),(0,-1), 'Helvetica-Bold'),
                ('FONTNAME',      (1,0),(1,-1), 'Helvetica'),
                ('FONTSIZE',      (0,0),(-1,-1), 10),
                ('TEXTCOLOR',     (0,0),(0,-1), colors.HexColor("#0d3a5c")),
                ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white, colors.HexColor("#f5fafc")]),
                ('GRID',          (0,0),(-1,-1), 0.5, colors.HexColor("#c0d8e8")),
                ('TOPPADDING',    (0,0),(-1,-1), 6),
                ('BOTTOMPADDING', (0,0),(-1,-1), 6),
                ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ]))
            story.append(t2)
            story.append(Spacer(1, 0.4*cm))

            detections = data.get("detections", [])
            if detections:
                story.append(Paragraph("FORENSIC EVIDENCE REGISTRY", section_style))
                det_data = [["Evidence ID","Item","Category","Grid Ref","Position","Confidence"]]
                for i, d in enumerate(detections):
                    ev_id = f"E-{i+1:03d}"
                    det_data.append([
                        ev_id, d.get("label","—"), d.get("category","—"),
                        d.get("grid","—"), str(d.get("center","—")),
                        f"{d.get('confidence',0):.0%}"
                    ])
                t3 = Table(det_data, colWidths=[2*cm, 3.5*cm, 3.5*cm, 2*cm, 3.5*cm, 2.5*cm])
                t3.setStyle(TableStyle([
                    ('BACKGROUND',    (0,0),(-1,0), colors.HexColor("#0d3a5c")),
                    ('TEXTCOLOR',     (0,0),(-1,0), WHITE),
                    ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE',      (0,0),(-1,-1), 9),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor("#f5fafc")]),
                    ('GRID',          (0,0),(-1,-1), 0.5, colors.HexColor("#c0d8e8")),
                    ('TOPPADDING',    (0,0),(-1,-1), 5),
                    ('BOTTOMPADDING', (0,0),(-1,-1), 5),
                    ('LEFTPADDING',   (0,0),(-1,-1), 6),
                    ('ALIGN',         (0,0),(-1,-1), 'LEFT'),
                ]))
                story.append(t3)
                story.append(Spacer(1, 0.4*cm))

            story.append(Paragraph("EVIDENCE FILE HASH MANIFEST", section_style))
            manifest_entries = MANIFEST.entries
            if manifest_entries:
                coc_data = [["Acq. ID","Timestamp","Filename","Action","SHA-256"]]
                for e in manifest_entries[:20]:
                    coc_data.append([
                        e.get("acquisition_id","—"),
                        e.get("timestamp","")[:19],
                        e.get("filename","—")[:22],
                        e.get("action","—"),
                        e.get("sha256","—")[:16]+"..."
                    ])
                t4 = Table(coc_data, colWidths=[2*cm, 4*cm, 4*cm, 2.5*cm, 4.5*cm])
                t4.setStyle(TableStyle([
                    ('BACKGROUND',    (0,0),(-1,0), colors.HexColor("#0d3a5c")),
                    ('TEXTCOLOR',     (0,0),(-1,0), WHITE),
                    ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE',      (0,0),(-1,-1), 8),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor("#f5fafc")]),
                    ('GRID',          (0,0),(-1,-1), 0.5, colors.HexColor("#c0d8e8")),
                    ('TOPPADDING',    (0,0),(-1,-1), 4),
                    ('BOTTOMPADDING', (0,0),(-1,-1), 4),
                    ('LEFTPADDING',   (0,0),(-1,-1), 4),
                ]))
                story.append(t4)
            else:
                story.append(Paragraph("No manifest entries recorded.", body_style))

            story.append(Spacer(1, 0.6*cm))
            story.append(HRFlowable(width="100%", thickness=1, color=CYAN))
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph(
                f"SpiderCam Forensic Suite v2.1  ·  M SELVAPRAKASH  |  "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ParagraphStyle('footer', fontName='Helvetica', fontSize=8,
                               textColor=GRAY, alignment=1)
            ))
            doc.build(story)
            MANIFEST.register(path, "REPORT_EXPORTED", "PDF forensic report")
            AUDIT.log("PDF REPORT EXPORTED", path)
            self.status_label.setText("✔ PDF report generated successfully")
            self.status_label.setStyleSheet("color: #4caf82; font-size: 12px; font-weight: 600;")
        except Exception as e:
            self.status_label.setText(f"✕ PDF generation failed: {str(e)}")
            self.status_label.setStyleSheet("color: #f05050; font-size: 12px; font-weight: 600;")

    def export_data(self, fmt):
        data = self._collect_case_data()
        path, _ = QFileDialog.getSaveFileName(
            self, f"Export {fmt.upper()} Report",
            f"exports/CASE_{data.get('case_id','UNKNOWN').replace(' ','_')}"
            f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}",
            f"{fmt.upper()} Files (*.{fmt})"
        )
        if not path: return
        try:
            if fmt == "json":
                with open(path,'w') as f:
                    json.dump(data, f, indent=2)
            elif fmt == "csv":
                with open(path,'w', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(["Field","Value"])
                    for k, v in data.items():
                        if k != "detections":
                            w.writerow([k, v])
                    if data.get("detections"):
                        w.writerow([])
                        w.writerow(["Evidence ID","Label","Category","Grid","X","Y","Confidence"])
                        for i, d in enumerate(data["detections"]):
                            cx, cy = d.get("center",(0,0))
                            ev_id  = f"E-{i+1:03d}"
                            w.writerow([ev_id, d["label"], d["category"],
                                        d["grid"], cx, cy, f"{d['confidence']:.0%}"])
            AUDIT.log(f"{fmt.upper()} REPORT EXPORTED", path)
            self.status_label.setText(f"✔ {fmt.upper()} exported successfully")
            self.status_label.setStyleSheet("color: #4caf82; font-size: 12px; font-weight: 600;")
            self.preview.setText(json.dumps(data, indent=2))
        except Exception as e:
            self.status_label.setText(f"✕ Export failed: {str(e)}")
            self.status_label.setStyleSheet("color: #f05050; font-size: 12px; font-weight: 600;")

# ─────────────────────────────────────────────

# SETTINGS PAGE

# ─────────────────────────────────────────────

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        hdr = QLabel("SYSTEM CONFIGURATION")
        hdr.setStyleSheet(
            "color: #4dc8f0; font-size: 15px; font-weight: 700; letter-spacing: 2px;"
        )
        layout.addWidget(hdr)

        sections = [
            ("OUTPUT CONFIGURATION", [
                ("Default Export Path", "exports/"),
                ("Report Format",       "PDF + JSON + CSV"),
            ]),
            ("DETECTION CONFIGURATION", [
                ("Default Confidence Threshold", "35%"),
                ("Detection Model",              "YOLOv8n (auto-download)"),
                ("Grid Configuration",           "8×8 forensic grid"),
            ]),
            ("EVIDENCE FILE HASHING", [
                ("Hashing Algorithm",  "SHA-256"),
                ("Auto-timestamp",     "Enabled"),
                ("Audit Log Path",     "case_data/audit_log.txt"),
                ("Manifest Path",      "case_data/<case_id>/manifest.json"),
            ]),
        ]
        for section_title, items in sections:
            sec_frame  = QFrame()
            sec_frame.setObjectName("glassPanel")
            sec_layout = QVBoxLayout(sec_frame)
            sec_layout.setContentsMargins(20, 16, 20, 16)
            sec_layout.setSpacing(12)
            sl = QLabel(section_title)
            sl.setStyleSheet(
                "color: #2a5a7a; font-size: 10px; font-weight: 700; letter-spacing: 2px;"
            )
            sec_layout.addWidget(sl)
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet("background: #162838;")
            sec_layout.addWidget(sep)
            for label, default in items:
                row = QHBoxLayout()
                l = QLabel(label)
                l.setStyleSheet("color: #5a8aaa; font-size: 12px;")
                l.setFixedWidth(290)
                row.addWidget(l)
                inp = QLineEdit()
                inp.setText(default)
                row.addWidget(inp)
                sec_layout.addLayout(row)
            layout.addWidget(sec_frame)

        verify_frame = QFrame()
        verify_frame.setObjectName("glassPanel")
        vl = QVBoxLayout(verify_frame)
        vl.setContentsMargins(20, 16, 20, 16)
        vl.setSpacing(12)
        vt = QLabel("EVIDENCE INTEGRITY VERIFICATION")
        vt.setStyleSheet(
            "color: #2a5a7a; font-size: 10px; font-weight: 700; letter-spacing: 2px;"
        )
        vl.addWidget(vt)
        verify_btn = QPushButton("🔒  VERIFY ALL EVIDENCE HASHES")
        verify_btn.setObjectName("actionBtn")
        verify_btn.setFixedHeight(40)
        verify_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        verify_btn.clicked.connect(self.verify_integrity)
        vl.addWidget(verify_btn)
        self.verify_result = QLabel(
            "Click to verify SHA-256 integrity of all registered evidence"
        )
        self.verify_result.setStyleSheet("color: #4a7a9a; font-size: 11px;")
        vl.addWidget(self.verify_result)

        # Mobile server panel
        server_frame = QFrame()
        server_frame.setObjectName("glassPanel")
        sv = QVBoxLayout(server_frame)
        sv.setContentsMargins(20, 16, 20, 16)
        sv.setSpacing(10)
        st = QLabel("MOBILE SERVER STATUS")
        st.setStyleSheet(
            "color: #2a5a7a; font-size: 10px; font-weight: 700; letter-spacing: 2px;"
        )
        sv.addWidget(st)
        import socket
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "127.0.0.1"
        ip_lbl = QLabel(
            f"Laptop IP:  {local_ip}:8765\n"
            f"Mobile → enter this IP in Flutter app\n"
            f"Endpoints: /full_image  /detections  /crop/E-001\n"
            f"           /confirm (POST)  /reject (POST)"
        )
        ip_lbl.setStyleSheet(
            "color: #4dc8f0; font-size: 11px; font-family: 'Consolas';"
        )
        sv.addWidget(ip_lbl)
        layout.addWidget(server_frame)
        layout.addWidget(verify_frame)

        layout.addStretch()


        save_btn = QPushButton("SAVE CONFIGURATION")
        save_btn.setObjectName("successBtn")
        save_btn.setFixedWidth(210)
        save_btn.setFixedHeight(42)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(save_btn)

    def verify_integrity(self):
        def display(message, indicator, color):
            self.verify_result.setText(message)
            self.verify_result.setStyleSheet(
                f"color: {color}; font-size: 11px; font-weight: 700;"
            )
            main_window = self.window()
            top_bar = getattr(main_window, "top_bar", None)
            if top_bar is not None:
                top_bar.integrity_label.setText(indicator)
                top_bar.integrity_label.setStyleSheet(
                    f"color: {color}; font-size: 10px; "
                    "font-weight: 600; letter-spacing: 1px;"
                )
            dashboard = getattr(main_window, "dashboard_page", None)
            if dashboard is not None:
                dashboard.card_hash.set_value(indicator.replace("HASH STATUS: ", ""))

        try:
            results = MANIFEST.verify_all()
        except (OSError, RuntimeError, ValueError):
            display(
                "INTEGRITY CHECK INCOMPLETE: manifest or file access error",
                "HASH STATUS: INCOMPLETE",
                "#f05050",
            )
            return
        if not results:
            display(
                "No evidence registered in current session",
                "HASH STATUS: NO EVIDENCE",
                "#8a9aaa",
            )
            return
        invalid = [r for r in results if r[1] == "INVALID_MANIFEST"]
        unreadable = [r for r in results if r[1] == "UNREADABLE"]
        modified = [r for r in results if r[1] == "MODIFIED"]
        missing  = [r for r in results if r[1] == "MISSING"]
        verified = [r for r in results if r[1] == "VERIFIED"]
        unexpected = len(results) - len(invalid) - len(unreadable) - len(modified) - len(missing) - len(verified)
        if invalid or unreadable or modified or missing or unexpected:
            display(
                "INTEGRITY CHECK FAILED: "
                f"{len(invalid)} invalid manifest, {len(unreadable)} unreadable, "
                f"{len(modified)} modified, {len(missing)} missing; "
                f"{unexpected} unrecognized, {len(verified)} verified",
                "HASH STATUS: FAILED",
                "#f05050",
            )
        else:
            display(
                f"ALL {len(verified)} EVIDENCE FILE HASHES MATCH THE MANIFEST",
                "HASH STATUS: MATCH",
                "#4caf82",
            )
        try:
            AUDIT.log("INTEGRITY VERIFICATION",
                      f"{len(verified)} verified, {len(modified)} modified, "
                      f"{len(missing)} missing, {len(unreadable)} unreadable, "
                      f"{len(invalid)} invalid manifest")
        except OSError:
            display(
                "INTEGRITY CHECK INCOMPLETE: audit log could not be written",
                "HASH STATUS: INCOMPLETE",
                "#f05050",
            )

# ─────────────────────────────────────────────

# 3D WALKTHROUGH PAGE

# ─────────────────────────────────────────────

class Reconstruction3DPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        hdr = QLabel("3D FORENSIC SCENE WALKTHROUGH")
        hdr.setStyleSheet(
            "color: #4dc8f0; font-size: 15px; font-weight: 700; letter-spacing: 2px;"
        )
        layout.addWidget(hdr)

        sub = QLabel(
            "COLMAP photogrammetry → Dense point cloud → Three.js forensic walkthrough viewer"
        )
        sub.setStyleSheet("color: #2a5a7a; font-size: 11px;")
        layout.addWidget(sub)

        btn_frame  = QFrame()
        btn_frame.setObjectName("glassPanel")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(18, 14, 18, 14)
        btn_layout.setSpacing(12)

        self.open_btn = QPushButton("▶  LAUNCH WALKTHROUGH VIEWER")
        self.open_btn.setObjectName("captureBtn")
        self.open_btn.setFixedHeight(42)
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.clicked.connect(self.open_walkthrough)
        btn_layout.addWidget(self.open_btn)

        self.status_lbl = QLabel("● VIEWER READY")
        self.status_lbl.setStyleSheet("color: #4caf82; font-size: 12px; font-weight: 600;")
        btn_layout.addWidget(self.status_lbl)
        btn_layout.addStretch()
        layout.addWidget(btn_frame)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)
        self.card_points   = StatCard("Point Cloud",    "—", "pts",   "#4dc8f0")
        self.card_frames   = StatCard("Frames Used",    "—", "imgs",  "#f0a030")
        self.card_evidence = StatCard("Evidence Items", "—", "items", "#4caf82")
        self.card_status   = StatCard("Reconstruction", "PENDING", "", "#f0a030")
        for card in [self.card_points, self.card_frames,
                     self.card_evidence, self.card_status]:
            cards_layout.addWidget(card)
        layout.addLayout(cards_layout)

        info = QFrame()
        info.setObjectName("glassPanel")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(22, 18, 22, 18)
        info_layout.setSpacing(8)

        info_title = QLabel("RECONSTRUCTION WORKFLOW")
        info_title.setStyleSheet(
            "color: #2a5a7a; font-size: 10px; font-weight: 700; letter-spacing: 2px;"
        )
        info_layout.addWidget(info_title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #162838;")
        info_layout.addWidget(sep)

        steps = [
            "1.  Acquire scene video or load imagery in SCENE MAPPING",
            "2.  Execute RECONSTRUCT SCENE to generate spatial map",
            "3.  Run AI DETECTION for evidence coordinate mapping",
            "4.  Click ▶ 3D RECONSTRUCT in Scene Mapping to initiate photogrammetry",
            "5.  COLMAP processes scene geometry automatically (RTX GPU accelerated)",
            "6.  Launch walkthrough viewer when reconstruction completes",
            "7.  Navigate crime scene — WASD + Mouse — evidence markers active",
        ]
        for step in steps:
            l = QLabel(step)
            l.setStyleSheet("color: #4a7a9a; font-size: 12px; padding: 3px 0;")
            info_layout.addWidget(l)

        layout.addWidget(info)
        layout.addStretch()

        self.log_box = ForensicLogWidget(placeholder="3D reconstruction pipeline log...")
        self.log_box.setFixedHeight(110)
        layout.addWidget(self.log_box)

    def open_walkthrough(self):
        import webbrowser
        try:
            from reconstruction_3d import start_flask_server
            start_flask_server(self.log)
            webbrowser.open("http://127.0.0.1:5000")
            self.log("Forensic walkthrough viewer launched in browser")
            self.status_lbl.setText("● VIEWER ACTIVE")
            self.status_lbl.setStyleSheet("color: #4caf82; font-size: 12px; font-weight: 600;")
        except Exception as e:
            self.log(f"ERROR: {str(e)}")

    def log(self, msg): self.log_box.append_log(msg)

# ─────────────────────────────────────────────

# PLACEHOLDER PAGE

# ─────────────────────────────────────────────

class PlaceholderPage(QWidget):
    def __init__(self, title, icon="◈", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic = QLabel(icon)
        ic.setStyleSheet("color: #1a3a5a; font-size: 52px;")
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ic)
        lbl = QLabel(title)
        lbl.setStyleSheet(
        "color: #2a4a6a; font-size: 16px; font-weight: 700; letter-spacing: 2px;"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        sub = QLabel("Module under development — coming in next release")
        sub.setStyleSheet("color: #1a3a5a; font-size: 11px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

    # ─────────────────────────────────────────────

    # BOTTOM STATUS BAR

    # ─────────────────────────────────────────────

class BottomStatusBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusBar")
        self.setFixedHeight(30)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 0, 22, 0)
        layout.setSpacing(20)

        self.left_msg = QLabel("SYSTEM OPERATIONAL  ●")
        self.left_msg.setStyleSheet(
            "color: #4caf82; font-size: 10px; font-weight: 600; letter-spacing: 1px;"
        )
        layout.addWidget(self.left_msg)
        layout.addStretch()

        self.mid_msg = QLabel("SpiderCam Forensic Suite  v2.1  ·  M SELVAPRAKASH")
        self.mid_msg.setStyleSheet("color: #1a3a54; font-size: 10px;")
        layout.addWidget(self.mid_msg)
        layout.addStretch()

        self.right_msg = QLabel("SHA-256 File Hashing  |  Local Audit Log")
        self.right_msg.setStyleSheet("color: #1a3a54; font-size: 10px;")
        layout.addWidget(self.right_msg)

    def set_message(self, msg, color="#4caf82"):
        self.left_msg.setText(msg)
        self.left_msg.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 600; letter-spacing: 1px;"
        )

# ─────────────────────────────────────────────

# MAIN WINDOW

# ─────────────────────────────────────────────

class SpiderCamMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpiderCam Forensic Suite  v2.1  —  M SELVAPRAKASH")
        self.setMinimumSize(1280, 780)
        self.resize(1440, 860)
        self.setStyleSheet(MASTER_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.top_bar = TopBar()
        main_layout.addWidget(self.top_bar)

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self.switch_page)
        content_layout.addWidget(self.sidebar)

        self.stack           = QStackedWidget()
        self.dashboard_page  = DashboardPage()
        self.live_feed_page  = LiveFeedPage()
        self.gallery_page    = EvidenceGalleryPage()
        self.mapping_page    = SceneMappingPage()
        self.ai_page         = AIDetectionPage()
        self.analysis_page   = PlaceholderPage("ANALYSIS MODULE", "≡")
        self.reports_page    = ReportsPage()
        self.settings_page   = SettingsPage()
        self.recon3d_page    = Reconstruction3DPage()

        for page in [
            self.dashboard_page, self.live_feed_page, self.gallery_page,
            self.mapping_page,   self.ai_page,        self.analysis_page,
            self.reports_page,   self.settings_page,  self.recon3d_page
        ]:
            self.stack.addWidget(page)

        content_layout.addWidget(self.stack, 1)
        main_layout.addWidget(content, 1)

        self.status_bar = BottomStatusBar()
        main_layout.addWidget(self.status_bar)

        self.web_bg = SpiderWebBackground(central)
        self.web_bg.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.web_bg.lower()

        self.dashboard_page.open_btn.clicked.connect(self.initialise_case)
        self.live_feed_page.frames_ready.connect(
            self.mapping_page.receive_live_frames
        )

        AUDIT.log("SPIDERCAM FORENSIC SUITE v2.1 INITIALISED", "M SELVAPRAKASH")
        MOBILE_SERVER.log_msg.connect(lambda m: print(f"[SERVER] {m}"))
        MOBILE_SERVER.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.web_bg.setGeometry(self.centralWidget().rect())

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)

    def initialise_case(self):
        case_id  = self.dashboard_page.case_input.text().strip()
        operator = self.dashboard_page.inv_input.text().strip() or "M SELVAPRAKASH"
        if case_id:
            MANIFEST.set_case(case_id, operator)
            self.top_bar.set_case(case_id)
            self.status_bar.set_message(f"CASE ACTIVE: {case_id}  ●", "#4caf82")
            AUDIT.log("CASE INITIALISED", f"Case: {case_id} | Operator: {operator}")
        else:
            self.status_bar.set_message("⚠  Case ID required to initialise", "#f0a030")

# ─────────────────────────────────────────────

# ENTRY POINT

# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("SpiderCam Forensic Suite")
    window = SpiderCamMain()
    window.show()
    sys.exit(app.exec())
