# Video Transcription & Subtitle Embedding Tool
# 影片轉錄與字幕嵌入工具

[English](#english) | [繁體中文](#繁體中文)

Turn a YouTube link or a local video into a Traditional Chinese transcript — and, when you want one, a video with the subtitles burned in.

---

## Public web UI available on every platform · 公開網頁版已上線

Open **https://franky5440-afk.github.io/video-transcription-tool/** in any browser.
The page itself is only an interface — download, transcription and translation all run on *your* machine through the local backend; nothing is ever uploaded. The AppImage below is still Linux-only for now.

---

## English

### What you get

Two ways to use it, both driving the same pipeline:

- **Public web UI** — open https://franky5440-afk.github.io/video-transcription-tool/ anywhere (Windows, macOS, Linux, any browser). It auto-detects a backend running on `127.0.0.1:8713`; if none is found it walks you through starting one. Files never leave your machine.
- **Local web UI** — double-click the AppImage and the same page opens locally. Nothing is uploaded anywhere; everything runs on your own machine.
- **Command line** — seven subcommands, for scripting or for running one step at a time.

### The two workflows

The web UI does not offer six equal buttons; it offers the two things people actually want:

| Workflow | Steps | Use it when |
|---|---|---|
| **Video** | download → transcribe → translate → format → **embed** | you want a video file with Traditional Chinese subtitles burned in |
| **Text** | download → transcribe → translate → format | you only want the words — an interview, a talk, a lecture |

**Text deliberately skips the embed step.** Burning subtitles re-encodes the whole video and is by far the slowest part of the run; if you are going to read a transcript, waiting for it produces a file you will never open.

Both workflows produce all four text artifacts, so the original language is always available alongside the translation.

### Quick start (AppImage)

There is no prebuilt download yet — build it once from source:

```bash
git clone https://github.com/franky5440-afk/video-transcription-tool.git
cd video-transcription-tool

python3 -m venv venv
venv/bin/pip install -r requirements.txt

# fetch the whisper "base" model once; the build bundles it
venv/bin/python -c "import whisper; whisper.load_model('base')"

./build_appimage/build.sh
```

This produces `video-transcription-tool.AppImage` (~460 MB — it carries its own Python, PyTorch, ffmpeg and the whisper model, so the machine you run it on needs nothing installed).

Then just **double-click it**. The web UI opens in your browser.

The build downloads a CPU-only PyTorch wheel, a static ffmpeg and appimagetool into `build_appimage/tools/` on first run and reuses them afterwards.

### Running from source instead

```bash
venv/bin/python cli.py serve      # web UI, same as double-clicking the AppImage
```

### How the public page talks to your machine

The GitHub Pages deployment is static — it cannot run Whisper or ffmpeg. When you open the public URL, the page probes `http://127.0.0.1:8713/api/health` every few seconds:

- **Backend running** → the page works exactly like the local one (same two workflows, same outputs).
- **Backend not found** → the page shows a short setup guide and keeps retrying; start `cli.py serve` and it connects automatically.

Security: CORS is granted to exactly one origin (`https://franky5440-afk.github.io`); no other website can talk to your local backend, and jobs still require `Content-Type: application/json`, so plain HTML form posts from any site are rejected. Your files stay on your disk.

### Why the backend runs on your machine instead of in the cloud

We did evaluate putting a real backend online so the public page would need nothing installed. It lost on practicality:

- **Whisper is heavy.** Transcription takes roughly as long as the video itself and wants about 1 GB of RAM. Free tiers don't fit it (Render's free plan caps at 512 MB); the ones that do fit bill every month (Fly.io ≈ $3–6/mo, Railway ≈ $10–20/mo).
- **Datacenter IPs get blocked by YouTube.** `yt-dlp` from cloud hosts constantly trips "confirm you're not a bot" checks; from a home connection it just works.
- **Free compute means sleeping and queueing.** The strongest free option (Hugging Face Spaces, 2 vCPU / 16 GB) sleeps when idle, adds 1–2 minute cold starts, and queues concurrent jobs — impractical for a tool you use occasionally but want *now*.
- **Privacy is the feature, not a bonus.** In this design your video never leaves your disk; a hosted backend would require uploading every file it processes.

So the trade we chose: one public URL anyone can open, while the heavy lifting stays on the machine that owns the files.

### Command line

Every subcommand takes `--output` and defaults to `./output`. Running the tool with no subcommand at all starts the web UI.

```bash
cli.py all         <url-or-file>          # full pipeline, ending in a subtitled MP4
cli.py download    <url>                  # download a YouTube video
cli.py transcribe  <video>                # video  -> SRT
cli.py translate   <srt>                  # SRT    -> Traditional Chinese SRT + Markdown
cli.py embed       <video> <srt>          # burn subtitles into a video
cli.py mp4         <video>                # convert to MP4 (H.264 / AAC)
cli.py serve       [--port 8713] [--no-browser]
```

### Output files

| File | Contents |
|---|---|
| `<video>.srt` | transcription in the original language |
| `transcription_translated.srt` | Traditional Chinese subtitles |
| `transcription_translated.md` | Traditional Chinese transcript |
| `transcription_original.md` | original-language transcript |
| `<video>_subtitled.mp4` | the video with subtitles burned in (video workflow only) |

Web UI runs keep everything in `<output>/webui/<job_id>/`, so two runs can never overwrite each other.

### Notes and limits

- **Linux x86_64 only** for now.
- **No progress percentage.** Whisper does not report progress, so the UI shows which step is running and how long it has been running — never an invented percentage.
- **Transcription takes about as long as the video**, on a CPU-only machine with the bundled `base` model.
- **The server keeps running after you close the browser tab.** Starting the tool again simply reopens the page. To stop it, press Ctrl+C in the terminal, or `pkill -f "cli[.]py"`.
- Video encoding is software H.264 (`libx264`); AV1 sources are avoided at download time. Both are choices made for a machine with no hardware video acceleration.
- The web UI binds `127.0.0.1` only. It reads local file paths you give it, so it is deliberately not reachable from your network.

### Requirements (running from source)

- Python 3.12
- `yt-dlp`, `openai-whisper`, `deep-translator`, `flask` (all in `requirements.txt`)
- `ffmpeg` on your PATH (`sudo apt install ffmpeg`)

### Project structure

```
.
├── cli.py                   # subcommand layer (all/download/transcribe/translate/embed/mp4/serve)
├── main.py                  # original interactive pipeline
├── youtube_downloader.py    # YouTube download
├── transcription_service.py # transcription (Whisper)
├── translation_service.py   # translation to Traditional Chinese
├── output_formatter.py      # Markdown formatting
├── video_processor.py       # subtitle embedding, MP4 conversion
├── webui/
│   ├── server.py            # local Flask backend (CORS: Pages origin only)
│   └── static/index.html    # the whole UI, one self-contained page
├── .github/workflows/
│   └── deploy-pages.yml     # deploys webui/static to GitHub Pages on push
├── build_appimage/build.sh  # builds the AppImage from scratch
├── tests/                   # regression tests (no network, no real server)
└── output/                  # results
```

### Troubleshooting

1. **ffmpeg not found** — install it with your package manager.
2. **`import whisper` fails or behaves oddly** — you have the wrong `whisper` package; install `openai-whisper`.
3. **Nothing happens when I start it again** — it is already running; the existing page is reopened instead of a second server being started.
4. **Port 8713 is taken by something else** — start with `--port`.
5. **Translation errors** — check your internet connection; translation is the only step that needs one.
6. **Downloaded video has no audio** — update `yt-dlp`.
7. **Filenames with special characters** — the tool handles them, but if you call ffmpeg yourself, quote the paths.

### License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

## 公開網頁版已上線，任何平台都能開

打開 **https://franky5440-afk.github.io/video-transcription-tool/** 就能使用。
這個網頁只是操作介面——下載、轉錄、翻譯全部在你自己的電腦上由本機後端執行，檔案不會上傳到任何地方。下面的 AppImage 目前仍然只支援 Linux。

---

## 繁體中文

### 這個工具做什麼

把 YouTube 影片或本機影片轉成繁體中文逐字稿；需要的話，還能把字幕直接燒進影片裡。三種使用方式，跑的是同一條流程：

- **公開網頁版**——在任何平台的瀏覽器打開 https://franky5440-afk.github.io/video-transcription-tool/。頁面會自動偵測你電腦上 `127.0.0.1:8713` 的後端；沒偵測到就引導你啟動。檔案永遠留在你的機器上。
- **本機網頁介面**——雙擊 AppImage，同樣的頁面會在本機打開。**檔案不會上傳到任何地方**，全部在你自己的電腦上處理。
- **命令列**——七個子命令，適合寫腳本或單獨執行某一步。

### 兩條工作流

網頁介面不是給你六個平等的按鈕，而是給你真正想要的兩件事：

| 工作流 | 步驟 | 什麼時候用 |
|---|---|---|
| **影片** | 下載 → 轉錄 → 翻譯 → 格式化 → **燒字幕** | 你要一支帶繁體中文字幕的影片 |
| **文字** | 下載 → 轉錄 → 翻譯 → 格式化 | 你只要文字——訪談、演講、課程 |

**「文字」刻意不跑燒字幕這一步。** 燒字幕要把整支影片重新編碼，是全流程最慢的一環；如果你要的只是逐字稿，等它等於白等，還多出一個你不會打開的影片檔。

四種文字產物**兩條工作流都會給**，所以原文永遠跟翻譯放在一起。

### 快速開始（AppImage）

目前還沒有現成的下載檔，先自己建一次：

```bash
git clone https://github.com/franky5440-afk/video-transcription-tool.git
cd video-transcription-tool

python3 -m venv venv
venv/bin/pip install -r requirements.txt

# 先抓一次 whisper 的 base 模型，打包時會一起包進去
venv/bin/python -c "import whisper; whisper.load_model('base')"

./build_appimage/build.sh
```

這會產生 `video-transcription-tool.AppImage`（約 460 MB——它自帶 Python、PyTorch、ffmpeg 與 whisper 模型，所以執行它的電腦不需要另外裝任何東西）。

接著**直接雙擊它**，網頁介面就會在瀏覽器打開。

首次建置會把 CPU 版 PyTorch、靜態 ffmpeg 與 appimagetool 下載到 `build_appimage/tools/`，之後重複使用。

### 不打包，直接從原始碼跑

```bash
venv/bin/python cli.py serve      # 網頁介面，與雙擊 AppImage 相同
```

### 公開頁面怎麼連上你的電腦

GitHub Pages 是靜態空間，跑不動 Whisper 與 ffmpeg。打開公開網址時，頁面會每幾秒探測一次 `http://127.0.0.1:8713/api/health`：

- **後端已在跑** → 頁面行為與本機版完全相同（同樣兩條工作流、同樣的產物）。
- **偵測不到後端** → 頁面顯示簡短的安裝指引並持續自動重試；執行 `cli.py serve` 之後就會自動連上。

安全設計：CORS 只允許唯一來源 `https://franky5440-afk.github.io`，其他任何網站都無法與你的本機後端溝通；送出任務仍然必須帶 `Content-Type: application/json`，所以任何網站的純 HTML 表單都會被拒絕。你的檔案只留在你的磁碟上。

### 為什麼後端放在你自己的電腦，而不是雲端

我們確實評估過「架一個真正的雲端後端，讓公開頁面什麼都不用裝」這條路，最後因為實用性不足而放棄：

- **whisper 很吃資源。** 轉錄時間大約等於影片長度，需要約 1GB RAM。免費層裝不下（Render 免費版上限 512MB）；裝得下的每個月都要錢（Fly.io 約 $3–6/月、Railway 約 $10–20/月）。
- **資料中心 IP 會被 YouTube 擋。** 從雲端主機跑 `yt-dlp` 動不動就被要求「確認你不是機器人」；從家裡的網路就是能直接動。
- **免費算力等於休眠與排隊。** 最強的免費選項（Hugging Face Spaces，2 vCPU / 16GB）閒置會休眠、冷啟動多等 1–2 分鐘、同時來的工作要排隊——對一個「偶爾用、但要用就要馬上動」的工具來說不實用。
- **隱私是功能本身，不是附加價值。** 目前的設計裡影片永遠不離開你的磁碟；改成雲端後端就變成每支影片都要先上傳。

所以我們做的取捨是：給你一個任何人都能打開的公開網址，重活兒則留在檔案所在的那台機器上。

### 命令列

每個子命令都吃 `--output`，預設 `./output`。**完全不給子命令時會直接開啟網頁介面。**

```bash
cli.py all         <網址或檔案>            # 完整流程，最後產出帶字幕的 MP4
cli.py download    <網址>                 # 下載 YouTube 影片
cli.py transcribe  <影片>                 # 影片   -> SRT
cli.py translate   <srt>                  # SRT    -> 繁中 SRT ＋ Markdown
cli.py embed       <影片> <srt>            # 把字幕燒進影片
cli.py mp4         <影片>                 # 轉成 MP4（H.264 / AAC）
cli.py serve       [--port 8713] [--no-browser]
```

### 輸出檔案

| 檔案 | 內容 |
|---|---|
| `<影片名>.srt` | 原文字幕 |
| `transcription_translated.srt` | 繁體中文字幕 |
| `transcription_translated.md` | 繁體中文逐字稿 |
| `transcription_original.md` | 原文逐字稿 |
| `<影片名>_subtitled.mp4` | 燒好字幕的影片（僅「影片」工作流） |

網頁介面的每次執行都放在 `<output>/webui/<job_id>/`，所以兩次執行不會互相覆蓋。

### 說明與限制

- 目前**只支援 Linux x86_64**。
- **沒有進度百分比。** whisper 不會回報進度，所以介面只顯示「現在在哪一步」與「已經過多久」——不會編一個假的百分比給你看。
- **轉錄時間大約等於影片長度**（無硬體加速的機器、使用內建的 `base` 模型）。
- **關掉瀏覽器分頁不會關掉伺服器。** 再啟動一次只會把頁面重新打開。要真的停掉它，在終端機按 Ctrl+C，或執行 `pkill -f "cli[.]py"`。
- 影片編碼使用純軟體的 H.264（`libx264`），下載時也會避開 AV1。這兩個都是為「沒有硬體影音加速的機器」所做的取捨。
- 網頁介面只綁定 `127.0.0.1`。它會讀取你給的本機檔案路徑，所以刻意不開放給區域網路連線。

### 需求（從原始碼執行時）

- Python 3.12
- `yt-dlp`、`openai-whisper`、`deep-translator`、`flask`（都在 `requirements.txt` 裡）
- `ffmpeg` 需在 PATH 上（`sudo apt install ffmpeg`）

### 專案結構

```
.
├── cli.py                   # 子命令層（all/download/transcribe/translate/embed/mp4/serve）
├── main.py                  # 最初的互動式流程
├── youtube_downloader.py    # YouTube 下載
├── transcription_service.py # 轉錄（Whisper）
├── translation_service.py   # 繁體中文翻譯
├── output_formatter.py      # Markdown 格式化
├── video_processor.py       # 字幕嵌入、MP4 轉換
├── webui/
│   ├── server.py            # 本機 Flask 後端（CORS 僅允許 Pages 來源）
│   └── static/index.html    # 整個介面，單一自足頁面
├── .github/workflows/
│   └── deploy-pages.yml     # push 時把 webui/static 部署到 GitHub Pages
├── build_appimage/build.sh  # 從零建置 AppImage
├── tests/                   # 回歸測試（不連網、不啟動真的伺服器）
└── output/                  # 產出結果
```

### 疑難排解

1. **找不到 ffmpeg**——用套件管理員安裝。
2. **`import whisper` 失敗或行為怪異**——裝到錯的 `whisper` 套件了，請改裝 `openai-whisper`。
3. **再啟動一次沒有反應**——它已經在跑了，程式會把原本的頁面重新打開，而不是再開一個伺服器。
4. **8713 埠被別的程式佔用**——用 `--port` 指定其他埠。
5. **翻譯出錯**——檢查網路連線；整條流程只有翻譯這一步需要連網。
6. **下載的影片沒有聲音**——更新 `yt-dlp`。
7. **檔名有特殊字元**——工具本身處理得了；但如果你自己呼叫 ffmpeg，記得把路徑加引號。

### 授權

Apache License 2.0 - 詳見 [LICENSE](LICENSE) 檔案。

---
