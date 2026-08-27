# EMA Prototype

EMA Prototype is the development version of Expert Motion Analyzer.

EMA supports a future workflow for endotracheal intubation skill analysis:

- Analyze / 動作を解析する
- Review / 解析結果を見る
- Recording / データを記録する

This repository is intended to contain source code required to rebuild the EMA Prototype application. Real research data, videos, analysis outputs, credentials, and local-only files must not be committed.

## Prototype UI

The start screen provides three large entries:

- Analyze / 動作を解析する
- Review / 解析結果を見る
- Recording / データを記録する

The app also includes a compact usage screen opened from `？ 使用方法`.

## Local Development

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

The current local prototype can read local sample analysis outputs when they are available. Public deployments should use anonymized demo assets instead of real research-derived files.

## Data Safety

Do not commit:

- source research videos
- EMG data
- photos
- research Excel workbooks
- pose JSON outputs
- marked videos
- logs
- credentials or secrets
- personal or subject-identifying information

## Streamlit Community Cloud Preparation

Before public deployment, replace local absolute paths with environment-based or relative configuration and add public, anonymized demo assets. The current local sample files are for local verification only.

## Current Limitations

- Review is a placeholder screen.
- Recording is a placeholder screen.
- AI coaching, scoring, cloud storage, authentication, and real-time camera analysis are not implemented in this prototype step.
- MediaPipe Pose uses a local model file during local development; model distribution strategy should be decided before public release.


## Streamlit Community Cloud Minimal Readiness

The app now resolves local paths in this order:

1. Environment variables such as `EMA_PROJECT_ROOT`, `EMA_DATA_ROOT`, and `EMA_ANALYSIS_ROOT`
2. Windows local defaults (`F:\EMA_Project`, `F:\EMA_Data`) when available
3. A local fallback path that lets the UI import and render when research storage is unavailable

On Streamlit Community Cloud, real research data is not included. If the marked sample video or Pose JSON is missing, the app shows that the sample video is unavailable in the current environment instead of crashing. Detection rates are shown only when a real Pose JSON file exists.

`EMA_Master_提案形式.xlsx`, source videos, EMG files, marked videos, logs, and Pose JSON outputs must remain local or private. Use dummy or anonymized assets before public deployment.

For Cloud verification without local defaults, run locally with:

```powershell
$env:EMA_DISABLE_LOCAL_DEFAULTS = "1"
streamlit run app.py
```

Unset the variable to return to the normal Windows research environment.
