#!/bin/bash

# Simple bash script to embed subtitles using ffmpeg
# This avoids Python script timeouts and runs directly

set -e

echo "Embedding subtitles using ffmpeg..."
echo "This may take several minutes for long videos."

# Use simple filenames to avoid special character issues
INPUT_VIDEO="/home/lintzuyang/Opencode/project/website/output/input.webm"
INPUT_SRT="/home/lintzuyang/Opencode/project/website/output/subtitles.srt"
OUTPUT_MP4="/home/lintzuyang/Opencode/project/website/output/final_output_with_subtitles.mp4"

# Check if input files exist
if [ ! -f "$INPUT_VIDEO" ]; then
    echo "Error: Input video not found: $INPUT_VIDEO"
    exit 1
fi

if [ ! -f "$INPUT_SRT" ]; then
    echo "Error: Input SRT not found: $INPUT_SRT"
    exit 1
fi

# Use ffmpeg with good quality settings
# -preset slow: Good balance of quality and speed
# -crf 23: Good quality (lower is better, 18-28 is typical range)
# -c:a aac: AAC audio codec
# -b:a 192k: Good audio bitrate

echo "Running ffmpeg command..."
ffmpeg -y \
    -i "$INPUT_VIDEO" \
    -vf "subtitles=$INPUT_SRT" \
    -c:v libx264 -preset slow -crf 23 \
    -c:a aac -b:a 192k \
    -movflags +faststart \
    "$OUTPUT_MP4"

echo "Done! Output file: $OUTPUT_MP4"

# Check the output duration
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT_MP4")
echo "Output video duration: $DURATION seconds ($((DURATION/60)) minutes $((DURATION%60)) seconds)"

# Check file size
SIZE=$(du -h "$OUTPUT_MP4" | cut -f1)
echo "Output file size: $SIZE"