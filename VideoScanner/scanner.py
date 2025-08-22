#!/usr/bin/env python3
"""
Video File Scanner - Analyzes directories for large video files
Creates markdown reports with file listings and paths for easy copy/paste
"""

import os
import json
import argparse
import threading
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Tuple, Dict


class ProgressDisplay:
    """UV-style minimal progress display"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.current_dir = ""
        self.files_found = 0
        self.total_size_gb = 0.0
        self.active = True
        self.start_time = time.time()
        self.last_update = 0
        self.dirs_scanned = 0
        
    def update(self, directory: str = None, found_file: bool = False, size_gb: float = 0, dir_completed: bool = False):
        with self.lock:
            if directory:
                self.current_dir = os.path.basename(directory)
            if found_file:
                self.files_found += 1
                self.total_size_gb += size_gb
            if dir_completed:
                self.dirs_scanned += 1
            
            # Only update display every 0.2 seconds to reduce flicker
            now = time.time()
            if now - self.last_update > 0.2:
                self._display_current_status()
                self.last_update = now
    
    def _display_current_status(self):
        """Display current status on single line"""
        elapsed = time.time() - self.start_time
        # Clear line and write status
        print(f"\r\033[K🔍 {self.current_dir[:40]:<40} | {self.files_found:>3} files | {self.total_size_gb:>6.1f}GB | {elapsed:>4.0f}s", 
              end="", flush=True)
    
    def display_loop(self):
        """Minimal display loop - just ensures we show something if updates stop"""
        while self.active:
            time.sleep(1.0)  # Much less frequent updates
            if self.active:
                with self.lock:
                    self._display_current_status()
    
    def stop(self):
        self.active = False
        print()  # New line after final update


class VideoScanner:
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.progress = ProgressDisplay()
        self.results: List[Tuple[str, float]] = []
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {config_path} not found. Using defaults.")
            return {
                "size_threshold_gb": 1.0,
                "supported_extensions": [".mp4", ".mov"],
                "max_workers": 4,
                "output_filename": "video_scan_results.md",
                "exclude_pattern": "_compressed"
            }
    
    def get_file_size_gb(self, file_path: str) -> float:
        """Get file size in gigabytes"""
        try:
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 ** 3)
        except (OSError, IOError):
            return 0.0
    
    def scan_directory(self, directory: str) -> List[Tuple[str, float]]:
        """Scan a single directory for video files"""
        found_files = []
        self.progress.update(directory=directory)
        
        try:
            for item in os.listdir(directory):
                if item.startswith('.') and not self.config.get('scan_hidden_dirs', False):
                    continue
                    
                item_path = os.path.join(directory, item)
                
                if os.path.isfile(item_path):
                    # Check if it's a supported video file
                    ext = os.path.splitext(item)[1].lower()
                    if ext in self.config['supported_extensions']:
                        # Check exclude pattern if configured
                        exclude_pattern = self.config.get('exclude_pattern', '')
                        if exclude_pattern and re.search(exclude_pattern, item):
                            continue  # Skip files matching exclude pattern
                            
                        size_gb = self.get_file_size_gb(item_path)
                        if size_gb >= self.config['size_threshold_gb']:
                            found_files.append((item_path, size_gb))
                            self.progress.update(found_file=True, size_gb=size_gb)
                            
        except (PermissionError, OSError):
            pass  # Skip directories we can't access
        
        self.progress.update(dir_completed=True)
        return found_files
    
    def discover_directories(self, root_path: str) -> List[str]:
        """Recursively discover all directories to scan"""
        directories = []
        try:
            for root, dirs, _ in os.walk(root_path):
                directories.append(root)
                # Filter out hidden directories if not configured to scan them
                if not self.config.get('scan_hidden_dirs', False):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
        except (PermissionError, OSError):
            directories = [root_path]  # Just scan the root if we can't walk
            
        return directories
    
    def scan_concurrent(self, root_path: str):
        """Scan directories concurrently"""
        print(f"🚀 Starting concurrent scan of: {root_path}")
        print(f"📏 Size threshold: {self.config['size_threshold_gb']}GB")
        print(f"🎬 Extensions: {', '.join(self.config['supported_extensions'])}")
        print(f"👥 Workers: {self.config['max_workers']}")
        exclude_pattern = self.config.get('exclude_pattern', '')
        if exclude_pattern:
            print(f"🚫 Excluding pattern: {exclude_pattern}")
        print()
        
        # Start progress display in background
        progress_thread = threading.Thread(target=self.progress.display_loop, daemon=True)
        progress_thread.start()
        
        # Discover all directories first
        directories = self.discover_directories(root_path)
        
        # Scan directories concurrently
        with ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
            future_to_dir = {
                executor.submit(self.scan_directory, directory): directory 
                for directory in directories
            }
            
            for future in as_completed(future_to_dir):
                try:
                    files_found = future.result()
                    self.results.extend(files_found)
                except Exception as e:
                    directory = future_to_dir[future]
                    print(f"\nError scanning {directory}: {e}")
        
        # Stop progress display
        self.progress.stop()
        
        # Sort results by size (largest first)
        self.results.sort(key=lambda x: x[1], reverse=True)
    
    def generate_markdown_report(self) -> str:
        """Generate markdown report with file list and paths"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_files = len(self.results)
        total_size = sum(size for _, size in self.results)
        
        report = f"""# Video File Scan Report

**Generated:** {timestamp}  
**Size Threshold:** {self.config['size_threshold_gb']}GB  
**Total Files Found:** {total_files}  
**Total Size:** {total_size:.2f}GB  

## Video Files (Sorted by Size)

"""
        
        # File list with details
        for file_path, size_gb in self.results:
            filename = os.path.basename(file_path)
            report += f"- **{filename}** ({size_gb:.2f}GB)\n"
        
        report += "\n## File Paths (Copy/Paste Ready)\n\n```\n"
        
        # Just the paths for easy copying
        for file_path, _ in self.results:
            report += f"{file_path}\n"
        
        report += "```\n"
        
        return report
    
    def save_report(self, content: str, scan_path: str):
        """Save markdown report to file"""
        if self.config.get('save_to_scan_dir', True):
            output_filename = self.config['output_filename']
            output_file = os.path.join(scan_path, output_filename)
        else:
            output_file = self.config['output_filename']
            
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📝 Report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Scan directories for large video files")
    parser.add_argument("path", help="Root directory to scan")
    parser.add_argument("-c", "--config", default="config.json", 
                       help="Configuration file path (default: config.json)")
    parser.add_argument("-o", "--output", help="Output markdown file (overrides config)")
    parser.add_argument("-s", "--size", type=float, 
                       help="Size threshold in GB (overrides config)")
    parser.add_argument("-e", "--exclude", 
                       help="Regex pattern to exclude files (overrides config, e.g., '_compressed|_backup')")
    
    args = parser.parse_args()
    
    # Initialize scanner
    scanner = VideoScanner(args.config)
    
    # Override config with command line args if provided
    if args.output:
        # If output contains path, use as-is; otherwise save to scan directory
        if os.path.dirname(args.output):
            scanner.config['output_filename'] = args.output
            scanner.config['save_to_scan_dir'] = False
        else:
            scanner.config['output_filename'] = args.output
            scanner.config['save_to_scan_dir'] = True
    else:
        scanner.config['save_to_scan_dir'] = True
        
    if args.size:
        scanner.config['size_threshold_gb'] = args.size
    if args.exclude:
        scanner.config['exclude_pattern'] = args.exclude
    
    # Validate path
    if not os.path.exists(args.path):
        print(f"❌ Error: Path '{args.path}' does not exist")
        return 1
    
    try:
        # Run the scan
        scanner.scan_concurrent(args.path)
        
        # Generate and save report
        if scanner.results:
            report = scanner.generate_markdown_report()
            scanner.save_report(report, args.path)
            print(f"✅ Scan complete! Found {len(scanner.results)} files totaling {sum(s for _, s in scanner.results):.2f}GB")
        else:
            print(f"ℹ️  No video files found above {scanner.config['size_threshold_gb']}GB threshold")
        
        return 0
        
    except KeyboardInterrupt:
        scanner.progress.stop()
        print("\n⏹️  Scan interrupted by user")
        return 1
    except Exception as e:
        scanner.progress.stop()
        print(f"\n❌ Error during scan: {e}")
        return 1


if __name__ == "__main__":
    exit(main())