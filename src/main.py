#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smart Clipboard - Quick Test Version
"""

import sys
import os
import json
import time
import threading
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleClipboardMonitor:
    def __init__(self):
        self.running = False
        self.last_content = ""
        self.data_file = Path.home() / '.smart_clipboard_test' / 'data.json'
        self.setup_directories()
        self.load_data()
        
    def setup_directories(self):
        """Create necessary directories and files"""
        try:
            self.data_file.parent.mkdir(exist_ok=True)
            logger.info(f"Directory created/verified: {self.data_file.parent}")
            
            if not self.data_file.exists():
                self.data_file.write_text('[]', encoding='utf-8')
                logger.info(f"Data file created: {self.data_file}")
        except Exception as e:
            logger.error(f"Error setting up directories: {e}")
            
    def load_data(self):
        """Load data from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"Loaded {len(self.data)} items from {self.data_file}")
        except FileNotFoundError:
            self.data = []
            logger.info("No data file found, starting with empty list")
        except json.JSONDecodeError:
            self.data = []
            logger.warning("Data file corrupted, starting with empty list")
            if self.data_file.exists():
                backup = self.data_file.with_suffix('.json.bak')
                self.data_file.rename(backup)
                logger.info(f"Corrupted file backed up to {backup}")
                
    def save_data(self):
        """Save data to JSON file"""
        try:
            self.data_file.parent.mkdir(exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.data)} items to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            
    def get_clipboard(self):
        """Get text from clipboard using tkinter"""
        try:
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return text
        except:
            return None
            
    def show_dialog(self, content):
        """Show dialog to get name and tags for copied content"""
        dialog = tk.Tk()
        dialog.title("Save to Clipboard")
        dialog.geometry("400x300")
        
        # Preview
        tk.Label(dialog, text="Copied Text:", font=('Arial', 10, 'bold')).pack(pady=5)
        text_frame = tk.Frame(dialog)
        text_frame.pack(fill='both', expand=True, padx=10)
        
        text_widget = tk.Text(text_frame, height=4, wrap='word')
        preview_text = content[:200] + ('...' if len(content) > 200 else '')
        text_widget.insert('1.0', preview_text)
        text_widget.config(state='disabled')
        text_widget.pack(side='left', fill='both', expand=True)
        
        # Name input
        tk.Label(dialog, text="Name (optional):").pack(pady=5)
        name_entry = tk.Entry(dialog, width=40)
        name_entry.pack()
        
        # Tags input
        tk.Label(dialog, text="Tags (comma separated):").pack(pady=5)
        tags_entry = tk.Entry(dialog, width=40)
        tags_entry.pack()
        
        result = {'saved': False, 'name': '', 'tags': []}
        
        def save():
            result['saved'] = True
            result['name'] = name_entry.get().strip()
            tags_text = tags_entry.get().strip()
            result['tags'] = [t.strip() for t in tags_text.split(',') if t.strip()]
            dialog.destroy()
            
        def skip():
            dialog.destroy()
            
        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Save", command=save).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Skip", command=skip).pack(side='left', padx=5)
        
        dialog.mainloop()
        return result if result['saved'] else None
        
    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Monitoring started...")
        while self.running:
            try:
                content = self.get_clipboard()
                if content and content != self.last_content and content.strip():
                    logger.info(f"New content detected: {content[:50]}...")
                    result = self.show_dialog(content)
                    
                    if result:
                        item = {
                            'id': len(self.data) + 1,
                            'text': content,
                            'name': result['name'] or f"Item {len(self.data) + 1}",
                            'tags': result['tags'],
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        self.data.append(item)
                        self.save_data()
                        logger.info(f"Saved: {item['name']}")
                        
                    self.last_content = content
                    
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(2)
                
    def start(self):
        """Start the application"""
        self.running = True
        thread = threading.Thread(target=self.monitor_loop, daemon=True)
        thread.start()
        
        # Control window
        root = tk.Tk()
        root.title("Smart Clipboard - Running")
        root.geometry("300x150")
        
        tk.Label(root, text="✅ Smart Clipboard is running", 
                fg="green", font=('Arial', 12, 'bold')).pack(pady=20)
        tk.Label(root, text="Copy any text to test").pack()
        
        def show_history():
            history = tk.Toplevel(root)
            history.title("History")
            history.geometry("500x300")
            
            text_widget = tk.Text(history)
            text_widget.pack(fill='both', expand=True)
            
            for item in self.data[-10:]:
                text_widget.insert('end', 
                    f"📝 {item['name']}\n"
                    f"📋 {item['text'][:100]}...\n"
                    f"🏷️ Tags: {', '.join(item['tags'])}\n"
                    f"⏰ {item['timestamp']}\n"
                    f"{'─'*50}\n\n")
                    
        tk.Button(root, text="Show History", command=show_history).pack(pady=5)
        tk.Button(root, text="Exit", command=root.destroy).pack()
        
        root.mainloop()
        self.running = False

if __name__ == "__main__":
    app = SimpleClipboardMonitor()
    app.start()