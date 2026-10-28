#!/usr/bin/env bash
set -e

echo "==> Building standalone Linux x86_64 binary for osu-farm-downloader..."
mkdir -p dist
uv tool run --with PySide6 pyinstaller --onefile --clean --name osu-farm-downloader-linux-x86_64 gui.py

echo "==> Packaging tar.gz release..."
cd dist
tar -czvf osu-farm-downloader-linux-x86_64.tar.gz osu-farm-downloader-linux-x86_64

echo "==> Build complete! Output located at dist/osu-farm-downloader-linux-x86_64"
