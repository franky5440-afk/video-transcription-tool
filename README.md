# Video Transcription & Subtitle Embedding Tool
# 影片轉錄與字幕嵌入工具

[English](#english) | [繁體中文](#繁體中文)

---

## Only availble in Linux, expecting Mac OS shortly

## English

### Features

- **YouTube Download**: Download videos from YouTube URLs (includes audio)
- **Local Video Support**: Process local video files directly
- **Automatic Transcription**: Generate timestamps and text using Whisper
- **Traditional Chinese Translation**: Translate transcriptions using Google Translator
- **Markdown Output**: Save results in clean Markdown format
- **Batch Processing**: Handle multiple videos at once
- **Subtitle Embedding**: Embed translated subtitles into videos
- **MP4 Conversion**: Convert videos to MP4 format with H.264/AAC
- **Standalone Tools**: Use video processing features independently

### Requirements

- Python 3.7+
- `yt-dlp` for YouTube downloads
- `whisper` for transcription
- `deep-translator` for translation
- `ffmpeg` for video processing (install separately)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/video-transcription-tool.git
cd video-transcription-tool

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install ffmpeg (required for video processing)
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg     # macOS
```

### Usage

#### 1. Full Pipeline (Transcription + Translation + Video Processing)

```bash
python main.py "video_url_or_path" --output "./output"
```

After transcription and translation, the tool will ask:
```
Continue with video processing? (y/n):
```

- `y` - Embed translated subtitles and convert to MP4
- `n` - Skip video processing (you can do it later manually)

#### 2. Standalone Video Processing (Embed Subtitles Only)

**For this project's specific files:**
```bash
./ffmpeg_subtitles.sh
```

**For ANY video file:**
```bash
./ffmpeg_subtitles_general.sh input.mp4 subtitles.srt output.mp4
```

#### 3. Manual Video Processing (If You Skipped Step 1)

```bash
# Convert translated Markdown to SRT
python -c "
from main import create_srt_from_transcription
with open('transcription.md', 'r', encoding='utf-8') as f:
    content = f.read()
create_srt_from_transcription(content, 'transcription.srt')
"

# Embed subtitles using ffmpeg
./ffmpeg_subtitles_general.sh video.mp4 transcription.srt output.mp4
```

### Output Files

- `transcription_original.md` - Original transcription with timestamps
- `transcription_translated.md` - Traditional Chinese translation
- `transcription_translated.srt` - SRT format for subtitle embedding
- `video_with_subtitles.mp4` - Final video with embedded subtitles

### Project Structure

```
.
├── main.py                  # Main CLI application
├── youtube_downloader.py    # YouTube video downloader
├── transcription_service.py # Video transcription with Whisper
├── translation_service.py   # Translation to Traditional Chinese
├── output_formatter.py      # Markdown output formatting
├── video_processor.py       # Video processing functions
├── ffmpeg_subtitles.sh      # Project-specific ffmpeg script
├── ffmpeg_subtitles_general.sh # General-purpose ffmpeg script
├── embed_sub_fast.py        # Fast Python embedding script
├── embed_sub_simple.py      # Standard Python embedding script
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── output/                  # Output directory
    ├── video.mp4           # Downloaded video (with audio)
    ├── transcription.srt    # Original subtitles
    ├── transcription.md     # Translated transcription
    └── video_with_subtitles.mp4 # Final output
```

### Quality Settings

- **Video**: H.264, CRF 23, slow preset (good quality)
- **Audio**: AAC, 192kbps
- **Subtitles**: Traditional Chinese, aligned with timestamps

### Troubleshooting

1. **ffmpeg not found**: Install ffmpeg using your package manager
2. **Timeout issues**: Use bash scripts instead of Python for long videos
3. **Special characters in filenames**: Use the general-purpose script
4. **Translation errors**: Check your internet connection
5. **No audio in downloaded video**: Update yt-dlp and ensure proper format selection
6. **Video processing fails silently**: Ensure output files are being overwritten properly and check for file permission issues
7. **Subtitles show mixed languages**: Verify SRT file contains only translated text and regenerate if needed

### License

MIT License - See [LICENSE](LICENSE) for details.

---

## 目前只有Linux版本，Mac OS版本開發中

## 繁體中文

### 功能

- **YouTube 下載**：從YouTube網址下載影片（包含音頻）
- **本地影片支援**：直接處理本地影片檔案
- **自動轉錄**：使用Whisper生成時間軸和文字
- **繁體中文翻譯**：使用Google Translator翻譯轉錄內容
- **Markdown輸出**：以乾淨的Markdown格式保存結果
- **批次處理**：一次處理多個影片
- **字幕嵌入**：將翻譯後的字幕嵌入影片
- **MP4轉換**：轉換為MP4格式（H.264/AAC編碼）
- **獨立工具**：獨立使用影片處理功能

### 需求

- Python 3.7+
- `yt-dlp` 用於YouTube下載
- `whisper` 用於轉錄
- `deep-translator` 用於翻譯
- `ffmpeg` 用於影片處理（需單獨安裝）

### 安裝

```bash
# 複製專案
git clone https://github.com/yourusername/video-transcription-tool.git
cd video-transcription-tool

# 創建虛擬環境（推薦）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安裝依賴套件
pip install -r requirements.txt

# 安裝ffmpeg（影片處理必需）
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg     # macOS
```

### 使用方式

#### 1. 完整流程（轉錄 + 翻譯 + 影片處理）

```bash
python main.py "影片網址或本地路徑" --output "./output"
```

完成轉錄與翻譯後，系統會詢問：
```
Continue with video processing? (y/n):
```

- `y` - 嵌入翻譯後的字幕並轉換為MP4
- `n` - 跳過影片處理（稍後可手動執行）

#### 2. 獨立影片處理（僅嵌入字幕）

**針對本專案的特定檔案**：
```bash
./ffmpeg_subtitles.sh
```

**適用於任何影片檔案**：
```bash
./ffmpeg_subtitles_general.sh 輸入.mp4 字幕.srt 輸出.mp4
```

#### 3. 手動影片處理（如果您在步驟1跳過）

```bash
# 將翻譯後的Markdown轉換為SRT
python -c "
from main import create_srt_from_transcription
with open('transcription.md', 'r', encoding='utf-8') as f:
    content = f.read()
create_srt_from_transcription(content, 'transcription.srt')
"

# 使用ffmpeg嵌入字幕
./ffmpeg_subtitles_general.sh 影片.mp4 transcription.srt 輸出.mp4
```

### 輸出檔案

- `transcription_original.md` - 原文轉錄（帶時間軸）
- `transcription_translated.md` - 繁體中文翻譯
- `transcription_translated.srt` - SRT格式（用於字幕嵌入）
- `video_with_subtitles.mp4` - 含嵌入字幕的最終影片

### 專案結構

```
.
├── main.py                  # 主CLI應用程式
├── youtube_downloader.py    # YouTube影片下載器
├── transcription_service.py # 使用Whisper進行影片轉錄
├── translation_service.py   # 繁體中文翻譯
├── output_formatter.py      # Markdown輸出格式化
├── video_processor.py       # 影片處理函數
├── ffmpeg_subtitles.sh      # 專案專用ffmpeg腳本
├── ffmpeg_subtitles_general.sh # 通用ffmpeg腳本
├── embed_sub_fast.py        # 快速Python嵌入腳本
├── embed_sub_simple.py      # 標準Python嵌入腳本
├── requirements.txt         # Python依賴套件
├── README.md                # 本檔案
└── output/                  # 輸出目錄
    ├── video.mp4           # 下載的影片（包含音頻）
    ├── transcription.srt    # 原文字幕
    ├── transcription.md     # 翻譯後的轉錄
    └── video_with_subtitles.mp4 # 最終輸出
```

### 品質設定

- **影片**：H.264編碼，CRF 23，slow預設（優良品質）
- **音頻**：AAC編碼，192kbps
- **字幕**：繁體中文，與時間軸對齊

### 疑難排解

1. **找不到ffmpeg**：請使用套件管理員安裝ffmpeg
2. **超時問題**：對於長影片，請使用bash腳本而非Python腳本
3. **檔案名稱含特殊字元**：請使用通用腳本
4. **翻譯錯誤**：請檢查網路連線
5. **下載的影片沒有音頻**：請更新yt-dlp並確保正確的格式選擇
6. **影片處理失敗但無錯誤訊息**：請確保輸出檔案被正確覆寫並檢查檔案權限
7. **字幕顯示混合語言**：請驗證SRT檔案僅包含翻譯後的文字，並重新生成

### 授權

MIT授權 - 詳見[LICENSE](LICENSE)檔案。

---