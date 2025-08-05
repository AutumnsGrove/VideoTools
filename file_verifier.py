#!/usr/bin/env python3

import os
import gradio as gr
from pathlib import Path
from datetime import datetime

def parse_file_paths(file_paths_text):
    """Parse the input text and extract file paths."""
    if not file_paths_text.strip():
        return []
    
    # First try to split by newlines (normal case)
    lines = file_paths_text.strip().split('\n')
    paths = []
    
    # If we have only one line, it might be space-separated paths
    if len(lines) == 1 and ' ' in lines[0]:
        # Split by spaces, but be careful with paths that contain spaces
        # Look for common video file extensions to identify path boundaries
        text = lines[0]
        extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
        
        # Find all extension positions
        ext_positions = []
        for ext in extensions:
            pos = 0
            while True:
                pos = text.find(ext, pos)
                if pos == -1:
                    break
                ext_positions.append(pos + len(ext))
                pos += len(ext)
        
        # Sort positions and split the text at these points
        ext_positions.sort()
        
        if ext_positions:
            start = 0
            for end_pos in ext_positions:
                # Find the next space after the extension (if any)
                next_space = text.find(' ', end_pos)
                if next_space == -1:
                    # This is the last file
                    path = text[start:].strip()
                    if path:
                        paths.append(path)
                    break
                else:
                    path = text[start:next_space].strip()
                    if path:
                        paths.append(path)
                    start = next_space + 1
        else:
            # Fallback: split by spaces (may break paths with spaces)
            potential_paths = text.split(' ')
            paths = [p.strip() for p in potential_paths if p.strip()]
    else:
        # Normal newline-separated processing
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):  # Skip empty lines and comments
                # Remove quotes if present
                if line.startswith('"') and line.endswith('"'):
                    line = line[1:-1]
                elif line.startswith("'") and line.endswith("'"):
                    line = line[1:-1]
                paths.append(line)
    
    return paths

def get_file_info(file_path):
    """Get file modification time and size."""
    try:
        stat = os.stat(file_path)
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        size_mb = stat.st_size / (1024 * 1024)
        return mod_time.strftime('%Y-%m-%d %H:%M:%S'), f"{size_mb:.1f} MB"
    except:
        return "Unknown", "Unknown"

def verify_files(file_paths_text, progress=gr.Progress()):
    """Main function to verify file existence and categorize them."""
    if not file_paths_text.strip():
        return "Please enter file paths to verify.", ""
    
    file_paths = parse_file_paths(file_paths_text)
    
    if not file_paths:
        return "No valid file paths found in input.", ""
    
    existing_files = []
    missing_files = []
    total_files = len(file_paths)
    
    # Process each file path
    for i, file_path in enumerate(file_paths):
        progress_percent = (i / total_files)
        progress(progress_percent, desc=f"Checking {Path(file_path).name}")
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            mod_time, size = get_file_info(file_path)
            existing_files.append({
                'path': file_path,
                'mod_time': mod_time,
                'size': size
            })
        else:
            missing_files.append(file_path)
    
    progress(1.0, desc="Complete!")
    
    # Format results
    processed_missing_output = format_processed_missing_section(missing_files, existing_files)
    next_up_output = format_next_up_section(existing_files)
    
    return processed_missing_output, next_up_output

def format_processed_missing_section(missing_files, existing_files):
    """Format the processed/missing files section."""
    output = []
    
    # Header
    output.append("# Already Processed / Missing Files")
    output.append(f"**Total Missing/Processed:** {len(missing_files)}")
    output.append(f"**Files Still Available:** {len(existing_files)}")
    output.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("")
    
    if missing_files:
        output.append("## Missing Files (Possibly Already Processed)")
        output.append("```")
        for file_path in missing_files:
            output.append(file_path)
        output.append("```")
        output.append("")
    else:
        output.append("## No Missing Files")
        output.append("All files in the input list still exist.")
        output.append("")
    
    return "\n".join(output)

def format_next_up_section(existing_files):
    """Format the next up files section."""
    if not existing_files:
        return "# No Files Remaining\n\nAll files appear to be missing or processed."
    
    output = []
    
    # Header
    output.append("# Next Up - Files Ready for Processing")
    output.append(f"**Total Files:** {len(existing_files)}")
    output.append("")
    
    # File details table
    output.append("## File Details")
    output.append("| File | Modified | Size |")
    output.append("|------|----------|------|")
    
    for file_info in existing_files:
        file_name = Path(file_info['path']).name
        output.append(f"| {file_name} | {file_info['mod_time']} | {file_info['size']} |")
    
    output.append("")
    
    # Copy-paste ready file paths
    output.append("## Copy-Paste Ready File Paths")
    output.append("```")
    for file_info in existing_files:
        output.append(file_info['path'])
    output.append("```")
    
    return "\n".join(output)

def create_interface():
    """Create and configure the Gradio interface."""
    
    # Create a modern, clean theme
    theme = gr.themes.Base(
        primary_hue="slate",
        secondary_hue="gray",
        neutral_hue="stone",
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
    ).set(
        body_background_fill="*neutral_50",
        background_fill_primary="white",
        background_fill_secondary="*neutral_100",
        border_color_primary="*neutral_200",
        button_primary_background_fill="*primary_600",
        button_primary_background_fill_hover="*primary_700"
    )
    
    with gr.Blocks(theme=theme, title="File Verifier") as interface:
        gr.Markdown("# 📁 File Path Verifier")
        gr.Markdown("""
        Verify which files from your list still exist and which are missing (possibly already processed).
        Perfect for checking video compression progress or any batch file processing tasks.
        """)
        
        with gr.Row():
            with gr.Column():
                file_paths_input = gr.Textbox(
                    label="File Paths (one per line)",
                    placeholder="Enter file paths, one per line:\n/path/to/file1.mp4\n/path/to/file2.mp4\n/path/to/file3.mp4",
                    lines=15,
                    max_lines=30
                )
                
                verify_btn = gr.Button("🔍 Verify Files", variant="primary")
        
        with gr.Row():
            with gr.Column():
                processed_output = gr.Textbox(
                    label="Already Processed / Missing Files",
                    lines=10,
                    max_lines=20,
                    show_copy_button=True,
                    placeholder="Missing files will appear here..."
                )
            
            with gr.Column():
                next_up_output = gr.Textbox(
                    label="Next Up - Ready for Processing",
                    lines=10,
                    max_lines=20,
                    show_copy_button=True,
                    placeholder="Files still available for processing will appear here..."
                )
        
        # Wire up the button
        verify_btn.click(
            fn=verify_files,
            inputs=[file_paths_input],
            outputs=[processed_output, next_up_output]
        )
        
        gr.Markdown("""
        ### Tips:
        - Paste file paths from your compression queue or any batch processing list
        - Files that don't exist are likely already processed or moved
        - Use the "Copy-Paste Ready File Paths" section to continue processing remaining files
        - Supports quoted paths and skips comment lines (starting with #)
        """)
    
    return interface

def main():
    """Launch the Gradio app."""
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7861,  # Different port from video transcriber
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()