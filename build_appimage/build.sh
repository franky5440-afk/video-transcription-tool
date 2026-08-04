#!/usr/bin/env bash
# Build the video-transcription-tool AppImage.
#
# Produces: build_appimage/AppDir/  (staging, not committed)
#           video-transcription-tool.AppImage  (final product, not committed)
#
# Third-party build inputs (CPU-only torch wheel, static ffmpeg, appimagetool)
# are downloaded into build_appimage/tools/ on first run and reused after that;
# that directory is gitignored, so a fresh clone re-fetches them.
#
# Reuses the existing project venv (<repo root>/venv)
# for the bundled site-packages and strips all CUDA-only content, which is
# unusable on this machine (nouveau driver, no NVIDIA proprietary driver).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build_appimage"
APPDIR="$BUILD/AppDir"
VENV="$ROOT/venv"
SITE="$VENV/lib/python3.12/site-packages"
PY_SYS="/usr/lib/python3.12"
LIBDIR="/lib/x86_64-linux-gnu"
MODULES="youtube_downloader.py transcription_service.py translation_service.py output_formatter.py video_processor.py main.py"
TOOLS="$BUILD/tools"
OUT="$ROOT/video-transcription-tool.AppImage"
WHISPER_MODEL="${XDG_CACHE_HOME:-$HOME/.cache}/whisper/base.pt"

TORCH_WHL="torch-2.13.0%2Bcpu-cp312-cp312-manylinux_2_28_x86_64.whl"
TORCH_URL="https://download.pytorch.org/whl/cpu/$TORCH_WHL"
FFMPEG_TAR="ffmpeg-release-amd64-static.tar.xz"
FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/$FFMPEG_TAR"
APPIMAGETOOL="appimagetool-x86_64.AppImage"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/$APPIMAGETOOL"

echo "== preflight =="
[ -d "$SITE" ] || { echo "ERROR: project venv not found at $VENV" >&2; exit 1; }
if [ ! -f "$WHISPER_MODEL" ]; then
  echo "ERROR: whisper 'base' model not found at $WHISPER_MODEL" >&2
  echo "       fetch it once with:" >&2
  echo "       \"$VENV/bin/python\" -c \"import whisper; whisper.load_model('base')\"" >&2
  exit 1
fi

echo "== fetching build inputs into tools/ (skipped when already present) =="
mkdir -p "$TOOLS"
fetch() {  # fetch <url> <dest>
  if [ -s "$2" ]; then
    echo "  have $(basename "$2")"
    return
  fi
  echo "  downloading $(basename "$2")"
  curl -fL --retry 3 -o "$2.part" "$1"
  mv "$2.part" "$2"
}
fetch "$TORCH_URL" "$TOOLS/$TORCH_WHL"
fetch "$FFMPEG_URL" "$TOOLS/$FFMPEG_TAR"
fetch "$APPIMAGETOOL_URL" "$TOOLS/$APPIMAGETOOL"

if [ ! -x "$TOOLS/ffmpeg" ]; then
  echo "  extracting static ffmpeg/ffprobe"
  tar -xJf "$TOOLS/$FFMPEG_TAR" -C "$TOOLS" --strip-components=1 --wildcards '*/ffmpeg' '*/ffprobe'
fi
if [ ! -x "$TOOLS/squashfs-root/AppRun" ]; then
  echo "  extracting appimagetool (so packaging does not need FUSE)"
  chmod +x "$TOOLS/$APPIMAGETOOL"
  ( cd "$TOOLS" && "./$APPIMAGETOOL" --appimage-extract >/dev/null )
fi

echo "== clearing staging AppDir =="
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" "$APPDIR/app" "$APPDIR/cache/whisper"

echo "== bundling python3.12 interpreter + stdlib =="
cp /usr/bin/python3.12 "$APPDIR/usr/bin/python3.12"
cp -a "$PY_SYS" "$APPDIR/usr/lib/python3.12"

echo "== bundling runtime system libraries =="
mkdir -p "$APPDIR/usr/lib/x86_64-linux-gnu"
for lib in libpython3.12.so.1.0 libssl.so.3 libcrypto.so.3 libexpat.so.1 \
           libz.so.1 libffi.so.8 liblzma.so.5 libbz2.so.1.0 libsqlite3.so.0 \
           libreadline.so.8 libtinfo.so.6 libstdc++.so.6; do
  cp -L "/usr/lib/x86_64-linux-gnu/$lib" "$APPDIR/usr/lib/x86_64-linux-gnu/" 2>/dev/null \
    || cp -L "$LIBDIR/$lib" "$APPDIR/usr/lib/x86_64-linux-gnu/" 2>/dev/null \
    || echo "  !! missing $lib"
done

echo "== copying site-packages (full copy, CUDA stripped next) =="
mkdir -p "$APPDIR/usr/lib/python3.12/site-packages"
cp -a "$SITE/." "$APPDIR/usr/lib/python3.12/site-packages/"

echo "== stripping CUDA-only / unused content =="
SP="$APPDIR/usr/lib/python3.12/site-packages"
rm -rf "$SP/nvidia" "$SP/cuda" "$SP/cuda_bindings" "$SP/cuda_bindings-13.3.1.dist-info" \
       "$SP/cuda_pathfinder" "$SP/cuda_pathfinder-1.6.0.dist-info" \
       "$SP/cuda_toolkit" "$SP/cuda_toolkit-13.0.3.0.dist-info" \
       "$SP/triton" "$SP/triton-3.7.1.dist-info"

echo "== replacing the CUDA-enabled torch wheel with the CPU-only wheel =="
rm -rf "$SP/torch" "$SP/torch-2.13.0.dist-info" "$SP/torchgen" "$SP/functorch"
unzip -q "$TOOLS/$TORCH_WHL" -d "$SP"
rm -f "$SP/torch/lib/libtorch_cuda.so" "$SP/torch/lib/libtorch_cuda_linalg.so" \
      "$SP/torch/lib/libc10_cuda.so" "$SP/torch/lib/libtorch_nvshmem.so" \
      "$SP/torch/lib/libcaffe2_nvrtc.so"
rm -rf "$SP/torch/include" "$SP/torch/share" "$SP/pip" "$SP/pip-24.0.dist-info"
rm -f "$SP/torch/bin/protoc" "$SP/torch/bin/protoc-3.13.0.0"
# The venv vendors an ancient argparse backport (argparse-1.4.0) which shadows
# the stdlib argparse when site-packages is prepended to PYTHONPATH; the stdlib
# one supports subparsers required=True. Drop the vendored copy.
rm -f "$SP/argparse.py" && rm -rf "$SP/argparse-1.4.0.dist-info"

echo "== bundling the six feature modules + cli entry =="
for m in $MODULES cli.py; do
  cp "$ROOT/$m" "$APPDIR/app/"
done

echo "== bundling the webui package =="
cp -r "$ROOT/webui" "$APPDIR/app/webui"
rm -rf "$APPDIR/app/webui/__pycache__"

echo "== bundling yt-dlp CLI (rewrite shebang to bundled python) =="
cp "$VENV/bin/yt-dlp" "$APPDIR/usr/bin/yt-dlp"
sed -i '1c #!/usr/bin/env python3.12' "$APPDIR/usr/bin/yt-dlp"
chmod +x "$APPDIR/usr/bin/yt-dlp"

echo "== bundling whisper 'base' model cache =="
cp "$HOME/.cache/whisper/base.pt" "$APPDIR/cache/whisper/base.pt"

echo "== bundling static ffmpeg/ffprobe =="
cp "$TOOLS/ffmpeg" "$TOOLS/ffprobe" "$APPDIR/usr/bin/"
chmod +x "$APPDIR/usr/bin/ffmpeg" "$APPDIR/usr/bin/ffprobe"

echo "== writing AppRun =="
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
SELF=$(readlink -f "$0")
HERE=$(dirname "$SELF")
export APPDIR="${APPDIR:-$HERE}"
export PATH="$APPDIR/usr/bin:$PATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib/x86_64-linux-gnu:$APPDIR/usr/lib:$APPDIR/usr/lib/python3.12/site-packages/torch/lib:$LD_LIBRARY_PATH"
export PYTHONHOME="$APPDIR/usr"
export PYTHONPATH="$APPDIR/app:$APPDIR/usr/lib/python3.12/site-packages"
export XDG_CACHE_HOME="$APPDIR/cache"
exec "$APPDIR/usr/bin/python3.12" "$APPDIR/app/cli.py" "$@"
EOF
chmod +x "$APPDIR/AppRun"

echo "== writing desktop file + icon =="
mkdir -p "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"
cat > "$APPDIR/usr/share/applications/video-transcription-tool.desktop" <<'EOF'
[Desktop Entry]
Name=Video Transcription Tool
Exec=video-transcription-tool.AppImage
Icon=video-transcription-tool
Type=Application
Categories=AudioVideo;
Terminal=true
EOF
"$APPDIR/usr/bin/python3.12" "$BUILD/make_icon.py" \
  "$APPDIR/usr/share/icons/hicolor/256x256/apps/video-transcription-tool.png"

echo "== copying desktop file + icon to AppDir root (appimagetool requirement) =="
cp "$APPDIR/usr/share/applications/video-transcription-tool.desktop" "$APPDIR/video-transcription-tool.desktop"
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/video-transcription-tool.png" "$APPDIR/video-transcription-tool.png"

echo "== AppDir staged, size: =="
du -sh "$APPDIR"

echo "== packaging AppImage =="
ARCH=x86_64 "$TOOLS/squashfs-root/AppRun" "$APPDIR" "$OUT"

echo "== done =="
ls -lh "$OUT"
