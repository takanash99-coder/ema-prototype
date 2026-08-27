from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from config import ANALYZER_VERSION, MARKED_VIDEO_DIR, POSE_DATA_DIR, POSE_MODEL_PATH, ensure_output_directories

MARKERS = {
    "head": "\u982d\u90e8",
    "left_shoulder": "\u5de6\u80a9",
    "left_elbow": "\u5de6\u8098",
    "left_wrist": "\u5de6\u624b\u9996",
    "right_shoulder": "\u53f3\u80a9",
    "right_elbow": "\u53f3\u8098",
    "right_wrist": "\u53f3\u624b\u9996",
    "torso_center": "\u4f53\u5e79\u4e2d\u5fc3",
    "pelvis_center": "\u9aa8\u76e4\u4e2d\u5fc3",
}

LANDMARK_INDEX = {
    "head": 0,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
}
VISIBILITY_THRESHOLD = 0.35


@dataclass
class PoseMarker:
    x: float | None
    y: float | None
    confidence: float
    detected: bool


@dataclass
class PoseAnalysisOutput:
    source_video: str
    marked_video: str
    pose_json: str
    fps: float
    frame_count: int
    processed_frames: int
    duration_sec: float
    detection_rates: dict[str, float]
    analysis_date: str
    analyzer_version: str


def _safe_stem(path: Path) -> str:
    text = path.stem.strip() or "video"
    for char in '<>:"/\\|?*':
        text = text.replace(char, "_")
    return text


def _visibility(landmark) -> float:
    visibility = getattr(landmark, "visibility", None)
    presence = getattr(landmark, "presence", None)
    scores = [float(value) for value in (visibility, presence) if value is not None]
    return min(scores) if scores else 1.0


def _landmark(landmarks, key: str, width: int, height: int) -> PoseMarker:
    lm = landmarks[LANDMARK_INDEX[key]]
    confidence = _visibility(lm)
    detected = bool(confidence >= VISIBILITY_THRESHOLD and 0.0 <= lm.x <= 1.0 and 0.0 <= lm.y <= 1.0)
    return PoseMarker(
        x=float(lm.x * width) if detected else None,
        y=float(lm.y * height) if detected else None,
        confidence=confidence,
        detected=detected,
    )


def _midpoint(a: PoseMarker, b: PoseMarker) -> PoseMarker:
    if not a.detected or not b.detected or a.x is None or a.y is None or b.x is None or b.y is None:
        return PoseMarker(None, None, min(a.confidence, b.confidence), False)
    return PoseMarker((a.x + b.x) / 2, (a.y + b.y) / 2, min(a.confidence, b.confidence), True)


def _empty_markers() -> dict[str, PoseMarker]:
    return {key: PoseMarker(None, None, 0.0, False) for key in MARKERS}


def _extract_markers(landmarks, width: int, height: int) -> dict[str, PoseMarker]:
    left_shoulder = _landmark(landmarks, "left_shoulder", width, height)
    right_shoulder = _landmark(landmarks, "right_shoulder", width, height)
    left_hip = _landmark(landmarks, "left_hip", width, height)
    right_hip = _landmark(landmarks, "right_hip", width, height)
    pelvis_center = _midpoint(left_hip, right_hip)
    shoulder_center = _midpoint(left_shoulder, right_shoulder)
    torso_center = _midpoint(shoulder_center, pelvis_center) if pelvis_center.detected else shoulder_center
    return {
        "head": _landmark(landmarks, "head", width, height),
        "left_shoulder": left_shoulder,
        "left_elbow": _landmark(landmarks, "left_elbow", width, height),
        "left_wrist": _landmark(landmarks, "left_wrist", width, height),
        "right_shoulder": right_shoulder,
        "right_elbow": _landmark(landmarks, "right_elbow", width, height),
        "right_wrist": _landmark(landmarks, "right_wrist", width, height),
        "torso_center": torso_center,
        "pelvis_center": pelvis_center,
    }


def _point(marker: PoseMarker) -> tuple[int, int] | None:
    if not marker.detected or marker.x is None or marker.y is None:
        return None
    return int(round(marker.x)), int(round(marker.y))


def _draw_line(frame, markers: dict[str, PoseMarker], start: str, end: str, color: tuple[int, int, int]) -> None:
    p1 = _point(markers[start])
    p2 = _point(markers[end])
    if p1 and p2:
        cv2.line(frame, p1, p2, color, 3, cv2.LINE_AA)


def _draw_overlay(frame, markers: dict[str, PoseMarker]) -> None:
    cyan = (245, 220, 30)
    blue = (255, 120, 40)
    white = (255, 255, 255)
    _draw_line(frame, markers, "left_shoulder", "left_elbow", cyan)
    _draw_line(frame, markers, "left_elbow", "left_wrist", cyan)
    _draw_line(frame, markers, "left_shoulder", "right_shoulder", blue)
    _draw_line(frame, markers, "right_shoulder", "right_elbow", blue)
    _draw_line(frame, markers, "right_elbow", "right_wrist", blue)
    _draw_line(frame, markers, "torso_center", "pelvis_center", blue)
    for key in MARKERS:
        point = _point(markers[key])
        if point:
            cv2.circle(frame, point, 8, cyan, -1, cv2.LINE_AA)
            cv2.circle(frame, point, 11, white, 2, cv2.LINE_AA)
    cv2.putText(frame, "EMA Pose Marking MVP", (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 3, cv2.LINE_AA)
    cv2.putText(frame, "EMA Pose Marking MVP", (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.85, cyan, 2, cv2.LINE_AA)


def _create_landmarker(model_path: Path):
    if not model_path.exists():
        raise FileNotFoundError(f"Pose model not found: {model_path}")
    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_segmentation_masks=False,
    )
    return vision.PoseLandmarker.create_from_options(options)


def analyze_pose(
    video_path: str | Path,
    output_video_path: str | Path | None = None,
    pose_json_path: str | Path | None = None,
    *,
    progress_callback: Callable[[int, int], None] | None = None,
    max_frames: int | None = None,
) -> PoseAnalysisOutput:
    ensure_output_directories()
    source = Path(video_path)
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(f"Video file not found: {source}")

    stem = _safe_stem(source)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    marked_video = Path(output_video_path) if output_video_path else MARKED_VIDEO_DIR / f"{stem}_marked_{stamp}.mp4"
    pose_json = Path(pose_json_path) if pose_json_path else POSE_DATA_DIR / f"{stem}_pose_{stamp}.json"
    marked_video.parent.mkdir(parents=True, exist_ok=True)
    pose_json.parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {source}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if width <= 0 or height <= 0:
        cap.release()
        raise RuntimeError("Could not read video dimensions.")

    total_for_progress = min(frame_count, max_frames) if max_frames and frame_count else frame_count
    writer = cv2.VideoWriter(str(marked_video), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Could not create marked video: {marked_video}")

    marker_hits = {key: 0 for key in MARKERS}
    frames: list[dict[str, object]] = []
    processed = 0

    landmarker = _create_landmarker(POSE_MODEL_PATH)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if max_frames is not None and processed >= max_frames:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(round((processed / fps) * 1000)) if fps > 0 else processed * 33
            result = landmarker.detect_for_video(mp_image, timestamp_ms)
            if result.pose_landmarks:
                markers = _extract_markers(result.pose_landmarks[0], width, height)
            else:
                markers = _empty_markers()

            for key, marker in markers.items():
                if marker.detected:
                    marker_hits[key] += 1
            _draw_overlay(frame, markers)
            writer.write(frame)
            frames.append({
                "frame": processed,
                "timestamp": processed / fps if fps > 0 else 0.0,
                "markers": {key: asdict(marker) for key, marker in markers.items()},
            })
            processed += 1
            if progress_callback and (processed % 5 == 0 or processed == total_for_progress):
                progress_callback(processed, total_for_progress or processed)
    finally:
        landmarker.close()
        cap.release()
        writer.release()

    if progress_callback:
        progress_callback(processed, total_for_progress or processed)

    detection_rates = {key: (marker_hits[key] / processed if processed else 0.0) for key in MARKERS}
    payload = {
        "source_video": str(source),
        "marked_video": str(marked_video),
        "fps": fps,
        "frame_count": frame_count,
        "processed_frames": processed,
        "duration_sec": frame_count / fps if fps > 0 else 0.0,
        "detection_rates": detection_rates,
        "frames": frames,
        "analysis_date": datetime.now().isoformat(timespec="seconds"),
        "analyzer_version": ANALYZER_VERSION,
        "pose_model": str(POSE_MODEL_PATH),
        "note": "Source video was read-only. Missing detections were not imputed.",
    }
    pose_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return PoseAnalysisOutput(
        source_video=str(source),
        marked_video=str(marked_video),
        pose_json=str(pose_json),
        fps=fps,
        frame_count=frame_count,
        processed_frames=processed,
        duration_sec=frame_count / fps if fps > 0 else 0.0,
        detection_rates=detection_rates,
        analysis_date=payload["analysis_date"],
        analyzer_version=ANALYZER_VERSION,
    )
