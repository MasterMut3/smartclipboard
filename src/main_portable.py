#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smart Clipboard - Portable Edition
Stores data in the SAME folder as the executable
"""

import sys
import os
import json
import time
import threading
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# IMPORTANT: Get the folder where the EXE is located
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    APP_FOLDER = Path(sys.executable).parent
else:
    # Running as script during development
    APP_FOLDER = Path(__file__).parent.parent

# Windows-specific imports
if sys.platform == 'win32':
    try:
        import win32clipboard
        import win32con
        import win32gui
        import win32api
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
else:
    HAS_WIN32 = False

# Configure logging to APP FOLDER
log_dir = APP_FOLDER / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PortableClipboardMonitor:
    def __init__(self):
        self.running = False
        self.last_content = ""
        
        # PORTABLE: Store data in the same folder as the EXE
        self.data_file = APP_FOLDER / 'clipboard_data.json'
        self.setup_directories()
        self.load_data()
        
    def setup_directories(self):
        """Create necessary files in app folder"""
        try:
            # Just create the data file if it doesn't exist
            if not self.data_file.exists():
                self.data_file.write_text('[]', encoding='utf-8')
                logger.info(f"Data file created: {self.data_file}")
        except Exception as e:
            logger.error(f"Error setting up: {e}")
            
    def load_data(self):
        """Load data from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"Loaded {len(self.data)} items from {self.data_file}")
        except FileNotFoundError:
            self.data = []
            logger.info("No data file found, starting fresh")
        except json.JSONDecodeError:
            self.data = []
            logger.warning("Data file corrupted, starting fresh")
            if self.data_file.exists():
                backup = self.data_file.with_suffix('.json.bak')
                self.data_file.rename(backup)
                
    def save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.data)} items")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def get_clipboard(self):
        """Get text from clipboard"""
        if HAS_WIN32:
            try:
                win32clipboard.OpenClipboard()
                try:
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                        data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                        return data.decode('utf-8', errors='ignore') if data else None
                finally:
                    win32clipboard.CloseClipboard()
            except:
                pass
        
        # Fallback to tkinter
        try:
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return text
        except:
            return None
    
    def show_dialog(self, content):
        """Show dialog to get name and tags"""
        dialog = tk.Tk()
        dialog.title("Smart Clipboard - Save Item")
        dialog.geometry("450x350")
        
        # Set icon if available (look in APP_FOLDER)
        icon_path = APP_FOLDER / 'icon.ico'
        if icon_path.exists():
            try:
                dialog.iconbitmap(str(icon_path))
            except:
                pass
        
        # Make it modal
        dialog.focus_set()
        dialog.grab_set()
        
        # Preview
        tk.Label(dialog, text="📋 Copied Text:", font=('Arial', 10, 'bold')).pack(pady=5)
        text_frame = tk.Frame(dialog)
        text_frame.pack(fill='both', expand=True, padx=10)
        
        text_widget = tk.Text(text_frame, height=4, wrap='word', font=('Consolas', 9))
        preview_text = content[:300] + ('...' if len(content) > 300 else '')
        text_widget.insert('1.0', preview_text)
        text_widget.config(state='disabled')
        text_widget.pack(side='left', fill='both', expand=True)
        
        # Name input
        tk.Label(dialog, text="🏷️ Name (optional):", font=('Arial', 10, 'bold')).pack(pady=(10, 0))
        name_entry = tk.Entry(dialog, width=50, font=('Arial', 10))
        name_entry.pack(pady=5)
        name_entry.focus_set()
        
        # Tags input
        tk.Label(dialog, text="🔖 Tags (comma separated):", font=('Arial', 10, 'bold')).pack()
        tags_entry = tk.Entry(dialog, width=50, font=('Arial', 10))
        tags_entry.pack(pady=5)
        
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
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="💾 Save", command=save,
                 bg="#4CAF50", fg="white", width=10).pack(side='left', padx=5)
        tk.Button(btn_frame, text="⏭️ Skip", command=skip,
                 bg="#f44336", fg="white", width=10).pack(side='left', padx=5)
        
        dialog.bind('<Return>', lambda e: save())
        dialog.bind('<Escape>', lambda e: skip())
        
        # Center window
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        dialog.mainloop()
        return result if result['saved'] else None
    
    def show_history(self):
        """Show history window"""
        history = tk.Toplevel()
        history.title("Smart Clipboard - History")
        history.geometry("600x400")
        
        # Set icon
        icon_path = APP_FOLDER / 'icon.ico'
        if icon_path.exists():
            try:
                history.iconbitmap(str(icon_path))
            except:
                pass
        
        # Text widget with scrollbar
        text_frame = tk.Frame(history)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set,
                             font=('Consolas', 10), wrap='word')
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Display items
        for item in reversed(self.data[-50:]):
            text_widget.insert('end', 
                f"📝 {item['name']}\n"
                f"📋 {item['text'][:100]}...\n"
                f"🏷️ Tags: {', '.join(item['tags'])}\n"
                f"⏰ {item['timestamp']}\n"
                f"{'─'*70}\n\n")
        
        # Export button
        def export():
            export_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                initialdir=str(APP_FOLDER),
                initialfile=f"export_{time.strftime('%Y%m%d')}.json"
            )
            if export_path:
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Success", f"Exported to {export_path}")
        
        tk.Button(history, text="📤 Export", command=export).pack(pady=5)
        
        # Show where data is stored
        location_label = tk.Label(history, 
                                 text=f"Data file: {self.data_file.name}",
                                 font=('Arial', 8), fg="gray")
        location_label.pack(side='bottom', pady=2)
    
    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info(f"Monitoring started. Data file: {self.data_file}")
        while self.running:
            try:
                content = self.get_clipboard()
                if content and content != self.last_content and content.strip():
                    logger.info(f"New content detected")
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
                        
                    self.last_content = content
                    
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(2)
    
    def start(self):
        """Start the application"""
        self.running = True
        thread = threading.Thread(target=self.monitor_loop, daemon=True)
        thread.start()
        
        # Simple control window
        root = tk.Tk()
        root.title("Smart Clipboard - Portable")
        root.geometry("350x250")
        
        # Set icon
        icon_path = APP_FOLDER / 'icon.ico'
        if icon_path.exists():
            try:
                root.iconbitmap(str(icon_path))
            except:
                pass
        
        tk.Label(root, text="✅ Smart Clipboard (Portable)", 
                fg="green", font=('Arial', 12, 'bold')).pack(pady=20)
        
        # Show stats
        tk.Label(root, text=f"Items saved: {len(self.data)}").pack()
        tk.Label(root, text=f"Data file: {self.data_file.name}").pack()
        
        tk.Button(root, text="📋 History", command=self.show_history).pack(pady=10)
        tk.Button(root, text="❌ Exit", command=root.destroy).pack()
        
        # Show location info
        location_text = f"📍 Data folder: {APP_FOLDER}"
        tk.Label(root, text=location_text, font=('Arial', 7), fg="gray").pack(side='bottom', pady=5)
        
        root.mainloop()
        self.running = False

def main():
    # Show where data will be stored on startup
    print(f"\n📁 Smart Clipboard Portable")
    print(f"📂 Data file: {APP_FOLDER / 'clipboard_data.json'}")
    print(f"🚀 Starting...\n")
    
    app = PortableClipboardMonitor()
    app.start()

if __name__ == "__main__":
    main()
