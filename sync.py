import os
from datetime import datetime
from pathlib import Path
import shutil
import logging
from typing import Optional, List
import sys


def print_progress(current, total):
    """Simple progress indicator that updates in place."""
    percentage = int(100.0 * current / float(total))
    sys.stdout.write(f'\rProgress: {percentage}% [{current}/{total}]')
    sys.stdout.flush()
    if current == total:
        print()


class CameraSync:
    def __init__(self, dcim_path: str, output_base: str):
        self.dcim_path = Path(dcim_path)
        self.output_base = Path(output_base)
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('sync.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_file_date(self, file_path: Path) -> Optional[datetime]:
        try:
            stat = file_path.stat()
            return datetime.fromtimestamp(stat.st_birthtime)
        except AttributeError:
            return datetime.fromtimestamp(file_path.stat().st_mtime)

    def get_day_suffix(self, day: int) -> str:
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        return str(day) + suffix

    def create_date_folder(self, date: datetime, file_type: str = 'video') -> Path:
        year_folder = str(date.year)
        month_folder = date.strftime("%B")
        day_folder = self.get_day_suffix(date.day)

        if file_type == 'photo':
            folder = self.output_base / year_folder / month_folder / day_folder / 'photos'
        else:
            folder = self.output_base / year_folder / month_folder / day_folder
        
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def get_media_files(self) -> List[tuple[Path, datetime, str]]:
        """Get media files with their creation dates and file types."""
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv'}
        photo_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
        media_files = []

        for file_path in self.dcim_path.rglob('*'):
            if file_path.is_file():
                suffix_lower = file_path.suffix.lower()
                file_type = None
                if suffix_lower in video_extensions:
                    file_type = 'video'
                elif suffix_lower in photo_extensions:
                    file_type = 'photo'
                
                if file_type:
                    file_date = self.get_file_date(file_path)
                    if file_date:
                        media_files.append((file_path, file_date, file_type))

        # Sort by creation date
        return sorted(media_files, key=lambda x: x[1])

    def generate_new_filename(self, index: int, date: datetime, file_type: str, original_ext: str) -> str:
        """Generate a clean, numbered filename with date."""
        if file_type == 'video':
            return f"video-{index:03d}-{date.strftime('%Y-%m-%d')}.mp4"
        else:  # photo
            return f"photo-{index:03d}-{date.strftime('%Y-%m-%d')}{original_ext}"

    def sync_files(self) -> bool:
        if not self.dcim_path.exists():
            self.logger.error(f"DCIM path does not exist: {self.dcim_path}")
            return False

        try:
            files_to_process = self.get_media_files()
            if not files_to_process:
                self.logger.info("No media files found to process.")
                return True

            files_moved = 0
            skipped = 0
            total_files = len(files_to_process)

            self.logger.info("\nStarting file sync...")
            print("-" * 50)

            # Group files by date to reset numbering each day
            date_groups = {}
            for file_path, file_date, file_type in files_to_process:
                date_key = file_date.date()
                if date_key not in date_groups:
                    date_groups[date_key] = []
                date_groups[date_key].append((file_path, file_date, file_type))

            # Process each day's files
            for date_key, day_files in date_groups.items():
                for idx, (file_path, file_date, file_type) in enumerate(day_files, 1):
                    dest_folder = self.create_date_folder(file_date, file_type)
                    new_filename = self.generate_new_filename(idx, file_date, file_type, file_path.suffix)
                    dest_file = dest_folder / new_filename

                    if dest_file.exists():
                        self.logger.info(f"File already exists: {dest_file}")
                        skipped += 1
                    else:
                        shutil.copy2(str(file_path), str(dest_file))
                        files_moved += 1
                        self.logger.info(
                            f"Copied: {file_path.name} -> {new_filename}")

                    print_progress(files_moved + skipped, total_files)

            self.logger.info("\nSync complete:")
            self.logger.info(f"Files copied: {files_moved}")
            self.logger.info(f"Files skipped: {skipped}")
            self.logger.info(f"Total processed: {files_moved + skipped}")
            return True

        except Exception as e:
            self.logger.error(f"Error during sync: {str(e)}", exc_info=True)
            return False


def main():
    # These paths should be configured based on your system
    dcim_path = "/Volumes/MicroSD/DCIM"  # Adjust this to your camera's mount point
    output_base = "/Volumes/External"  # Adjust this to match your external drive path

    syncer = CameraSync(dcim_path, output_base)
    success = syncer.sync_files()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
