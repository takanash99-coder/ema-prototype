from __future__ import annotations

from datetime import datetime

from config import ANALYZER_VERSION
from face_analyzer import analyze_face
from hand_analyzer import analyze_hands
from models import ItemAnalysis, LegendAnalysisResult, TrialRecord, VideoStatus
from pose_analyzer import analyze_pose

ITEMS_10 = [
    "Ready Position",
    "Grip",
    "Left Arm Chain",
    "Trunk",
    "Gaze",
    "Smoothness",
    "Patient Distance",
    "Blade Trajectory",
    "Correction Movements",
    "AI Coaching",
]


def _item_result(item: str, pose: dict[str, object], hands: dict[str, object], face: dict[str, object]) -> ItemAnalysis:
    if item == "Grip":
        return ItemAnalysis(item=item, auto_result=str(hands.get("grip_candidate", "Requires confirmation")), confidence=0.35, final_result="Requires researcher confirmation")
    if item == "Gaze":
        return ItemAnalysis(item=item, auto_result=str(face.get("gaze_candidate", "Requires confirmation")), confidence=0.3, final_result="Requires researcher confirmation")
    if item == "AI Coaching":
        return ItemAnalysis(item=item, auto_result="Generate coaching after researcher review.", confidence=0.25, final_result="Draft only")
    return ItemAnalysis(item=item, auto_result="Initial motion feature placeholder", confidence=float(pose.get("confidence", 0.3)), final_result="Requires researcher confirmation")


def analyze_trial(record: TrialRecord, front_status: VideoStatus, side_status: VideoStatus) -> LegendAnalysisResult:
    selected_video = front_status.selected_path or side_status.selected_path
    pose = analyze_pose(selected_video) if selected_video else {"confidence": 0.0}
    hands = analyze_hands(selected_video) if selected_video else {}
    face = analyze_face(selected_video) if selected_video else {}
    items = [_item_result(item, pose, hands, face) for item in ITEMS_10]
    return LegendAnalysisResult(
        subject_name=record.subject_name,
        trial_id=record.trial_id,
        front_file=record.front_video,
        side_file=record.side_video,
        emg_file=record.emg_file,
        photo_file=record.photo_file,
        front_status=front_status,
        side_status=side_status,
        items=items,
        grip_type_candidate="Requires researcher confirmation",
        motion_type_candidate="Requires researcher confirmation",
        ai_coaching="This is a draft coaching field. Confirm motion findings before use.",
        analysis_date=datetime.now().isoformat(timespec="seconds"),
        analyzer_version=ANALYZER_VERSION,
        notes=record.remarks,
    )
