from __future__ import annotations

from pathlib import Path


def probe_video(video_path: str | Path) -> dict[str, object]:
    path = Path(video_path)
    if not path.exists():
        return {"exists": False, "readable": False, "frame_count": 0, "fps": 0.0, "duration_sec": 0.0}
    try:
        import cv2  # type: ignore
    except Exception:
        return {"exists": True, "readable": False, "frame_count": 0, "fps": 0.0, "duration_sec": 0.0, "warning": "opencv-python is not available."}

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"exists": True, "readable": False, "frame_count": 0, "fps": 0.0, "duration_sec": 0.0}
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    cap.release()
    duration = frame_count / fps if fps > 0 else 0.0
    return {"exists": True, "readable": True, "frame_count": frame_count, "fps": fps, "duration_sec": duration}
