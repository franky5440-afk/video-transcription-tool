#!/usr/bin/env python3
"""Generate a minimal solid-color PNG icon for the AppImage (no external deps)."""

import struct
import sys
import zlib

SIZE = 256
COLOR = (0x1F, 0x6F, 0xEB)  # a blue square


def write_png(path: str) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    raw = b"".join(
        b"\x00" + bytes(COLOR) * SIZE for _ in range(SIZE)
    )
    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


if __name__ == "__main__":
    write_png(sys.argv[1])
