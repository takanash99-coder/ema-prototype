from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import ANALYZER_VERSION, LOGS_DIR, RESULTS_DIR, ensure_output_directories
from models import LegendAnalysisResult


def _safe_name(value: str) -> str:
    text = str(value or "unknown").strip()
    for char in '<>:"/\\|?*':
        text = text.replace(char, "_")
    return text or "unknown"


def write_json(result: LegendAnalysisResult, results_dir: Path = RESULTS_DIR) -> Path:
    ensure_output_directories()
    destination = results_dir / f"Legend_{_safe_name(result.subject_name)}_{_safe_name(result.trial_id)}.json"
    destination.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def write_excel(results: list[LegendAnalysisResult], output_path: Path | None = None) -> Path:
    ensure_output_directories()
    destination = output_path or RESULTS_DIR / "EMA_Legend_Analysis_Results.xlsx"
    summary_rows = []
    item_rows = []
    file_rows = []
    review_rows = []

    for result in results:
        summary_rows.append({
            "Legend_ID": result.subject_name,
            "Trial": result.trial_id,
            "Front_file": result.front_file,
            "Side_file": result.side_file,
            "EMG_file": result.emg_file,
            "Grip_Type_Candidate": result.grip_type_candidate,
            "Motion_Type_Candidate": result.motion_type_candidate,
            "AI_Coaching": result.ai_coaching,
            "Analysis_Date": result.analysis_date,
            "Analyzer_Version": result.analyzer_version,
            "Notes": result.notes,
        })
        file_rows.append({
            "Legend_ID": result.subject_name,
            "Trial": result.trial_id,
            "Front_Status": result.front_status.status,
            "Front_Selected": result.front_status.selected_path,
            "Side_Status": result.side_status.status,
            "Side_Selected": result.side_status.selected_path,
        })
        for item in result.items:
            row = asdict(item)
            row.update({"Legend_ID": result.subject_name, "Trial": result.trial_id})
            item_rows.append(row)
            review_rows.append({
                "Legend_ID": result.subject_name,
                "Trial": result.trial_id,
                "Item": item.item,
                "Researcher_Confirmed": item.researcher_confirmed,
                "Correction_Notes": item.correction_notes,
                "Final_Result": item.final_result,
            })

    with pd.ExcelWriter(destination, engine="openpyxl") as writer:
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Analysis_Summary", index=False)
        pd.DataFrame(item_rows).to_excel(writer, sheet_name="Legend_10_Items", index=False)
        pd.DataFrame(review_rows).to_excel(writer, sheet_name="Review_Log", index=False)
        pd.DataFrame(file_rows).to_excel(writer, sheet_name="File_Status", index=False)
        pd.DataFrame([], columns=["Grip_Type", "Definition", "Notes"]).to_excel(writer, sheet_name="Grip_Types", index=False)
        pd.DataFrame([], columns=["Motion_Type", "Definition", "Notes"]).to_excel(writer, sheet_name="Motion_Types", index=False)
        pd.DataFrame([], columns=["Condition", "Coaching_Text", "Notes"]).to_excel(writer, sheet_name="Coaching_Library", index=False)
    return destination


def write_log(message: str, log_dir: Path = LOGS_DIR) -> Path:
    ensure_output_directories()
    destination = log_dir / f"ema_legend_analyzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    destination.write_text(f"{datetime.now().isoformat(timespec='seconds')} {ANALYZER_VERSION} {message}\n", encoding="utf-8")
    return destination
