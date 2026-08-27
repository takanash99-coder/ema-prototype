from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config import MASTER_DEFAULT_COLUMNS, MASTER_FILE
from models import TrialRecord


class MasterLoadError(RuntimeError):
    pass


def _clean_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _resolve_column(columns: list[str], aliases: list[str]) -> str | None:
    normalized = {str(column).strip(): column for column in columns}
    lowered = {str(column).strip().lower(): column for column in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
        if alias.lower() in lowered:
            return lowered[alias.lower()]
    return None


def load_master(master_path: str | Path = MASTER_FILE) -> tuple[pd.DataFrame, list[TrialRecord], dict[str, str]]:
    path = Path(master_path)
    if not path.exists():
        raise MasterLoadError(f"Master file not found: {path}")
    if path.suffix.lower() not in {".xlsx", ".xls"}:
        raise MasterLoadError(f"Unsupported master file format: {path.suffix}")

    try:
        df = pd.read_excel(path)
    except Exception as error:
        raise MasterLoadError(f"Failed to read master file: {error}") from error

    columns = [str(column).strip() for column in df.columns]
    column_map: dict[str, str] = {}
    for key, aliases in MASTER_DEFAULT_COLUMNS.items():
        resolved = _resolve_column(columns, aliases)
        if resolved is not None:
            column_map[key] = resolved

    records: list[TrialRecord] = []
    for row_number, row in df.iterrows():
        raw = {str(column): _clean_cell(row[column]) for column in df.columns}
        exclude_text = _clean_cell(row[column_map["exclude_flag"]]) if "exclude_flag" in column_map else ""
        exclude_flag = exclude_text.lower() in {"1", "true", "yes", "y", "exclude", "excluded", "??"}
        records.append(
            TrialRecord(
                subject_name=_clean_cell(row[column_map["subject_name"]]) if "subject_name" in column_map else "",
                trial_id=_clean_cell(row[column_map["trial_id"]]) if "trial_id" in column_map else str(row_number + 1),
                front_video=_clean_cell(row[column_map["front_video"]]) if "front_video" in column_map else "",
                side_video=_clean_cell(row[column_map["side_video"]]) if "side_video" in column_map else "",
                emg_file=_clean_cell(row[column_map["emg_file"]]) if "emg_file" in column_map else "",
                photo_file=_clean_cell(row[column_map["photo_file"]]) if "photo_file" in column_map else "",
                exclude_flag=exclude_flag,
                remarks=_clean_cell(row[column_map["remarks"]]) if "remarks" in column_map else "",
                row_index=int(row_number),
                raw=raw,
            )
        )

    return df, records, column_map
