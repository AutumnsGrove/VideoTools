# CameraSync

Fast, concurrent media file syncer written in Go. Copies photos and videos from a camera's SD card (DCIM) to an organized date-based folder structure.

Rewritten from the original Python `sync_concurrent.py` for speed and portability — single binary, zero dependencies.

## Install

```bash
cd CameraSync
go build -o camera-sync .

# Install the binary system-wide
sudo cp camera-sync /usr/local/bin/

# Set up your global config so it works from anywhere
mkdir -p ~/.config/camera-sync
cp config_template.json ~/.config/camera-sync/config.json

# Edit with your actual paths
nano ~/.config/camera-sync/config.json
```

After this, just run `camera-sync` from any directory.

## Configuration

CameraSync looks for a config file in this order:

1. Path passed via `-config` flag
2. `./config.json` in the current directory
3. `~/.config/camera-sync/config.json`

If no config is found, built-in defaults are used. CLI flags always override config values.

### config.json

```json
{
  "source": "/Volumes/MicroSD/DCIM",
  "destination": "/Volumes/External",
  "workers": 8
}
```

### Full config with custom extensions

```json
{
  "source": "/Volumes/MicroSD/DCIM",
  "destination": "/Volumes/External",
  "workers": 8,
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".m4v", ".3gp"],
  "photo_extensions": [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".heif"]
}
```

Copy `config_template.json` to `config.json` and edit to match your setup.

For global config, place it at `~/.config/camera-sync/config.json` so it works from any directory.

## Usage

```bash
# Use config file (auto-discovered)
camera-sync

# Override source/destination
camera-sync -src /Volumes/SD/DCIM -dst ~/Media

# Explicit config path
camera-sync -config /path/to/config.json

# More workers for fast drives
camera-sync -workers 16
```

## Output Structure

Files are organized by date with ordinal day suffixes:

```
/Volumes/External/
  2026/
    April/
      10th/
        video-001-2026-04-10.mp4
        video-002-2026-04-10.mov
        photos/
          photo-001-2026-04-10.heic
          photo-002-2026-04-10.jpg
      9th/
        video-001-2026-04-09.mp4
```

## How It Works

1. Recursively scans the source DCIM path for media files
2. Groups files by date and type (video/photo)
3. Copies concurrently using a goroutine worker pool
4. Skips files that already exist at the destination
5. Preserves file modification times

## CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-src` | from config | Source DCIM path |
| `-dst` | from config | Destination base path |
| `-workers` | from config (8) | Concurrent copy workers |
| `-config` | auto-discover | Path to config.json |
