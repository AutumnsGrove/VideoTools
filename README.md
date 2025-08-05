# VideoTools 🎥

A collection of Python utilities for video processing, file synchronization, and batch file management. These tools were designed to streamline common video workflow tasks and provide easy-to-use interfaces for file operations.

## 🚀 Tools Overview

### 📁 `file_verifier.py`
**Modern Gradio interface for file existence verification**

A web-based tool that helps you track which files from a batch processing queue still exist versus which have been processed or moved. Perfect for resuming interrupted video compression tasks.

**Features:**
- Parse space-separated or newline-separated file paths
- Categorize files into "Missing/Processed" and "Ready for Processing"
- Display file details (modification time, size) in a clean table
- Copy-paste ready file paths for continuing batch operations
- Modern, responsive UI with Inter font and neutral color scheme

**Usage:**
```bash
python file_verifier.py
# Opens web interface on http://localhost:7861
```

**Created with:** Claude Code for solving the common problem of tracking batch processing progress when operations are interrupted.

---

### 🔄 `sync.py`
**Camera file synchronization utility**

Intelligent file synchronization tool for organizing camera files (photos/videos) from DCIM folders into date-based directory structures.

**Features:**
- Automatic date-based folder organization
- Duplicate detection and handling
- Progress tracking with real-time updates
- Comprehensive logging
- Safe file operations with verification

**Key Functions:**
- `CameraSync`: Main synchronization class
- `print_progress()`: Real-time progress indicators
- Smart date extraction from file metadata
- Conflict resolution for duplicate files

---

### ⚡ `sync_concurrent.py`
**High-performance concurrent file synchronization**

Enhanced version of the sync utility with concurrent processing capabilities for handling large file sets efficiently.

**Features:**
- Multi-threaded file operations
- Concurrent duplicate detection
- Enhanced performance for large datasets
- Maintains all safety features of the base sync tool

---

### 🎬 `video_analyzer.py`
**AI-powered video content analysis**

Advanced video analysis tool powered by Qwen2.5-VL-7B-Instruct vision model for intelligent video content understanding.

**Features:**
- Vision-language model integration
- Video frame analysis and interpretation
- AI-powered content description
- Gradio web interface for easy interaction

**Requirements:**
- PyTorch with CUDA support
- Transformers library
- Qwen2.5-VL model (7B parameters)
- Flash Attention 2 for optimized performance

---

### 🎞️ `video_combiner.py`
**Intelligent video concatenation and merging**

Professional-grade video combination tool with smart file grouping, quality analysis, and batch processing capabilities.

**Features:**
- Automatic video grouping by date/time
- Quality and format analysis
- FFmpeg-based concatenation
- Comprehensive logging and error handling
- Progress tracking for batch operations
- Human-readable file size and duration reporting

**Key Functions:**
- `VideoCombiner`: Main processing class
- Smart video grouping algorithms
- Quality-aware merging decisions
- Robust error handling and recovery

---

## 🔗 Related Projects

### [Video Compressor](https://github.com/yourusername/video-compressor)
A separate repository containing advanced video compression tools with Gradio interfaces. The Video Compressor folder in this project is maintained as an independent repository for focused development.

**Note:** The Video Compressor tools complement these VideoTools utilities, providing a complete video processing pipeline from analysis through compression and verification.

---

## 🛠️ Installation & Setup

### Prerequisites
```bash
# Core dependencies
pip install gradio pathlib humanize

# For video_analyzer.py
pip install torch transformers qwen-vl-utils
pip install flash-attn --no-build-isolation

# System requirements
# - FFmpeg (for video operations)
# - Python 3.8+
```

### Quick Start
1. Clone this repository
2. Install dependencies
3. Run any tool directly:
   ```bash
   python file_verifier.py      # Web interface on :7861
   python video_analyzer.py     # AI analysis interface
   python sync.py              # Command-line sync tool
   ```

---

## 📝 Development Notes

### Code Style & Architecture
- **Modern Python**: Type hints, pathlib, f-strings
- **Error Handling**: Comprehensive exception handling and logging
- **User Experience**: Progress indicators, clear status messages
- **Modularity**: Clean class-based architecture
- **Documentation**: Inline docstrings and clear variable names

### Design Philosophy
Each tool is designed to be:
- **Standalone**: Run independently without complex setup
- **Intuitive**: Clear interfaces and helpful error messages
- **Robust**: Handle edge cases and provide meaningful feedback
- **Efficient**: Optimized for real-world file processing scenarios

---

## 🤖 About

**Created with [Claude Code](https://claude.ai/code)**

These tools were developed using Claude Code to solve real-world video processing and file management challenges. Each utility addresses specific pain points in video workflows:

- **File Verifier**: Born from the frustration of interrupted batch processing
- **Sync Tools**: Designed for efficient camera file organization
- **Video Analyzer**: Leveraging AI for intelligent content understanding
- **Video Combiner**: Professional-grade concatenation with smart grouping

The development process emphasized practical usability, robust error handling, and modern user interfaces.

---

## 🚀 Future Enhancements

- [ ] Integration with cloud storage providers
- [ ] Advanced video quality metrics
- [ ] Batch processing queue management
- [ ] Enhanced AI analysis capabilities
- [ ] Cross-platform packaging and distribution

---

## 📄 License

MIT License - feel free to use, modify, and distribute these tools for your own video processing needs.

---

*Part of a comprehensive video processing toolkit. See also: [Video Compressor](https://github.com/yourusername/video-compressor) for advanced compression workflows.*