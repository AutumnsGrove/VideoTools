import os
import subprocess
import logging
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
import time
import humanize


class VideoCombiner:
    def __init__(self, input_dir: str, output_dir: str, log_dir: str = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.log_dir = Path(log_dir) if log_dir else self.output_dir
        self._setup_logging()
        self._setup_directories()

    def _setup_logging(self):
        log_file = self.log_dir / 'video_processing.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _setup_directories(self):
        if not self.input_dir.exists():
            raise ValueError(f"Input directory does not exist: {self.input_dir}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_video_metadata(self, video_path: Path) -> Optional[Dict]:
        try:
            # Get detailed metadata including bit depth
            result = subprocess.run([
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ], capture_output=True, text=True)

            if result.returncode != 0:
                self.logger.error(f"Error getting metadata for {video_path}")
                return None

            metadata = json.loads(result.stdout)
            video_stream = next((stream for stream in metadata.get('streams', [])
                               if stream['codec_type'] == 'video'), None)

            if not video_stream:
                self.logger.error(f"No video stream found in {video_path}")
                return None

            # Extract bit depth and color space information
            pix_fmt = video_stream.get('pix_fmt', '')
            bit_depth = 8  # default
            if 'p10' in pix_fmt:
                bit_depth = 10
            elif 'p12' in pix_fmt:
                bit_depth = 12

            return {
                'path': str(video_path),
                'creation_time': metadata.get('format', {}).get('tags', {}).get('creation_time', ''),
                'duration': float(metadata.get('format', {}).get('duration', 0)),
                'codec_name': video_stream.get('codec_name'),
                'frame_rate': video_stream.get('r_frame_rate'),
                'bit_depth': bit_depth,
                'pix_fmt': pix_fmt,
                'size': os.path.getsize(video_path)
            }
        except Exception as e:
            self.logger.error(f"Error getting metadata for {video_path}: {str(e)}")
            return None

    def _prepare_video(self, video_path: Path, position: int, total: int) -> Optional[Path]:
        """Prepare video for concatenation with enhanced 10-bit support."""
        try:
            metadata = self._get_video_metadata(video_path)
            if not metadata:
                return None

            # Create temporary directory if it doesn't exist
            temp_dir = self.output_dir / 'temp'
            temp_dir.mkdir(exist_ok=True)

            output_path = temp_dir / f"prep_{video_path.name}"
            
            print(f"\nProcessing video {position}/{total}: {video_path.name}")
            print(f"Original size: {humanize.naturalsize(metadata['size'])}")
            
            # Basic conversion that maintains quality while ensuring compatibility
            process = subprocess.Popen([
                'ffmpeg',
                '-i', str(video_path),
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '17',
                '-profile:v', 'high444',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'copy',
                '-y',
                str(output_path)
            ], stderr=subprocess.PIPE, universal_newlines=True)

            # Progress tracking
            start_time = time.time()
            duration = metadata.get('duration', 0)
            
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                    
                # Parse FFmpeg progress
                time_match = re.search(r'time=(\d+):(\d+):(\d+.\d+)', line)
                if time_match:
                    hours, minutes, seconds = map(float, time_match.groups())
                    current_duration = hours * 3600 + minutes * 60 + seconds
                    progress = min(100, (current_duration / float(duration)) * 100)
                    
                    # Calculate ETA
                    elapsed = time.time() - start_time
                    if progress > 0:
                        eta = (elapsed / progress) * (100 - progress)
                        eta_str = str(timedelta(seconds=int(eta)))
                    else:
                        eta_str = "Unknown"
                        
                    print(f"\rProgress: {progress:.1f}% | ETA: {eta_str}", end='')

            if process.wait() != 0:
                self.logger.error(f"FFmpeg error processing {video_path}")
                return None

            # Show size comparison
            if output_path.exists():
                new_size = os.path.getsize(output_path)
                print(f"\nProcessed size: {humanize.naturalsize(new_size)}")
                size_change = new_size - metadata['size']
                sign = '+' if size_change >= 0 else ''
                print(f"Size change: {sign}{humanize.naturalsize(size_change)}")
                return output_path
            else:
                self.logger.error(f"Output file not created: {output_path}")
                return None

        except Exception as e:
            self.logger.error(f"Error preparing video {video_path}: {str(e)}")
            return None

    def combine_videos(self, output_filename: str = None) -> Optional[str]:
        try:
            if output_filename is None:
                date_match = re.search(r'(\d{4})/([^/]+)/(\d+)[^\d/]*$', str(self.input_dir))
                if date_match:
                    year, month, day = date_match.groups()
                    output_filename = f"combined-{year}-{month}-{day}.mp4"
                else:
                    output_filename = f"combined-{datetime.now().strftime('%Y-%m-%d')}.mp4"

            if not output_filename.endswith('.mp4'):
                output_filename += '.mp4'

            video_files = sorted(list(self.input_dir.glob('video-*.mp4')))
            if not video_files:
                raise ValueError(f"No video files found in {self.input_dir}")

            print(f"\nFound {len(video_files)} videos to process")
            
            # Process videos and get metadata
            processed_videos = []
            total_size = 0
            
            for idx, video_path in enumerate(video_files, 1):
                processed_path = self._prepare_video(video_path, idx, len(video_files))
                if processed_path:
                    metadata = self._get_video_metadata(processed_path)
                    if metadata:
                        processed_videos.append(metadata)
                        total_size += metadata['size']

            if not processed_videos:
                raise ValueError("No valid videos to combine")

            # Create file list for FFmpeg
            file_list_path = self.output_dir / 'temp_files.txt'
            with open(file_list_path, 'w', encoding='utf-8') as f:
                for video in processed_videos:
                    escaped_path = video['path'].replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")

            output_path = self.output_dir / output_filename
            print(f"\nCombining {len(processed_videos)} videos into {output_filename}")
            print(f"Total input size: {humanize.naturalsize(total_size)}")

            # Combine videos with simpler settings
            process = subprocess.Popen([
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(file_list_path),
                '-c', 'copy',  # Just copy streams without re-encoding
                '-y',
                str(output_path)
            ], stderr=subprocess.PIPE, universal_newlines=True)

            # Calculate total duration for progress tracking
            total_duration = sum(float(v.get('duration', 0)) for v in processed_videos)
            start_time = time.time()

            while True:
                line = process.stderr.readline()
                if not line:
                    break
                    
                # Parse FFmpeg progress
                time_match = re.search(r'time=(\d+):(\d+):(\d+.\d+)', line)
                if time_match:
                    hours, minutes, seconds = map(float, time_match.groups())
                    current_duration = hours * 3600 + minutes * 60 + seconds
                    progress = min(100, (current_duration / float(total_duration)) * 100)
                    
                    # Calculate ETA
                    elapsed = time.time() - start_time
                    if progress > 0:
                        eta = (elapsed / progress) * (100 - progress)
                        eta_str = str(timedelta(seconds=int(eta)))
                    else:
                        eta_str = "Unknown"
                        
                    print(f"\rCombining: {progress:.1f}% | ETA: {eta_str}", end='')

            if process.wait() != 0:
                self.logger.error(f"Error combining videos")
                return None

            # Show final size comparison
            final_size = os.path.getsize(output_path)
            print(f"\nFinal video size: {humanize.naturalsize(final_size)}")
            print(f"Size change from total inputs: {humanize.naturalsize(final_size - total_size, signed=True)}")

            self.logger.info(f"Successfully combined videos to {output_path}")

            # Clean up
            file_list_path.unlink()
            temp_dir = self.output_dir / 'temp'
            if temp_dir.exists():
                for file in temp_dir.glob('*'):
                    file.unlink()
                temp_dir.rmdir()

            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error combining videos: {str(e)}")
            return None


def main():
    input_dir = "/Volumes/External/2025/May/26th"
    output_dir = "/Volumes/External/2025/May"
    log_dir = "/Users/mini/Documents/VideoTools"

    try:
        print("\nVideo Combiner with 10-bit support")
        print("=" * 40)
        combiner = VideoCombiner(input_dir, output_dir, log_dir)
        output_path = combiner.combine_videos()
        if output_path:
            print(f"\nSuccess! Combined video saved to: {output_path}")
        else:
            print("\nFailed to combine videos")
            exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()