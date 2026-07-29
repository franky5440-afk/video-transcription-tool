#!/bin/bash

# General-purpose script to embed subtitles into any video
# Usage: ./ffmpeg_subtitles_general.sh input_video input_srt [output_mp4]

set -e

# Check if ffmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install ffmpeg first."
    exit 1
fi

# Check arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 input_video input_srt [output_mp4]"
    echo ""
    echo "Example:"
    echo "  $0 video.mp4 subtitles.srt output_with_subtitles.mp4"
    echo ""
    echo "If output_mp4 is not specified, it will be generated as:"
    echo "  <input_video_name>_with_subtitles.mp4"
    exit 1
fi

INPUT_VIDEO="$1"
INPUT_SRT="$2"
OUTPUT_MP4="${3:-$(dirname "$INPUT_VIDEO")/$(basename "$INPUT_VIDEO" .webm)_with_subtitles.mp4)}
OUTPUT_MP4="${OUTPUT_MP4:-$(dirname "$INPUT_VIDEO")/$(basename "$INPUT_VIDEO" .mp4)_with_subtitles.mp4)}
OUTPUT_MP4="${OUTPUT_MP4:-$(dirname "$INPUT_VIDEO")/$(basename "$INPUT_VIDEO")_with_subtitles.mp4}"

# Check if input files exist
if [ ! -f "$INPUT_VIDEO" ]; then
    echo "Error: Input video not found: $INPUT_VIDEO"
    exit 1
fi

if [ ! -f "$INPUT_SRT" ]; then
    echo "Error: Input SRT not found: $INPUT_SRT"
    exit 1
fi

echo "=== Video Subtitle Embedding ==="
echo "Input video: $INPUT_VIDEO"
echo "Input SRT: $INPUT_SRT"
echo "Output MP4: $OUTPUT_MP4"
echo ""

# Get input video duration
INPUT_DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$INPUT_VIDEO")
echo "Input video duration: ${INPUT_DURATION} seconds ($((INPUT_DURATION/60)) minutes $((INPUT_DURATION%60)) seconds)"
echo ""

# Use ffmpeg with good quality settings
# -preset slow: Good balance of quality and speed
# -crf 23: Good quality (lower is better, 18-28 is typical range)
# -c:a aac: AAC audio codec
# -b:a 192k: Good audio bitrate
# -movflags +faststart: Enable streaming-friendly MP4
echo "Running ffmpeg... (this may take a while for long videos)"
echo ""

ffmpeg -y \
    -i "$INPUT_VIDEO" \
    -vf "subtitles=$INPUT_SRT" \
    -c:v libx264 -preset slow -crf 23 \
    -c:a aac -b:a 192k \
    -movflags +faststart \
    "$OUTPUT_MP4"

echo ""
echo "=== Done! ==="
echo "Output file: $OUTPUT_MP4"

# Check the output duration
if [ -f "$OUTPUT_MP4" ]; then
    OUTPUT_DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT_MP4")
    echo "Output video duration: ${OUTPUT_DURATION} seconds ($((OUTPUT_DURATION/60)) minutes $((OUTPUT_DURATION%60)) seconds)"
    
    # Check file size
    SIZE=$(du -h "$OUTPUT_MP4" | cut -f1)
    echo "Output file size: $SIZE"
    
    # Verify duration matches
    if [ $(echo "$OUTPUT_DURATION > $INPUT_DURATION - 1" | bc) -eq 1 ]; then
        echo "✓ Success: Output duration matches input duration"
    else
        echo "⚠ Warning: Output duration ($OUTPUT_DURATION s) is shorter than input ($INPUT_DURATION s)"
    fi
else
    echo "✗ Error: Output file was not created"
    exit 1
fi