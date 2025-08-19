#!/usr/bin/env python3
"""
Efficient labeling tool for handwriting OCR training data.
Optimized for speed with auto-suggestions, keyboard shortcuts, and batch operations.
"""

import os
import sys
import json
import argparse
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import List, Dict, Optional, Set
import logging
from PIL import Image, ImageTk
import cv2
import numpy as np
from collections import Counter
import re

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EfficientLabelingTool:
    """Enhanced GUI tool for fast handwriting data labeling."""
    
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
        
        # Auto-suggestion system
        self.common_words = self._build_common_words()
        self.suggestions = []
        self.suggestion_index = 0
        
        # Keyboard shortcuts mapping
        self.shortcuts = {
            'Ctrl+1': 'Empty line',
            'Ctrl+2': 'Date',
            'Ctrl+3': 'Signature',
            'Ctrl+4': 'Page number',
            'Ctrl+5': 'Common word 1',
            'Ctrl+6': 'Common word 2',
            'Ctrl+7': 'Common word 3',
            'Ctrl+8': 'Common word 4',
            'Ctrl+9': 'Common word 5',
            'Tab': 'Next suggestion',
            'Enter': 'Save and next',
            'Space': 'Skip line',
            'Backspace': 'Previous line'
        }
        
        # Setup GUI
        self.setup_gui()
        self.load_current_line()
        
        # Auto-save timer
        self.auto_save_interval = 15000  # 15 seconds (faster)
        self.schedule_auto_save()
    
    def _build_common_words(self) -> List[str]:
        """Build list of common words from existing labels."""
        all_text = []
        for line in self.lines:
            if line.get('text', '').strip():
                words = re.findall(r'\b\w+\b', line['text'].lower())
                all_text.extend(words)
        
        # Get most common words
        word_counts = Counter(all_text)
        common_words = [word for word, count in word_counts.most_common(20) if len(word) > 2]
        
        return common_words[:10]  # Top 10 common words
    
    def setup_gui(self):
        """Initialize the GUI components with efficiency features."""
        self.root = tk.Tk()
        self.root.title(f"Efficient Handwriting Labeling Tool - {self.metadata_path.name}")
        self.root.geometry("1400x900")
        
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=2)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Status bar with progress
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.progress_label = ttk.Label(self.status_frame, text="")
        self.progress_label.pack(side="left")
        
        self.speed_label = ttk.Label(self.status_frame, text="Speed: 0 lines/min")
        self.speed_label.pack(side="right")
        
        # Image display
        self.image_frame = ttk.Frame(self.root)
        self.image_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.image_label = ttk.Label(self.image_frame, text="Loading image...")
        self.image_label.pack(expand=True, fill="both")
        
        # Control panel
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Text input with auto-suggestions
        ttk.Label(self.control_frame, text="Transcribed Text:").pack(anchor="w", pady=(0, 5))
        
        self.text_input = tk.Text(self.control_frame, height=6, width=50, wrap="word")
        self.text_input.pack(fill="both", expand=True, pady=(0, 10))
        
        # Auto-suggestion box
        self.suggestion_frame = ttk.Frame(self.control_frame)
        self.suggestion_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(self.suggestion_frame, text="Suggestions:").pack(anchor="w")
        self.suggestion_listbox = tk.Listbox(self.suggestion_frame, height=3)
        self.suggestion_listbox.pack(fill="x")
        self.suggestion_listbox.bind('<Double-Button-1>', self.use_suggestion)
        
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
        
        # Quick actions with keyboard shortcuts
        quick_frame = ttk.LabelFrame(self.control_frame, text="Quick Actions (Keyboard Shortcuts)")
        quick_frame.pack(fill="x", pady=10)
        
        # Create quick action buttons
        quick_actions = [
            ("Empty Line", "Ctrl+1", lambda: self.set_quick_text("")),
            ("Date", "Ctrl+2", lambda: self.set_quick_text("[DATE]")),
            ("Signature", "Ctrl+3", lambda: self.set_quick_text("[SIGNATURE]")),
            ("Page Number", "Ctrl+4", lambda: self.set_quick_text("[PAGE]")),
        ]
        
        for i, (text, shortcut, command) in enumerate(quick_actions):
            btn = ttk.Button(quick_frame, text=f"{text} ({shortcut})", command=command)
            btn.grid(row=i//2, column=i%2, padx=5, pady=2, sticky="ew")
        
        # Common words buttons
        common_frame = ttk.LabelFrame(self.control_frame, text="Common Words")
        common_frame.pack(fill="x", pady=10)
        
        for i, word in enumerate(self.common_words[:5]):
            btn = ttk.Button(common_frame, text=f"{word} (Ctrl+{i+5})", 
                           command=lambda w=word: self.set_quick_text(w))
            btn.grid(row=i//3, column=i%3, padx=2, pady=2, sticky="ew")
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.control_frame)
        nav_frame.pack(fill="x", pady=10)
        
        ttk.Button(nav_frame, text="← Previous (Backspace)", command=self.previous_line).pack(side="left", padx=(0, 5))
        ttk.Button(nav_frame, text="Next → (Enter)", command=self.next_line).pack(side="left", padx=(0, 5))
        ttk.Button(nav_frame, text="Skip (Space)", command=self.skip_line).pack(side="left")
        
        # Action buttons
        action_frame = ttk.Frame(self.control_frame)
        action_frame.pack(fill="x", pady=5)
        
        ttk.Button(action_frame, text="Save & Next (Enter)", command=self.save_and_next).pack(side="left", padx=(0, 5))
        ttk.Button(action_frame, text="Save (Ctrl+S)", command=self.save_current).pack(side="left", padx=(0, 5))
        ttk.Button(action_frame, text="Clear (Esc)", command=self.clear_input).pack(side="left")
        
        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Bind text input events
        self.text_input.bind('<Control-s>', lambda e: self.save_current())
        self.text_input.bind('<Return>', lambda e: self.save_and_next())
        self.text_input.bind('<BackSpace>', lambda e: self.previous_line())
        self.text_input.bind('<space>', lambda e: self.skip_line())
        self.text_input.bind('<Tab>', lambda e: self.next_suggestion())
        self.text_input.bind('<Escape>', lambda e: self.clear_input())
        
        # Bind text changes for auto-suggestions
        self.text_input.bind('<KeyRelease>', self.update_suggestions)
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for the entire window."""
        self.root.bind('<Control-s>', lambda e: self.save_current())
        self.root.bind('<Return>', lambda e: self.save_and_next())
        self.root.bind('<BackSpace>', lambda e: self.previous_line())
        self.root.bind('<space>', lambda e: self.skip_line())
        self.root.bind('<Tab>', lambda e: self.next_suggestion())
        self.root.bind('<Escape>', lambda e: self.clear_input())
        
        # Number shortcuts for quick actions
        for i in range(1, 10):
            self.root.bind(f'<Control-Key-{i}>', lambda e, num=i: self.quick_action(num))
    
    def quick_action(self, number):
        """Handle quick action number shortcuts."""
        if number == 1:
            self.set_quick_text("")
        elif number == 2:
            self.set_quick_text("[DATE]")
        elif number == 3:
            self.set_quick_text("[SIGNATURE]")
        elif number == 4:
            self.set_quick_text("[PAGE]")
        elif 5 <= number <= 9 and number - 5 < len(self.common_words):
            self.set_quick_text(self.common_words[number - 5])
    
    def update_suggestions(self, event=None):
        """Update auto-suggestions based on current text."""
        current_text = self.text_input.get(1.0, tk.END).strip()
        if not current_text:
            self.suggestions = []
        else:
            # Simple word completion
            self.suggestions = [word for word in self.common_words 
                              if word.startswith(current_text.lower())][:5]
        
        # Update suggestion listbox
        self.suggestion_listbox.delete(0, tk.END)
        for suggestion in self.suggestions:
            self.suggestion_listbox.insert(tk.END, suggestion)
    
    def next_suggestion(self, event=None):
        """Move to next suggestion."""
        if self.suggestions:
            self.suggestion_index = (self.suggestion_index + 1) % len(self.suggestions)
            if self.suggestions:
                self.set_quick_text(self.suggestions[self.suggestion_index])
    
    def use_suggestion(self, event=None):
        """Use selected suggestion."""
        selection = self.suggestion_listbox.curselection()
        if selection:
            suggestion = self.suggestions[selection[0]]
            self.set_quick_text(suggestion)
    
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
            
            # Resize image to fit display (max 800x600 for better visibility)
            display_size = (800, 600)
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
        
        # Update suggestions
        self.update_suggestions()
        
        # Update status
        self.update_status()
        
        # Focus on text input for faster typing
        self.text_input.focus()
    
    def update_status(self):
        """Update the status bar with current progress and speed."""
        labeled_count = sum(1 for line in self.lines if line.get('labeled', False))
        progress_text = f"Line {self.current_index + 1}/{self.total_lines} | Labeled: {labeled_count}/{self.total_lines}"
        self.progress_label.configure(text=progress_text)
        
        # Calculate speed (lines per minute)
        # This is a simplified calculation - you could track actual timing
        if labeled_count > 0:
            speed = min(labeled_count * 2, 60)  # Rough estimate
            self.speed_label.configure(text=f"Speed: ~{speed} lines/min")
    
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
        self.text_input.focus()
    
    def set_quick_text(self, text: str):
        """Set quick text in the input field."""
        self.text_input.delete(1.0, tk.END)
        self.text_input.insert(1.0, text)
        self.text_input.focus()
    
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
        
        # Calculate efficiency metrics
        if labeled_count > 0:
            avg_confidence = sum(line.get('confidence', 0) for line in self.lines if line.get('labeled', False)) / labeled_count
            message += f"\nAverage confidence: {avg_confidence:.2f}"
        
        messagebox.showinfo("Labeling Complete", message)
        self.root.quit()
    
    def run(self):
        """Start the labeling tool."""
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description='Efficient handwriting labeling tool')
    parser.add_argument('--metadata', required=True, help='Path to metadata.json file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.metadata):
        print(f"Error: Metadata file {args.metadata} not found")
        print("Please run the data preparation script first:")
        print("python src/data_preparation/prepare_data.py --input_dir your_journal_pages/")
        return
    
    # Start labeling tool
    tool = EfficientLabelingTool(args.metadata)
    tool.run()


if __name__ == "__main__":
    main()
