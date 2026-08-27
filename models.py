from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TrialRecord:
    subject_name: str = ""
    trial_id: str = ""
    front_video: str = ""
    side_video: str = ""
    emg_file: str = ""
    photo_file: str = ""
    exclude_flag: bool = False
    remarks: str = ""
    row_index: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoStatus:
    requested_file: str
    resolved_path: str = ""
    converted_mp4_path: str = ""
    selected_path: str = ""
    status: str = "missing"
    message: str = ""


@dataclass
class ItemAnalysis:
    item: str
    auto_result: str
    confidence: float
    researcher_confirmed: str = ""
    correction_notes: str = ""
    final_result: str = ""
    remarks: str = ""


@dataclass
class LegendAnalysisResult:
    subject_name: str
    trial_id: str
    front_file: str
    side_file: str
    emg_file: str
    photo_file: str
    front_status: VideoStatus
    side_status: VideoStatus
    items: list[ItemAnalysis]
    grip_type_candidate: str
    motion_type_candidate: str
    ai_coaching: str
    analysis_date: str
    analyzer_version: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["front_status"] = asdict(self.front_status)
        data["side_status"] = asdict(self.side_status)
        data["items"] = [asdict(item) for item in self.items]
        return data
