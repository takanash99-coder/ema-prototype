from __future__ import annotations

from pathlib import Path

from config import CONVERTED_MP4_DIR, RAW_DATA_ROOT, SUPPORTED_VIDEO_EXTENSIONS
from models import VideoStatus


def _candidate_names(file_name: str) -> list[str]:
    name = str(file_name).strip()
    if not name:
        return []
    path = Path(name)
    names = [path.name]
    if path.suffix:
        names.append(path.with_suffix(".mp4").name)
    else:
        for suffix in (".mp4", ".MTS", ".mts"):
            names.append(path.name + suffix)
    return list(dict.fromkeys(names))


def _find_file(root: Path, names: list[str]) -> Path | None:
    if not root.exists():
        return None
    wanted = {name.lower() for name in names}
    for path in root.rglob("*"):
        if path.is_file() and path.name.lower() in wanted:
            return path
    return None


def resolve_video(file_name: str, raw_data_root: Path = RAW_DATA_ROOT, converted_mp4_dir: Path = CONVERTED_MP4_DIR) -> VideoStatus:
    names = _candidate_names(file_name)
    if not names:
        return VideoStatus(requested_file=file_name, status="missing", message="No file name was provided.")

    mp4_names = [Path(name).with_suffix(".mp4").name for name in names]
    converted = _find_file(converted_mp4_dir, mp4_names)
    raw = _find_file(raw_data_root, names)

    if converted is not None:
        return VideoStatus(
            requested_file=file_name,
            resolved_path=str(raw or ""),
            converted_mp4_path=str(converted),
            selected_path=str(converted),
            status="mp4_ready",
            message="Converted MP4 found and selected.",
        )

    if raw is not None:
        if raw.suffix.lower() == ".mp4":
            return VideoStatus(
                requested_file=file_name,
                resolved_path=str(raw),
                converted_mp4_path="",
                selected_path=str(raw),
                status="raw_mp4_ready",
                message="Raw MP4 found and selected read-only.",
            )
        if raw.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
            return VideoStatus(
                requested_file=file_name,
                resolved_path=str(raw),
                converted_mp4_path="",
                selected_path="",
                status="needs_conversion",
                message="Original video found, but converted MP4 is not available.",
            )

    return VideoStatus(requested_file=file_name, status="missing", message="Video file was not found.")
