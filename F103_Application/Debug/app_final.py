#!/usr/bin/env python3
import zlib, struct

APP_BIN = "application.bin"

with open(APP_BIN, "rb") as f:
    app = f.read()

crc = zlib.crc32(app) & 0xFFFFFFFF
size = len(app)

hdr = struct.pack(
    "<IIIII",
    0,
    0xABCDEFAB,
    size,
    crc,
    0x07
)

# Pad header to 1KB
header_padded = hdr + b'\xFF' * (1024 - len(hdr))

with open("ota_image.bin", "wb") as f:
    f.write(header_padded)
    f.write(app)
