from __future__ import annotations

import os
import platform
from pathlib import Path

APP_NAME = "EMA Legend Analyzer"
ANALYZER_VERSION = "0.2.0-marking-mvp"
APP_ROOT = Path(__file__).resolve().parent

MASTER_FOLDER_NAME = "\u305d\u306e\u4ed6\u8cc7\u6599"
MASTER_FILE_NAME = "EMA_Master_\u63d0\u6848\u5f62\u5f0f.xlsx"
SAMPLE_MARKED_VIDEO_NAME = "stretcher_45_160_minus15_marked_20260825_091224.mp4"
SAMPLE_POSE_JSON_NAME = "stretcher_45_160_minus15_pose_20260825_091224.json"


def _env_path(name: str) -> Path | None:
    value = os.environ.get(name, "").strip()
    return Path(value).expanduser() if value else None


def _use_local_defaults() -> bool:
    disabled = os.environ.get("EMA_DISABLE_LOCAL_DEFAULTS", "").strip().lower()
    return disabled not in {"1", "true", "yes", "on"}


def _windows_default(path_text: str) -> Path | None:
    if platform.system() == "Windows" and _use_local_defaults():
        return Path(path_text)
    return None


PROJECT_ROOT = _env_path("EMA_PROJECT_ROOT") or _windows_default(r"F:\EMA_Project")
EMA_DATA_ROOT = _env_path("EMA_DATA_ROOT") or _windows_default(r"F:\EMA_Data")

UNAVAILABLE_ROOT = APP_ROOT / ".ema_unavailable"
OUTPUT_FALLBACK_ROOT = APP_ROOT / "local_outputs"

MASTER_FILE = (PROJECT_ROOT / MASTER_FOLDER_NAME / MASTER_FILE_NAME) if PROJECT_ROOT else (UNAVAILABLE_ROOT / MASTER_FOLDER_NAME / MASTER_FILE_NAME)
RAW_DATA_ROOT = (PROJECT_ROOT / "01_RawData") if PROJECT_ROOT else (UNAVAILABLE_ROOT / "01_RawData")

ANALYSIS_ROOT = _env_path("EMA_ANALYSIS_ROOT") or (
    EMA_DATA_ROOT / "Analysis" / "Legend_Analysis" if EMA_DATA_ROOT else OUTPUT_FALLBACK_ROOT / "Analysis" / "Legend_Analysis"
)
RESULTS_DIR = ANALYSIS_ROOT / "Results"
POSE_DATA_DIR = ANALYSIS_ROOT / "Pose_Data"
THUMBNAILS_DIR = ANALYSIS_ROOT / "Thumbnails"
LOGS_DIR = ANALYSIS_ROOT / "Logs"
REPORTS_DIR = ANALYSIS_ROOT / "Reports"
MARKED_VIDEO_DIR = ANALYSIS_ROOT / "Marked_Videos"

ASSETS_DIR = APP_ROOT / "assets"
POSE_MODEL_PATH = ASSETS_DIR / "pose_landmarker_lite.task"
SAMPLE_MARKED_VIDEO = MARKED_VIDEO_DIR / SAMPLE_MARKED_VIDEO_NAME
SAMPLE_POSE_JSON = POSE_DATA_DIR / SAMPLE_POSE_JSON_NAME

CONVERTED_MP4_DIR = EMA_DATA_ROOT / "Recording" / "Converted_MP4" if EMA_DATA_ROOT else OUTPUT_FALLBACK_ROOT / "Recording" / "Converted_MP4"
VIDEO_CONVERTER_DIR = PROJECT_ROOT / "03_Tools" / "ema_video_converter" if PROJECT_ROOT else UNAVAILABLE_ROOT / "03_Tools" / "ema_video_converter"

LOCAL_PROJECT_AVAILABLE = PROJECT_ROOT is not None and PROJECT_ROOT.exists()
LOCAL_DATA_AVAILABLE = EMA_DATA_ROOT is not None and EMA_DATA_ROOT.exists()
MASTER_AVAILABLE = MASTER_FILE.exists()
SAMPLE_MARKED_VIDEO_AVAILABLE = SAMPLE_MARKED_VIDEO.exists()
SAMPLE_POSE_JSON_AVAILABLE = SAMPLE_POSE_JSON.exists()
POSE_MODEL_AVAILABLE = POSE_MODEL_PATH.exists()

SUPPORTED_VIDEO_EXTENSIONS = {".mts", ".mp4"}
MASTER_DEFAULT_COLUMNS = {
    "subject_name": ["\u88ab\u9a13\u8005\u540d", "\u6c0f\u540d", "Name", "Subject", "Subject_Name"],
    "trial_id": ["\u8a66\u6280\u756a\u53f7", "\u8a66\u6280", "Trial", "Trial_ID", "Trial No"],
    "front_video": ["Front\u52d5\u753b\u540d", "Front\u52d5\u753b", "Front", "Front_file", "Front Video"],
    "side_video": ["Side\u52d5\u753b\u540d", "Side\u52d5\u753b", "Side", "Side_file", "Side Video"],
    "emg_file": ["EMG\u30d5\u30a1\u30a4\u30eb\u540d", "EMG", "EMG_file"],
    "photo_file": ["\u9759\u6b62\u753b\u540d", "Photo", "Photo_file"],
    "exclude_flag": ["\u9664\u5916\u30d5\u30e9\u30b0", "Exclude", "Exclude_Flag"],
    "remarks": ["\u5099\u8003", "Remarks", "Notes"],
}


def required_output_directories() -> list[Path]:
    return [RESULTS_DIR, POSE_DATA_DIR, THUMBNAILS_DIR, LOGS_DIR, REPORTS_DIR, MARKED_VIDEO_DIR]


def ensure_output_directories() -> list[Path]:
    created: list[Path] = []
    for directory in required_output_directories():
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(directory)
    return created
