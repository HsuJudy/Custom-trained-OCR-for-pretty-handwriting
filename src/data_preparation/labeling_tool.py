#!/usr/bin/env python3
"""
Interactive labeling tool for handwriting OCR training data.
Provides efficient line-by-line annotation with keyboard shortcuts.
"""

import os
import sys
import json
import argparse
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import List, Dict, Optional
import logging
from PIL import Image, ImageTk
import cv2
import numpy as np

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HandwritingLabelingTool:
    """Interactive GUI tool for labeling handwriting data."""
    
    def __init__(self, metadata_path: str):
        self.metadata_path = Path(metadata_path)
        self.data_dir = self.metadata_path.parent
        
        # Load metadata
        with open(self.metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        self.lines = self.metadata['lines']
        self.current_index = 0
        self.total_lines = len(self.lines)
        
        # Find first unlabeled line
        for i, line in enumerate(self.lines):
            if not line.get('labeled', False):
                self.current_index = i
                break
        
        # Setup GUI
        self.setup_gui()
        self.load_current_line()
        
        # Auto-save timer
        self.auto_save_interval = 30000  # 30 seconds
        self.schedule_auto_save()
    
    def setup_gui(self):
        """Initialize the GUI components."""
        self.root = tk.Tk()
        self.root.title(f"Handwriting Labeling Tool - {self.metadata_path.name}")
        self.root.geometry("1200x800")
        
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Status bar
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.progress_label = ttk.Label(self.status_frame, text="")
        self.progress_label.pack(side="left")
        
        self.auto_save_label = ttk.Label(self.status_frame, text="Auto-save: Enabled")
        self.auto_save_label.pack(side="right")
        
        # Image display
        self.image_frame = ttk.Frame(self.root)
        self.image_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.image_label = ttk.Label(self.image_frame, text="Loading image...")
        self.image_label.pack(expand=True, fill="both")
        
        # Control panel
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Text input
        ttk.Label(self.control_frame, text="Transcribed Text:").pack(anchor="w", pady=(0, 5))
        
        self.text_input = tk.Text(self.control_frame, height=8, width=50, wrap="word")
        self.text_input.pack(fill="both", expand=True, pady=(0, 10))
        
        # Confidence slider
        ttk.Label(self.control_frame, text="Confidence:").pack(anchor="w", pady=(0, 5))
        
        self.confidence_var = tk.DoubleVar(value=1.0)
        self.confidence_slider = ttk.Scale(
            self.control_frame, 
            from_=0.0, 
            to=1.0, 
            variable=self.confidence_var,
            orient="horizontal"
        )
        self.confidence_slider.pack(fill="x", pady=(0, 10))
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.control_frame)
        buttons_frame.pack(fill="x", pady=10)
        
        # Navigation buttons
        nav_frame = ttk.Frame(buttons_frame)
        nav_frame.pack(fill="x", pady=5)
        
        ttk.Button(nav_frame, text="← Previous", command=self.previous_line).pack(side="left", padx=(0, 5))
        ttk.Button(nav_frame, text="Next →", command=self.next_line).pack(side="left", padx=(0, 5))
        ttk.Button(nav_frame, text="Skip", command=self.skip_line).pack(side="left")
        
        # Action buttons
        action_frame = ttk.Frame(buttons_frame)
        action_frame.pack(fill="x", pady=5)
        
        ttk.Button(action_frame, text="Save & Next", command=self.save_and_next).pack(side="left", padx=(0, 5))
        ttk.Button(action_frame, text="Save", command=self.save_current).pack(side="left", padx=(0, 5))
        ttk.Button(action_frame, text="Clear", command=self.clear_input).pack(side="left")
        
        # Quick actions
        quick_frame = ttk.Frame(buttons_frame)
        quick_frame.pack(fill="x", pady=5)
        
        ttk.Label(quick_frame, text="Quick Actions:").pack(anchor="w")
        
        quick_buttons_frame = ttk.Frame(quick_frame)
        quick_buttons_frame.pack(fill="x", pady=5)
        
        ttk.Button(quick_buttons_frame, text="Empty Line", command=lambda: self.set_quick_text("")).pack(side="left", padx=(0, 5))
        ttk.Button(quick_buttons_frame, text="Date", command=lambda: self.set_quick_text("[DATE]")).pack(side="left", padx=(0, 5))
        ttk.Button(quick_buttons_frame, text="Signature", command=lambda: self.set_quick_text("[SIGNATURE]")).pack(side="left")
        
        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Bind text input events
        self.text_input.bind('<Control-s>', lambda e: self.save_current())
        self.text_input.bind('<Control-n>', lambda e: self.next_line())
        self.text_input.bind('<Control-p>', lambda e: self.previous_line())
        self.text_input.bind('<Control-k>', lambda e: self.skip_line())
        self.text_input.bind('<Control-Return>', lambda e: self.save_and_next())
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for the entire window."""
        self.root.bind('<Control-s>', lambda e: self.save_current())
        self.root.bind('<Control-n>', lambda e: self.next_line())
        self.root.bind('<Control-p>', lambda e: self.previous_line())
        self.root.bind('<Control-k>', lambda e: self.skip_line())
        self.root.bind('<Control-Return>', lambda e: self.save_and_next())
        self.root.bind('<Escape>', lambda e: self.clear_input())
    
    def load_current_line(self):
        """Load and display the current line image."""
        if self.current_index >= self.total_lines:
            self.show_completion_message()
            return
        
        line_data = self.lines[self.current_index]
        image_path = line_data['image_path']
        
        # Load and display image
        try:
            image = Image.open(image_path)
            
            # Resize image to fit display (max 600x400)
            display_size = (600, 400)
            image.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo, text="")
            self.image_label.image = photo  # Keep a reference
            
        except Exception as e:
            self.image_label.configure(text=f"Error loading image: {e}")
        
        # Load existing text if available
        existing_text = line_data.get('text', '')
        self.text_input.delete(1.0, tk.END)
        self.text_input.insert(1.0, existing_text)
        
        # Set confidence
        confidence = line_data.get('confidence', 1.0)
        self.confidence_var.set(confidence)
        
        # Update status
        self.update_status()
    
    def update_status(self):
        """Update the status bar with current progress."""
        labeled_count = sum(1 for line in self.lines if line.get('labeled', False))
        progress_text = f"Line {self.current_index + 1}/{self.total_lines} | Labeled: {labeled_count}/{self.total_lines}"
        self.progress_label.configure(text=progress_text)
    
    def save_current(self):
        """Save the current line's transcription."""
        if self.current_index >= self.total_lines:
            return
        
        text = self.text_input.get(1.0, tk.END).strip()
        confidence = self.confidence_var.get()
        
        self.lines[self.current_index].update({
            'text': text,
            'confidence': confidence,
            'labeled': True
        })
        
        logger.info(f"Saved line {self.current_index + 1}: {text[:50]}...")
    
    def next_line(self):
        """Move to the next line."""
        if self.current_index < self.total_lines - 1:
            self.current_index += 1
            self.load_current_line()
    
    def previous_line(self):
        """Move to the previous line."""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_line()
    
    def skip_line(self):
        """Skip the current line (mark as unlabeled)."""
        if self.current_index < self.total_lines:
            self.lines[self.current_index]['labeled'] = False
            self.lines[self.current_index]['text'] = ''
            self.lines[self.current_index]['confidence'] = 0.0
            
            self.next_line()
    
    def save_and_next(self):
        """Save current line and move to next."""
        self.save_current()
        self.next_line()
    
    def clear_input(self):
        """Clear the text input."""
        self.text_input.delete(1.0, tk.END)
    
    def set_quick_text(self, text: str):
        """Set quick text in the input field."""
        self.text_input.delete(1.0, tk.END)
        self.text_input.insert(1.0, text)
    
    def schedule_auto_save(self):
        """Schedule the next auto-save."""
        self.save_metadata()
        self.root.after(self.auto_save_interval, self.schedule_auto_save)
    
    def save_metadata(self):
        """Save the metadata to file."""
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info("Auto-saved metadata")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def show_completion_message(self):
        """Show completion message when all lines are processed."""
        labeled_count = sum(1 for line in self.lines if line.get('labeled', False))
        
        message = f"Labeling complete!\n\nLabeled: {labeled_count}/{self.total_lines} lines"
        if labeled_count < self.total_lines:
            message += f"\nSkipped: {self.total_lines - labeled_count} lines"
        
        messagebox.showinfo("Labeling Complete", message)
        self.root.quit()
    
    def run(self):
        """Start the labeling tool."""
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description='Interactive handwriting labeling tool')
    parser.add_argument('--metadata', required=True, help='Path to metadata.json file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.metadata):
        print(f"Error: Metadata file {args.metadata} not found")
        print("Please run the data preparation script first:")
        print("python src/data_preparation/prepare_data.py --input_dir your_journal_pages/")
        return
    
    # Start labeling tool
    tool = HandwritingLabelingTool(args.metadata)
    tool.run()


if __name__ == "__main__":
    main()
