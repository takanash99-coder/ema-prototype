from __future__ import annotations

import base64
import json
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import streamlit as st
import streamlit.components.v1 as components

from config import ASSETS_DIR, MASTER_FILE, RESULTS_DIR, SAMPLE_MARKED_VIDEO, SAMPLE_POSE_JSON, ensure_output_directories
from master_loader import MasterLoadError, load_master
from result_writer import write_log

EMA_ICON_IMAGE = ASSETS_DIR / "ema_icon.png"
WEB_APP_NAME = "EMA"
STATIC_ICON_BASE = "/app/static"
PUBLIC_ICON_BASE = "https://raw.githubusercontent.com/takanash99-coder/ema-prototype/main/static"
st.set_page_config(page_title=WEB_APP_NAME, page_icon=str(EMA_ICON_IMAGE), layout="centered")

DEMO_CAMERA_GUIDE_IMAGE = ASSETS_DIR / "demo_camera_guide_2.png"
DEMO_MARKING_RESULT_IMAGE = ASSETS_DIR / "demo_marking_result.png"

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
    "shoot_analyze": "\U0001F4F7 \u64ae\u5f71\u3057\u3066\u89e3\u6790",
    "upload_analyze": "\U0001F4C1 \u52d5\u753b\u304b\u3089\u89e3\u6790",
    "marking_result": "\u30de\u30fc\u30ad\u30f3\u30b0\u7d50\u679c",
    "loading": "\u89e3\u6790\u6e08\u307f\u30c7\u30fc\u30bf\u3092\u8aad\u307f\u8fbc\u307f\u4e2d",
    "start_marking": "\u30de\u30fc\u30ad\u30f3\u30b0\u958b\u59cb",
    "marking_now": "\u30de\u30fc\u30ad\u30f3\u30b0\u4e2d...",
    "save": "\u7d50\u679c\u3092\u4fdd\u5b58",
    "saved": "\u4fdd\u5b58\u3057\u307e\u3057\u305f",
    "developing": "\u958b\u767a\u4e2d\u3067\u3059",
    "usage_title": "\u4f7f\u7528\u65b9\u6cd5",
    "analysis_title": "\u52d5\u4f5c\u89e3\u6790",
    "history": "\u89e3\u6790\u5c65\u6b74",
    "history_sub": "\u904e\u53bb\u306e\u89e3\u6790\u7d50\u679c\u3092\u78ba\u8a8d\u3059\u308b",
    "recording_title": "\u52d5\u753b\u64ae\u5f71",
    "status": "\u30de\u30fc\u30ad\u30f3\u30b0\u72b6\u614b",
}

st.markdown("""
<style>
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {display:none!important;}
[data-testid="stMainBlockContainer"], .block-container {padding:22px 20px 38px!important; max-width:980px!important;}
.stApp {background:radial-gradient(circle at 50% 0%, rgba(51,170,245,.20), transparent 34%), linear-gradient(180deg,#fafdff 0%,#edf7ff 58%,#e7f3ff 100%); color:#132238;}
.stApp::after {content:""; position:fixed; left:0; right:0; bottom:0; height:180px; pointer-events:none; opacity:.55; background:repeating-linear-gradient(160deg, transparent 0 28px, rgba(22,116,210,.08) 29px 31px, transparent 32px 58px); mask-image:linear-gradient(transparent, #000);}
.ema-brand {text-align:center; padding:18px 0 24px;}
.ema-brand-icon {display:block; width:min(168px, 34vw); height:auto; margin:0 auto 14px; border-radius:28px; box-shadow:0 18px 42px rgba(12,40,86,.18);}
.ema-logo {font-size:76px; line-height:1; font-weight:950; letter-spacing:0; color:#0b66c3; margin:0; text-shadow:0 10px 24px rgba(11,102,195,.13);}
.ema-name {font-size:24px; font-weight:900; margin:10px 0 5px; color:#10233d;}
.ema-sub {font-size:14px; font-weight:760; color:#64758b; margin:2px 0;}
.ema-page-title {font-size:36px; font-weight:950; text-align:center; margin:12px 0 22px; color:#10233d; line-height:1.24;}
.ema-page-title span {font-size:20px; color:#66788d;}
.ema-panel {background:#fff; border:1px solid rgba(18,104,216,.12); border-radius:22px; box-shadow:0 16px 34px rgba(31,86,141,.10); margin:16px 0; padding:22px;}
.ema-help-text {font-size:17px; line-height:1.8; color:#2b3f58;}
.ema-rate-row {display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #e8f1fb; padding:12px 2px; font-size:18px;}
.ema-rate-row strong {font-size:20px; color:#0b66c3;}
.ema-note {font-size:13px; color:#6c7d8f; text-align:center; margin-top:12px;}
.ema-path {font-family:Consolas,monospace; font-size:12px; color:#52677e; word-break:break-all;}
.ema-purpose {max-width:640px; margin:0 auto 26px; text-align:center; font-size:20px; line-height:1.7; font-weight:850; color:#1b385b;}
.ema-flow {display:grid; grid-template-columns:1fr auto 1fr auto 1fr; align-items:stretch; gap:10px; margin:2px auto 22px; max-width:760px;}
.ema-flow-step {background:rgba(255,255,255,.78); border:1px solid rgba(18,104,216,.13); border-radius:18px; padding:15px 12px; text-align:center; box-shadow:0 12px 26px rgba(31,86,141,.08);}
.ema-flow-number {font-size:13px; font-weight:950; color:#0b66c3; margin-bottom:3px;}
.ema-flow-title {font-size:18px; font-weight:950; color:#132238; margin-bottom:4px;}
.ema-flow-text {font-size:12px; font-weight:760; line-height:1.45; color:#64758b;}
.ema-flow-arrow {display:flex; align-items:center; justify-content:center; font-size:24px; font-weight:950; color:#74b6ec;}
.ema-image-frame {background:#fff; border:1px solid rgba(18,104,216,.12); border-radius:24px; box-shadow:0 18px 36px rgba(31,86,141,.12); padding:12px; margin:12px auto 18px;}
.ema-image-frame img {display:block; width:100%; height:auto; border-radius:18px;}
.ema-demo-tag {display:inline-block; font-size:12px; font-weight:900; letter-spacing:.08em; color:#0b66c3; background:#eaf5ff; border:1px solid #cce8ff; border-radius:999px; padding:5px 12px; margin:0 auto 10px;}
.ema-center {text-align:center;}
.stButton>button {width:100%; min-height:66px; border-radius:22px; font-size:20px; font-weight:900; border:1px solid rgba(18,104,216,.13); white-space:pre-line; box-shadow:0 16px 30px rgba(31,86,141,.11); transition:transform .14s ease, box-shadow .14s ease, border-color .14s ease;}
.stButton>button:hover {transform:translateY(-1px); box-shadow:0 20px 34px rgba(31,86,141,.16); border-color:rgba(18,104,216,.24);}
.stButton>button[kind="primary"] {background:linear-gradient(135deg,#25c7f3,#1268d8); border:0; color:#fff;}
.stButton>button[kind="secondary"] {background:#fff; color:#15304f;}
.st-key-home_analyze button, .st-key-home_review button, .st-key-home_recording button,
.st-key-shoot_analyze button, .st-key-upload_analyze button, .st-key-analysis_history button {min-height:154px!important; font-size:19px!important; border-radius:25px!important; text-align:left!important; padding:20px 20px!important;}
.st-key-home_analyze button {background:linear-gradient(135deg,#21c8f4,#1270de)!important; color:#fff!important; border:0!important;}
.st-key-home_review button {background:linear-gradient(135deg,#0f4e96,#0b2f66)!important; color:#fff!important; border:0!important;}
.st-key-home_recording button {background:linear-gradient(135deg,#1678de,#6d54d8)!important; color:#fff!important; border:0!important;}
.st-key-shoot_analyze button {background:linear-gradient(135deg,#25c7f3,#1268d8)!important; color:#fff!important; border:0!important;}
.st-key-upload_analyze button {background:#fff!important; color:#15304f!important;}
.st-key-analysis_history button {background:linear-gradient(135deg,#f7fbff,#eef6ff)!important; color:#15304f!important;}
.st-key-home_help button {min-height:38px!important; font-size:14px!important; box-shadow:none!important; border:0!important; background:transparent!important; color:#6c7d8f!important;}
.st-key-shutter_button button {width:96px!important; height:96px!important; min-height:96px!important; border-radius:999px!important; margin:6px auto 0!important; font-size:46px!important; line-height:1!important; display:block!important; box-shadow:0 18px 34px rgba(18,104,216,.22)!important;}
.st-key-motion_rec_start button {width:138px!important; height:138px!important; min-height:138px!important; border-radius:999px!important; margin:10px auto 18px!important; font-size:25px!important; line-height:1.15!important; display:block!important; background:linear-gradient(135deg,#ef4444,#b91c1c)!important;}
.st-key-coaching_start button {max-width:520px!important; min-height:82px!important; margin:0 auto 12px!important; display:block!important; background:linear-gradient(135deg,#25c7f3,#1268d8)!important; color:#fff!important; border:0!important; text-align:center!important;}
.st-key-motion_recording_home button, .st-key-result_home button {box-shadow:none!important;}
div[data-testid="stFileUploader"] section {border-radius:18px; border-color:#cde3fb; background:#fff;}
@media (max-width: 620px) {
  [data-testid="stMainBlockContainer"], .block-container {padding:16px 16px 30px!important;}
  .ema-logo{font-size:56px}.ema-brand-icon{width:min(138px, 42vw); border-radius:24px}.ema-page-title{font-size:30px}.stButton>button{font-size:18px; min-height:60px;}
  .ema-purpose{font-size:17px; line-height:1.65; margin-bottom:20px;}
  .ema-flow{grid-template-columns:1fr; gap:8px; margin-bottom:18px;}
  .ema-flow-arrow{display:none;}
  .ema-flow-step{padding:13px 12px;}
  .st-key-home_analyze button, .st-key-home_review button, .st-key-home_recording button,
  .st-key-shoot_analyze button, .st-key-upload_analyze button, .st-key-analysis_history button {min-height:92px!important; font-size:18px!important; padding:16px 18px!important;}
  .st-key-motion_rec_start button {width:120px!important; height:120px!important; min-height:120px!important;}
}
</style>
""", unsafe_allow_html=True)


def goto(screen: str) -> None:
    st.session_state.screen = screen
    st.rerun()


def back_button(target: str) -> None:
    if st.button(T["back"]):
        goto(target)


def brand() -> None:
    if EMA_ICON_IMAGE.exists():
        encoded = base64.b64encode(EMA_ICON_IMAGE.read_bytes()).decode("ascii")
        brand_mark = f'<img class="ema-brand-icon" src="data:image/png;base64,{encoded}" alt="EMA Expert Motion Analyzer">'
        brand_name = ""
    else:
        brand_mark = f'<div class="ema-logo">{T["ema"]}</div>'
        brand_name = f'<div class="ema-name">{T["name"]}</div>'
    html = (
        '<div class="ema-brand">'
        f'{brand_mark}'
        f'{brand_name}'
        f'<div class="ema-sub">{T["target"]}</div>'
        f'<div class="ema-sub">{T["system"]}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def page_title(japanese: str, english: str) -> None:
    st.markdown(f'<div class="ema-page-title">{japanese}<br><span>{english}</span></div>', unsafe_allow_html=True)


def mobile_icon_tags() -> None:
    head_markup = f"""
    <script>
    (() => {{
      const doc = window.parent.document;
      const origin = window.parent.location.origin;
      const iconBase = `${{origin}}{STATIC_ICON_BASE}`;
      const publicIconBase = '{PUBLIC_ICON_BASE}';
      const ensureLink = (rel, href, attrs = {{}}) => {{
        let link = doc.head.querySelector(`link[rel="${{rel}}"]`);
        if (!link) {{
          link = doc.createElement('link');
          link.setAttribute('rel', rel);
          doc.head.appendChild(link);
        }}
        link.setAttribute('href', href);
        Object.entries(attrs).forEach(([key, value]) => link.setAttribute(key, value));
      }};
      const ensureMeta = (name, content) => {{
        let meta = doc.head.querySelector(`meta[name="${{name}}"]`);
        if (!meta) {{
          meta = doc.createElement('meta');
          meta.setAttribute('name', name);
          doc.head.appendChild(meta);
        }}
        meta.setAttribute('content', content);
      }};
      doc.title = '{WEB_APP_NAME}';
      ensureLink('icon', `${{publicIconBase}}/favicon.ico`, {{ sizes: 'any' }});
      ensureLink('shortcut icon', `${{publicIconBase}}/favicon.ico`);
      ensureLink('apple-touch-icon', `${{publicIconBase}}/apple-touch-icon.png`, {{ sizes: '180x180' }});
      ensureLink('manifest', `${{iconBase}}/manifest.json`);
      ensureMeta('apple-mobile-web-app-title', '{WEB_APP_NAME}');
      ensureMeta('application-name', '{WEB_APP_NAME}');
      ensureMeta('mobile-web-app-capable', 'yes');
      ensureMeta('apple-mobile-web-app-capable', 'yes');
      ensureMeta('theme-color', '#1268d8');
    }})();
    </script>
    """
    components.html(head_markup, height=0, width=0)


mobile_icon_tags()


@st.cache_data(show_spinner=False)
def image_data_uri(path_text: str) -> str:
    path = Path(path_text)
    suffix = path.suffix.lower().lstrip(".") or "png"
    mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{mime};base64,{encoded}"


def show_demo_image(path: Path, alt: str) -> None:
    if not path.exists():
        st.warning("デモ画像が見つかりません")
        st.markdown(f'<div class="ema-path">{path}</div>', unsafe_allow_html=True)
        return
    src = image_data_uri(str(path))
    st.markdown(
        f'<div class="ema-image-frame"><img src="{src}" alt="{alt}"></div>',
        unsafe_allow_html=True,
    )


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
    st.markdown('<div class="ema-purpose">気管挿管の動作を可視化し、<br>熟練者の動きから学ぶモーションコーチングAI</div>', unsafe_allow_html=True)
    home_cols = st.columns(3, gap="medium")
    with home_cols[0]:
        if st.button(f'{T["analyze"]}\n{T["analyze_ja"]}\n撮影した動作をAIで解析', key="home_analyze", type="primary"):
            goto("analyze")
    with home_cols[1]:
        if st.button(f'{T["review"]}\n{T["review_ja"]}\n解析結果・コーチングを確認', key="home_review"):
            goto("review")
    with home_cols[2]:
        if st.button(f'{T["recording"]}\n{T["recording_ja"]}\n技能データを記録', key="home_recording"):
            goto("recording")
    if st.button(T["help"], key="home_help"):
        goto("usage")

elif screen == "usage":
    back_button("home")
    page_title(T["usage_title"], "Usage")
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
    page_title(T["analysis_title"], "Analyze")
    st.markdown("""
    <div class="ema-flow">
      <div class="ema-flow-step"><div class="ema-flow-number">01</div><div class="ema-flow-title">撮影</div><div class="ema-flow-text">位置を合わせて静止画を撮影</div></div>
      <div class="ema-flow-arrow">→</div>
      <div class="ema-flow-step"><div class="ema-flow-number">02</div><div class="ema-flow-title">確認</div><div class="ema-flow-text">マーキング結果を確認</div></div>
      <div class="ema-flow-arrow">→</div>
      <div class="ema-flow-step"><div class="ema-flow-number">03</div><div class="ema-flow-title">解析</div><div class="ema-flow-text">動画撮影して動作を解析</div></div>
    </div>
    """, unsafe_allow_html=True)
    analyze_cols = st.columns(3, gap="medium")
    with analyze_cols[0]:
        if st.button(f'{T["shoot_analyze"]}\nその場で撮影して解析する', key="shoot_analyze", type="primary"):
            goto("camera_guide")
    with analyze_cols[1]:
        if st.button(f'{T["upload_analyze"]}\n保存済みの動画を使用する', key="upload_analyze"):
            goto("upload_analyze")
    with analyze_cols[2]:
        if st.button(f'{T["history"]}\n{T["history_sub"]}', key="analysis_history"):
            goto("review")

elif screen == "camera_guide":
    back_button("analyze")
    page_title("撮影ガイド", "Camera Guide")
    show_demo_image(DEMO_CAMERA_GUIDE_IMAGE, "Camera guide")
    if st.button("●", key="shutter_button", type="primary"):
        goto("demo_analyzing")

elif screen == "demo_analyzing":
    page_title("動作を解析しています…", "Analyzing")
    progress = st.progress(0)
    for value in (22, 48, 74, 100):
        time.sleep(0.18)
        progress.progress(value)
    time.sleep(0.25)
    goto("demo_result")

elif screen == "demo_result":
    page_title("解析結果", "Analysis Result")
    st.markdown('<div class="ema-center"><span class="ema-demo-tag">DEMO</span></div>', unsafe_allow_html=True)
    show_demo_image(DEMO_MARKING_RESULT_IMAGE, "Demo marking result")
    if st.button("\U0001F3A5 動画撮影へ", key="to_motion_recording", type="primary"):
        goto("motion_recording")
    if st.button("\U0001F4F7 もう一度撮影", key="shoot_again"):
        goto("camera_guide")
    if st.button("\U0001F3E0 ホームへ", key="result_home"):
        goto("home")

elif screen == "motion_recording":
    back_button("demo_result")
    page_title(T["recording_title"], "Motion Recording")
    st.markdown('<div class="ema-purpose">撮影位置を変えずに、気管挿管を実施してください</div>', unsafe_allow_html=True)
    if st.button("● REC\n撮影開始", key="motion_rec_start", type="primary"):
        st.info("動画撮影機能はPrototypeでは準備中です")
    if st.button("コーチング開始\n撮影した動画をAIコーチングで解析します", key="coaching_start", type="primary"):
        goto("ai_coaching")
    if st.button("ホームへ", key="motion_recording_home"):
        goto("home")

elif screen == "ai_coaching":
    page_title("AIコーチング", "AI Coaching")
    st.markdown('<div class="ema-center"><span class="ema-demo-tag">Prototype</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="ema-panel ema-help-text">撮影した動作を解析し、<br>熟練者の動作特性と比較してコーチングを行います。<br><br><strong>AIコーチング機能は現在開発中です。</strong></div>', unsafe_allow_html=True)
    if st.button("ホームへ戻る", key="ai_coaching_home", type="primary"):
        goto("home")

elif screen == "upload_analyze":
    back_button("analyze")
    page_title(T["select"], "Video Upload")
    uploaded = st.file_uploader(T["select"], type=["mp4", "mov", "mts"])
    if uploaded is not None:
        temp_dir = Path(tempfile.gettempdir()) / "ema_legend_analyzer_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        uploaded_path = temp_dir / uploaded.name
        uploaded_path.write_bytes(uploaded.getbuffer())
        st.session_state.uploaded_video_path = str(uploaded_path)
        st.video(str(uploaded_path))
        if st.button(T["start_marking"], key="start_uploaded_marking", type="primary"):
            goto("custom_analyzing")

elif screen == "sample_loading":
    back_button("analyze")
    page_title(T["loading"], "Loading")
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
    back_button("upload_analyze")
    page_title(T["marking_now"], "Marking")
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
    page_title(T["marking_result"], "Marking Result")
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
    page_title(T["review_ja"], T["review"])
    st.markdown('<div class="ema-panel">', unsafe_allow_html=True)
    st.info("Review機能は開発中です")
    st.markdown('</div>', unsafe_allow_html=True)

elif screen == "recording":
    back_button("home")
    page_title(T["recording_ja"], T["recording"])
    st.markdown('<div class="ema-panel">', unsafe_allow_html=True)
    st.info("Recording機能は開発中です")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.session_state.screen = "home"
    st.rerun()
