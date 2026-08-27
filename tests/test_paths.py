from pathlib import Path

import config
from app import MARKER_LABELS
from video_resolver import resolve_video


def test_default_paths_are_resolved():
    assert config.MASTER_FILE.name == "EMA_Master_\u63d0\u6848\u5f62\u5f0f.xlsx"
    assert config.RAW_DATA_ROOT.name == "01_RawData"
    assert config.ANALYSIS_ROOT.name == "Legend_Analysis"
    assert config.MARKED_VIDEO_DIR == config.ANALYSIS_ROOT / "Marked_Videos"


def test_empty_video_resolution_does_not_touch_raw_data():
    status = resolve_video("")
    assert status.status == "missing"


def test_pose_marker_set_contains_required_markers():
    for key in ["head", "left_shoulder", "left_elbow", "left_wrist", "right_shoulder", "torso_center"]:
        assert key in MARKER_LABELS
