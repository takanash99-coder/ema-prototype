
from __future__ import annotations

import base64
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import streamlit as st
import streamlit.components.v1 as components

from config import MASTER_FILE, RESULTS_DIR, SAMPLE_MARKED_VIDEO, SAMPLE_POSE_JSON, ensure_output_directories
from master_loader import MasterLoadError, load_master
from result_writer import write_log

st.set_page_config(page_title="EMA", layout="centered")

MARKER_LABELS = {
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

T = {
    "ema": "EMA",
    "name": "Expert Motion Analyzer",
    "target": "for Endotracheal Intubation",
    "system": "AI-assisted Laryngoscopy Skill Analysis System",
    "analyze": "Analyze",
    "analyze_ja": "\u52d5\u4f5c\u3092\u89e3\u6790\u3059\u308b",
    "review": "Review",
    "review_ja": "\u89e3\u6790\u7d50\u679c\u3092\u898b\u308b",
    "recording": "Recording",
    "recording_ja": "\u30c7\u30fc\u30bf\u3092\u8a18\u9332\u3059\u308b",
    "help": "\uff1f \u4f7f\u7528\u65b9\u6cd5",
    "back": "\u2190 \u623b\u308b",
    "sample": "\u30b5\u30f3\u30d7\u30eb\u52d5\u753b\u3067\u8a66\u3059",
    "select": "\u52d5\u753b\u3092\u9078\u629e",
    "marking_result": "\u30de\u30fc\u30ad\u30f3\u30b0\u7d50\u679c",
    "loading": "\u89e3\u6790\u6e08\u307f\u30c7\u30fc\u30bf\u3092\u8aad\u307f\u8fbc\u307f\u4e2d",
    "start_marking": "\u30de\u30fc\u30ad\u30f3\u30b0\u958b\u59cb",
    "marking_now": "\u30de\u30fc\u30ad\u30f3\u30b0\u4e2d...",
    "save": "\u7d50\u679c\u3092\u4fdd\u5b58",
    "saved": "\u4fdd\u5b58\u3057\u307e\u3057\u305f",
    "developing": "\u958b\u767a\u4e2d\u3067\u3059",
    "usage_title": "\u4f7f\u7528\u65b9\u6cd5",
    "analysis_title": "\u52d5\u4f5c\u89e3\u6790",
    "status": "\u30de\u30fc\u30ad\u30f3\u30b0\u72b6\u614b",
}

st.markdown("""
<style>
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {display:none!important;}
[data-testid="stMainBlockContainer"], .block-container {padding:18px 16px 34px!important; max-width:780px!important;}
.stApp {background:linear-gradient(180deg,#f7fbff 0%,#edf6ff 100%); color:#132238;}
.ema-brand {text-align:center; padding:10px 0 22px;}
.ema-logo {font-size:64px; line-height:1; font-weight:950; letter-spacing:0; color:#0b66c3; margin:0;}
.ema-name {font-size:22px; font-weight:850; margin:8px 0 4px; color:#172a46;}
.ema-sub {font-size:14px; font-weight:750; color:#64758b; margin:2px 0;}
.ema-menu-card, .ema-panel {background:#fff; border:1px solid rgba(18,104,216,.12); border-radius:20px; box-shadow:0 16px 34px rgba(31,86,141,.10); margin:14px 0; padding:22px;}
.ema-menu-card {padding:0; overflow:hidden;}
.ema-page-title {font-size:34px; font-weight:950; text-align:center; margin:10px 0 18px; color:#10233d;}
.ema-help-text {font-size:17px; line-height:1.8; color:#2b3f58;}
.ema-rate-row {display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #e8f1fb; padding:12px 2px; font-size:18px;}
.ema-rate-row strong {font-size:20px; color:#0b66c3;}
.ema-note {font-size:13px; color:#6c7d8f; text-align:center; margin-top:12px;}
.ema-path {font-family:Consolas,monospace; font-size:12px; color:#52677e; word-break:break-all;}
.stButton>button {width:100%; min-height:58px; border-radius:17px; font-size:20px; font-weight:900; border:1px solid rgba(18,104,216,.15); white-space:pre-line;}
.stButton>button[kind="primary"] {background:linear-gradient(135deg,#20b8ef,#1268d8); border:0; color:#fff;}
div[data-testid="stFileUploader"] section {border-radius:18px; border-color:#cde3fb;}
@media (max-width: 520px) {.ema-logo{font-size:52px}.ema-page-title{font-size:29px}.stButton>button{font-size:18px}}
</style>
""", unsafe_allow_html=True)


def goto(screen: str) -> None:
    st.session_state.screen = screen
    st.rerun()


def back_button(target: str) -> None:
    if st.button(T["back"]):
        goto(target)


def brand() -> None:
    html = (
        '<div class="ema-brand">'
        f'<div class="ema-logo">{T["ema"]}</div>'
        f'<div class="ema-name">{T["name"]}</div>'
        f'<div class="ema-sub">{T["target"]}</div>'
        f'<div class="ema-sub">{T["system"]}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def menu_button(key: str, english: str, japanese: str, target: str) -> None:
    st.markdown('<div class="ema-menu-card">', unsafe_allow_html=True)
    if st.button(f"{english}\n{japanese}", key=key, type="primary"):
        goto(target)
    st.markdown('</div>', unsafe_allow_html=True)


def load_master_count() -> int | None:
    try:
        _, records, _ = load_master(MASTER_FILE)
        return len(records)
    except MasterLoadError:
        return None


def read_pose_summary(pose_json: Path) -> SimpleNamespace:
    data = json.loads(pose_json.read_text(encoding="utf-8"))
    return SimpleNamespace(
        source_video=data.get("source_video", ""),
        marked_video=data.get("marked_video", str(SAMPLE_MARKED_VIDEO)),
        pose_json=str(pose_json),
        fps=float(data.get("fps", 0.0)),
        frame_count=int(data.get("frame_count", 0)),
        processed_frames=int(data.get("processed_frames", 0)),
        duration_sec=float(data.get("duration_sec", 0.0)),
        detection_rates=data.get("detection_rates", {}),
        analysis_date=data.get("analysis_date", ""),
        analyzer_version=data.get("analyzer_version", ""),
    )


def load_sample_result() -> SimpleNamespace:
    if not SAMPLE_MARKED_VIDEO.exists() or not SAMPLE_POSE_JSON.exists():
        raise FileNotFoundError("sample_unavailable")
    result = read_pose_summary(SAMPLE_POSE_JSON)
    result.marked_video = str(SAMPLE_MARKED_VIDEO)
    return result


@st.cache_data(show_spinner=False)
def video_base64(path_text: str) -> str:
    return base64.b64encode(Path(path_text).read_bytes()).decode("ascii")


def video_player(path_text: str) -> None:
    encoded = video_base64(path_text)
    components.html(
        f"""
        <div style="width:100%; margin:0 auto;">
          <video id="emaVideo" controls playsinline preload="metadata" style="width:100%; border-radius:18px; box-shadow:0 16px 34px rgba(31,86,141,.14); background:#000;">
            <source src="data:video/mp4;base64,{encoded}" type="video/mp4">
          </video>
          <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-top:12px;">
            <button onclick="document.getElementById('emaVideo').currentTime=0;document.getElementById('emaVideo').play();" style="height:42px;border-radius:12px;border:1px solid #cfe2f7;background:#fff;font-weight:800;">最初から</button>
            <button onclick="document.getElementById('emaVideo').playbackRate=0.5;" style="height:42px;border-radius:12px;border:1px solid #cfe2f7;background:#fff;font-weight:800;">0.5x</button>
            <button onclick="document.getElementById('emaVideo').playbackRate=1.0;" style="height:42px;border-radius:12px;border:1px solid #cfe2f7;background:#fff;font-weight:800;">1.0x</button>
            <button onclick="document.getElementById('emaVideo').playbackRate=1.5;" style="height:42px;border-radius:12px;border:1px solid #cfe2f7;background:#fff;font-weight:800;">1.5x</button>
          </div>
        </div>
        """,
        height=560,
        scrolling=False,
    )


def detection_rates(result: SimpleNamespace) -> None:
    st.subheader(T["status"])
    for key in ["head", "left_shoulder", "left_elbow", "left_wrist", "right_shoulder", "torso_center"]:
        if not result.detection_rates:
            st.info("Pose JSONがないため検出率は表示できません")
            return
        label = MARKER_LABELS.get(key, key)
        rate = float(result.detection_rates.get(key, 0.0)) * 100
        st.markdown(f'<div class="ema-rate-row"><span>{label}</span><strong>{rate:.0f}%</strong></div>', unsafe_allow_html=True)


def save_summary(result: SimpleNamespace) -> Path:
    summary = {
        "source_video": result.source_video,
        "marked_video": result.marked_video,
        "pose_json": result.pose_json,
        "fps": result.fps,
        "frame_count": result.frame_count,
        "processed_frames": result.processed_frames,
        "duration_sec": result.duration_sec,
        "detection_rates": result.detection_rates,
        "analysis_date": result.analysis_date,
        "analyzer_version": result.analyzer_version,
    }
    source = Path(result.pose_json)
    ensure_output_directories()
    destination = RESULTS_DIR / f"{source.stem}_ui_summary.json"
    destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        write_log(f"ui summary saved summary={destination}")
    except OSError:
        pass
    return destination


if "screen" not in st.session_state:
    st.session_state.screen = "home"

screen = st.session_state.screen

if screen == "home":
    brand()
    menu_button("menu_analyze", T["analyze"], T["analyze_ja"], "analyze")
    menu_button("menu_review", T["review"], T["review_ja"], "review")
    menu_button("menu_recording", T["recording"], T["recording_ja"], "recording")
    if st.button(T["help"]):
        goto("usage")

elif screen == "usage":
    back_button("home")
    st.markdown(f'<div class="ema-page-title">{T["usage_title"]}</div>', unsafe_allow_html=True)
    st.markdown('<div class="ema-panel ema-help-text">', unsafe_allow_html=True)
    st.markdown("""
EMAは、気管挿管時の身体動作を動画から解析するシステムです。

1. Analyzeから動画を選択
2. マーキング結果を確認
3. 動作解析結果を確認
4. AI Coachingを確認

Reviewでは過去の解析結果を確認します。Recordingは研究・教師データの記録に使用します。
""")
    st.markdown('</div>', unsafe_allow_html=True)

elif screen == "analyze":
    back_button("home")
    st.markdown(f'<div class="ema-page-title">{T["analysis_title"]}<br><span style="font-size:20px;color:#66788d">Analyze</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="ema-panel">', unsafe_allow_html=True)
    if st.button(T["sample"], type="primary"):
        goto("sample_loading")
    uploaded = st.file_uploader(T["select"], type=["mp4", "mov", "mts"])
    if uploaded is not None:
        temp_dir = Path(tempfile.gettempdir()) / "ema_legend_analyzer_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        uploaded_path = temp_dir / uploaded.name
        uploaded_path.write_bytes(uploaded.getbuffer())
        st.session_state.uploaded_video_path = str(uploaded_path)
        st.video(str(uploaded_path))
        if st.button(T["start_marking"]):
            goto("custom_analyzing")
    st.markdown('</div>', unsafe_allow_html=True)

elif screen == "sample_loading":
    back_button("analyze")
    st.markdown(f'<div class="ema-page-title">{T["loading"]}</div>', unsafe_allow_html=True)
    try:
        st.session_state.pose_result = load_sample_result()
    except FileNotFoundError:
        st.warning("サンプル動画は現在この環境では利用できません")
        st.caption("ローカル研究環境では解析済みサンプルが存在する場合のみ表示されます。")
        st.stop()
    except json.JSONDecodeError:
        st.error("Pose JSONを読み込めませんでした。JSON形式を確認してください。")
        st.stop()
    goto("marking_result")

elif screen == "custom_analyzing":
    back_button("analyze")
    st.markdown(f'<div class="ema-page-title">{T["marking_now"]}</div>', unsafe_allow_html=True)
    path = st.session_state.get("uploaded_video_path", "")
    if not path or not Path(path).exists():
        st.warning("動画が見つかりません")
        st.stop()
    progress = st.progress(0)
    status = st.empty()

    def update_progress(done: int, total: int) -> None:
        ratio = min(1.0, done / total) if total else 0.0
        progress.progress(ratio)
        status.write(f"{int(ratio * 100)}%")

    try:
        from pose_analyzer import analyze_pose

        result = analyze_pose(path, progress_callback=update_progress)
        st.session_state.pose_result = result
        try:
            write_log(f"ui custom pose marking completed source={result.source_video} marked={result.marked_video}")
        except OSError:
            pass
    except ImportError:
        st.error("この環境ではPose解析を利用できません。MediaPipeとOpenCVの導入状況を確認してください。")
        st.stop()
    except FileNotFoundError as error:
        if "pose_landmarker_lite.task" in str(error):
            st.error("Poseモデルが見つからないため、マーキング解析を実行できません。")
        else:
            st.error("解析に必要なファイルが見つかりません。")
        st.stop()
    except Exception:
        st.error("マーキング解析を実行できませんでした。入力動画と実行環境を確認してください。")
        st.stop()
    goto("marking_result")

elif screen == "marking_result":
    back_button("analyze")
    st.markdown(f'<div class="ema-page-title">{T["marking_result"]}</div>', unsafe_allow_html=True)
    result = st.session_state.get("pose_result")
    if result is None:
        st.warning("結果がありません")
        st.stop()
    st.markdown('<div class="ema-panel">', unsafe_allow_html=True)
    if result.marked_video and Path(result.marked_video).exists():
        video_player(result.marked_video)
    else:
        st.warning("サンプル動画は現在この環境では利用できません")
    detection_rates(result)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="ema-panel">', unsafe_allow_html=True)
    if st.button("動作解析へ"):
        st.info(T["developing"])
    if st.button(T["save"], type="primary"):
        st.session_state.saved_summary_path = str(save_summary(result))
    if "saved_summary_path" in st.session_state:
        st.success(T["saved"])
        st.markdown(f'<div class="ema-path">{st.session_state.saved_summary_path}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif screen == "review":
    back_button("home")
    st.markdown(f'<div class="ema-page-title">{T["review"]}<br><span style="font-size:20px;color:#66788d">{T["review_ja"]}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="ema-panel">', unsafe_allow_html=True)
    st.info("Review機能は開発中です")
    st.markdown('</div>', unsafe_allow_html=True)

elif screen == "recording":
    back_button("home")
    st.markdown(f'<div class="ema-page-title">{T["recording"]}<br><span style="font-size:20px;color:#66788d">{T["recording_ja"]}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="ema-panel">', unsafe_allow_html=True)
    st.info("Recording機能は開発中です")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.session_state.screen = "home"
    st.rerun()
