#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#lol
"""
Smart Clipboard - Windows Edition
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
import subprocess

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
        print("Warning: pywin32 not installed. Some features may be limited.")
else:
    HAS_WIN32 = False

# Safer UTF-8 handling for both console and windowed modes
if sys.platform == 'win32':
    try:
        # Only try to set encoding if we're in a console
        if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        if sys.stderr is not None and hasattr(sys.stderr, 'buffer'):
            import io
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except (AttributeError, io.UnsupportedOperation):
        # Running in windowed mode - ignore encoding setup
        pass
# Configure logging
log_dir = Path.home() / '.smart_clipboard'
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

class WindowsClipboardMonitor:
    def __init__(self):
        self.running = False
        self.last_content = ""
        self.data_dir = Path.home() / '.smart_clipboard'
        self.data_file = self.data_dir / 'data.json'
        self.setup_directories()
        self.load_data()
        
        # Windows-specific: Add to startup
        if HAS_WIN32:
            self.add_to_startup()
        
    def setup_directories(self):
        """Create necessary directories and files"""
        try:
            self.data_dir.mkdir(exist_ok=True)
            logger.info(f"Directory created/verified: {self.data_dir}")
            
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
            self.data_dir.mkdir(exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.data)} items to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def add_to_startup(self):
        """Add application to Windows startup"""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            # Open registry key
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                                winreg.KEY_SET_VALUE)
            
            # Get current executable path
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                app_path = sys.executable
            else:
                # Running as script
                app_path = sys.executable + ' "' + os.path.abspath(__file__) + '"'
            
            # Set registry value
            winreg.SetValueEx(key, "SmartClipboard", 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            logger.info("Added to Windows startup")
        except Exception as e:
            logger.error(f"Failed to add to startup: {e}")
    
    def remove_from_startup(self):
        """Remove application from Windows startup"""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                                winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "SmartClipboard")
            winreg.CloseKey(key)
            logger.info("Removed from Windows startup")
        except Exception as e:
            logger.error(f"Failed to remove from startup: {e}")
    
    def get_clipboard_win32(self):
        """Get clipboard content using win32api (faster)"""
        if not HAS_WIN32:
            return self.get_clipboard_tk()
            
        try:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                    data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                    return data.decode('utf-8', errors='ignore') if data else None
            finally:
                win32clipboard.CloseClipboard()
        except:
            return self.get_clipboard_tk()
        return None
    
    def get_clipboard_tk(self):
        """Fallback: Get text from clipboard using tkinter"""
        try:
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return text
        except:
            return None
    
    def get_clipboard(self):
        """Get clipboard content (Windows optimized)"""
        if HAS_WIN32:
            return self.get_clipboard_win32()
        return self.get_clipboard_tk()
    
    def show_dialog(self, content):
        """Show dialog to get name and tags for copied content"""
        dialog = tk.Tk()
        dialog.title("Smart Clipboard - Save Item")
        dialog.geometry("450x350")
        
        # Set icon if available
        try:
            if os.path.exists("icon.ico"):
                dialog.iconbitmap("icon.ico")
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
        
        scrollbar = tk.Scrollbar(text_frame, command=text_widget.yview)
        scrollbar.pack(side='right', fill='y')
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Name input
        tk.Label(dialog, text="🏷️ Name (optional):", font=('Arial', 10, 'bold')).pack(pady=(10, 0))
        name_entry = tk.Entry(dialog, width=50, font=('Arial', 10))
        name_entry.pack(pady=5)
        name_entry.focus_set()
        
        # Tags input
        tk.Label(dialog, text="🔖 Tags (comma separated):", font=('Arial', 10, 'bold')).pack()
        tags_entry = tk.Entry(dialog, width=50, font=('Arial', 10))
        tags_entry.pack(pady=5)
        
        # Preview of existing tags (quick select)
        tag_frame = tk.Frame(dialog)
        tag_frame.pack(pady=5)
        
        # Get common tags from existing data
        all_tags = []
        for item in self.data:
            all_tags.extend(item.get('tags', []))
        common_tags = list(set(all_tags))[:5]  # Top 5 unique tags
        
        if common_tags:
            tk.Label(tag_frame, text="Quick tags:").pack(side='left', padx=5)
            for tag in common_tags:
                btn = tk.Button(tag_frame, text=tag, 
                              command=lambda t=tag: tags_entry.insert('end', t + ', '))
                btn.pack(side='left', padx=2)
        
        result = {'saved': False, 'name': '', 'tags': []}
        
        def save():
            result['saved'] = True
            result['name'] = name_entry.get().strip()
            tags_text = tags_entry.get().strip()
            result['tags'] = [t.strip() for t in tags_text.split(',') if t.strip()]
            dialog.destroy()
            
        def save_and_close():
            save()
            self.show_notification("Item Saved", f"Saved to clipboard history")
            
        def skip():
            dialog.destroy()
            
        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="💾 Save", command=save_and_close, 
                 bg="#4CAF50", fg="white", width=10, height=1).pack(side='left', padx=5)
        tk.Button(btn_frame, text="⏭️ Skip", command=skip, 
                 bg="#f44336", fg="white", width=10, height=1).pack(side='left', padx=5)
        
        # Bind Enter key to save
        dialog.bind('<Return>', lambda e: save_and_close())
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
    
    def show_notification(self, title, message):
        """Show Windows notification"""
        try:
            if HAS_WIN32:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=3)
            else:
                print(f"Notification: {title} - {message}")
        except:
            pass
    
    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Monitoring started...")
        self.show_notification("Smart Clipboard", "Monitoring started")
        
        while self.running:
            try:
                content = self.get_clipboard()
                if content and content != self.last_content and content.strip():
                    logger.info(f"New content detected: {content[:50]}...")
                    
                    # Optional: Beep on new content
                    if HAS_WIN32:
                        import winsound
                        winsound.Beep(500, 100)
                    
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
    
    def show_history_window(self):
        """Show history window with search"""
        history = tk.Toplevel()
        history.title("Smart Clipboard - History")
        history.geometry("700x500")
        
        # Set icon
        try:
            if os.path.exists("icon.ico"):
                history.iconbitmap("icon.ico")
        except:
            pass
        
        # Search frame
        search_frame = tk.Frame(history)
        search_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(search_frame, text="🔍 Search:").pack(side='left')
        search_entry = tk.Entry(search_frame, width=40)
        search_entry.pack(side='left', padx=5)
        
        # Results frame with scrollbar
        result_frame = tk.Frame(history)
        result_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(result_frame)
        scrollbar.pack(side='right', fill='y')
        
        text_widget = tk.Text(result_frame, yscrollcommand=scrollbar.set, 
                             font=('Consolas', 10), wrap='word')
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=text_widget.yview)
        
        def update_display(items=None):
            text_widget.delete('1.0', tk.END)
            display_items = items if items is not None else self.data[-50:]
            
            for item in reversed(display_items):
                text_widget.insert('end', 
                    f"📝 {item['name']}\n"
                    f"📋 {item['text'][:100]}...\n"
                    f"🏷️ Tags: {', '.join(item['tags'])}\n"
                    f"⏰ {item['timestamp']}\n"
                    f"{'─'*70}\n\n")
        
        def do_search():
            query = search_entry.get().lower()
            if not query:
                update_display()
                return
                
            results = []
            for item in self.data:
                if (query in item['name'].lower() or 
                    query in item['text'].lower() or
                    any(query in tag.lower() for tag in item['tags'])):
                    results.append(item)
            update_display(results)
        
        search_entry.bind('<Return>', lambda e: do_search())
        tk.Button(search_frame, text="Search", command=do_search).pack(side='left', padx=5)
        tk.Button(search_frame, text="Clear", command=lambda: [search_entry.delete(0, 'end'), update_display()]).pack(side='left')
        
        # Export button
        def export_data():
            """Export data with proper file dialog and error handling"""
            try:
                from tkinter import filedialog
                
                # Ask user where to save
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    initialdir=str(Path.home() / "Desktop"),
                    initialfile=f"clipboard_export_{time.strftime('%Y%m%d_%H%M%S')}.json",
                    title="Save Clipboard Export As"
                )
                
                if not file_path:  # User cancelled
                    return
                    
                # Save the data
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                    
                # Show success message
                messagebox.showinfo(
                    "Export Successful", 
                    f"✅ Successfully exported {len(self.data)} items to:\n{file_path}"
                )
                
                # Open containing folder (optional)
                if messagebox.askyesno("Open Folder", "Would you like to open the containing folder?"):
                    os.startfile(os.path.dirname(file_path))
                    
            except PermissionError:
                messagebox.showerror(
                    "Permission Error", 
                    "Cannot write to that location. Please choose a different folder."
                )
            except Exception as e:
                messagebox.showerror(
                    "Export Failed", 
                    f"Error exporting data:\n{str(e)}"
                )
                logger.error(f"Export error: {e}")
        #quick expoert tot desktop
        def quick_export_to_desktop():
            """Quick export directly to desktop with timestamp"""
            try:
                # Find desktop path (handles OneDrive cases)
                desktop = Path.home() / "Desktop"
                
                if not desktop.exists():
                    # Try OneDrive Desktop
                    desktop = Path.home() / "OneDrive" / "Desktop"
                    
                if not desktop.exists():
                    # Fallback to Documents
                    desktop = Path.home() / "Documents"
        
                if not desktop.exists():
                    # Last resort - current directory
                    desktop = Path.cwd()
                    
                # Generate filename with timestamp
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f"clipboard_quick_export_{timestamp}.json"
                filepath = desktop / filename
                
                # Save the data
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                
                # Show success message with option to open folder
                result = messagebox.askyesno(
                    "Quick Export Successful", 
                    f"✅ Exported {len(self.data)} items to:\n{filepath}\n\nWould you like to open the folder?"
                )
                
                if result:
                    # Open containing folder
                    if sys.platform == 'win32':
                        os.startfile(str(desktop))
                    else:
                        import subprocess
                        subprocess.run(['open', str(desktop)])  # macOS
                        # subprocess.run(['xdg-open', str(desktop)])  # Linux
                    
                logger.info(f"Quick export completed: {filepath}")
                
            except PermissionError:
                messagebox.showerror(
                    "Permission Denied", 
                    "Cannot write to Desktop. Try running as administrator."
                )
            except Exception as e:
                messagebox.showerror("Export Failed", f"Error: {str(e)}")
                logger.error(f"Quick export error: {e}")
        #import
        def import_data():
            """Import data from JSON file"""
            try:
                from tkinter import filedialog
                
                file_path = filedialog.askopenfilename(
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    initialdir=str(Path.home() / "Desktop"),
                    title="Select Clipboard Data to Import"
                )
                
                if not file_path:
                    return
                    
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                
                if not isinstance(imported_data, list):
                    messagebox.showerror("Invalid Format", "The file does not contain valid clipboard data.")
                    return
                    
                # Ask how to handle import
                choice = messagebox.askyesnocancel(
                    "Import Options", 
                    f"Found {len(imported_data)} items.\n\n"
                    "Yes: Replace existing data\n"
                    "No: Append to existing data\n"
                    "Cancel: Abort import"
                )
                
                if choice is None:  # Cancel
                    return
                elif choice:  # Yes - Replace
                    self.data = imported_data
                else:  # No - Append
                    # Update IDs to avoid conflicts
                    next_id = max([item.get('id', 0) for item in self.data] or [0]) + 1
                    for item in imported_data:
                        if 'id' in item:
                            item['id'] = next_id
                            next_id += 1
                    self.data.extend(imported_data)
                
                self.save_data()
                messagebox.showinfo(
                    "Import Successful", 
                    f"✅ Successfully imported {len(imported_data)} items."
                )
                
                # Refresh history window if open
                update_display()
                
            except json.JSONDecodeError:
                messagebox.showerror("Invalid File", "The selected file is not a valid JSON file.")
            except Exception as e:
                messagebox.showerror("Import Failed", f"Error importing data:\n{str(e)}")
                logger.error(f"Import error: {e}")
        
        # Button frame for import/export
        action_frame = tk.Frame(history)
        action_frame.pack(pady=5)

        tk.Button(action_frame, text="📤 Export...", command=export_data,
                bg="#4CAF50", fg="white", width=12).pack(side='left', padx=2)
        tk.Button(action_frame, text="📥 Import...", command=import_data,
                bg="#2196F3", fg="white", width=12).pack(side='left', padx=2)
        tk.Button(action_frame, text="⚡ Quick Export", command=quick_export_to_desktop,
                bg="#FF9800", fg="white", width=12).pack(side='left', padx=2)
        update_display()
    
    def show_settings_window(self):
        """Show settings window"""
        settings = tk.Toplevel()
        settings.title("Smart Clipboard - Settings")
        settings.geometry("400x300")
        
        # Set icon
        try:
            if os.path.exists("icon.ico"):
                settings.iconbitmap("icon.ico")
        except:
            pass
        
        tk.Label(settings, text="⚙️ Settings", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Startup option
        startup_var = tk.BooleanVar(value=True)
        tk.Checkbutton(settings, text="Run on Windows startup", 
                      variable=startup_var).pack(anchor='w', padx=20, pady=5)
        
        # Notification option
        notif_var = tk.BooleanVar(value=True)
        tk.Checkbutton(settings, text="Show notifications", 
                      variable=notif_var).pack(anchor='w', padx=20, pady=5)
        
        # Check interval
        tk.Label(settings, text="Check interval (seconds):").pack(anchor='w', padx=20)
        interval_var = tk.StringVar(value="1")
        tk.Entry(settings, textvariable=interval_var, width=10).pack(anchor='w', padx=20)
        
        # Data location
        tk.Label(settings, text=f"Data file: {self.data_file}", 
                font=('Arial', 8)).pack(pady=20)
        
        def save_settings():
            # Update startup setting
            if startup_var.get():
                self.add_to_startup()
            else:
                self.remove_from_startup()
            
            # Update interval
            try:
                new_interval = float(interval_var.get())
                if new_interval > 0:
                    self.check_interval = new_interval
            except:
                pass
            
            messagebox.showinfo("Settings", "Settings saved")
            settings.destroy()
        
        tk.Button(settings, text="Save", command=save_settings, 
                 bg="#4CAF50", fg="white").pack(pady=10)
    
    def start(self):
        """Start the application"""
        self.running = True
        self.check_interval = 1.0
        thread = threading.Thread(target=self.monitor_loop, daemon=True)
        thread.start()
        self.show_control_window()
        # # Create system tray icon if available
        # try:
        #     self.setup_tray()
        # except:
        #     self.show_control_window()
    
    def setup_tray(self):
        """Setup system tray icon"""
        try:
            import pystray
            from PIL import Image
            
            # Create or load icon
            if os.path.exists("icon.ico"):
                image = Image.open("icon.ico")
            else:
                # Create simple icon
                image = Image.new('RGB', (64, 64), color='blue')
            
            def on_quit():
                self.running = False
                self.icon.stop()
                sys.exit()
            
            menu = pystray.Menu(
                pystray.MenuItem("Show History", self.show_history_window),
                pystray.MenuItem("Search", lambda: self.show_history_window()),
                pystray.MenuItem("Settings", self.show_settings_window),
                pystray.MenuItem("About", lambda: messagebox.showinfo("About", 
                    "Smart Clipboard v1.0\nWindows Edition")),
                pystray.MenuItem("Exit", on_quit)
            )
            
            self.icon = pystray.Icon("smart_clipboard", image, "Smart Clipboard", menu)
            threading.Thread(target=self.icon.run, daemon=True).start()
            
        except ImportError:
            logger.warning("pystray not installed, showing control window")
            self.show_control_window()
    
    def show_control_window(self):
        """Show simple control window (fallback)"""
        root = tk.Tk()
        root.title("Smart Clipboard")
        root.geometry("350x200")
        
        # Set icon
        try:
            if os.path.exists("icon.ico"):
                root.iconbitmap("icon.ico")
        except:
            pass
        
        tk.Label(root, text="✅ Smart Clipboard is running", 
                fg="green", font=('Arial', 12, 'bold')).pack(pady=20)
        tk.Label(root, text="Copy any text to save it").pack()
        
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="📋 History", command=self.show_history_window,
                 width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="⚙️ Settings", command=self.show_settings_window,
                 width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="❌ Exit", command=root.destroy,
                 width=15).pack(side='left', padx=5)
        
        root.mainloop()
        self.running = False

def main():
    """Main entry point"""
    # Check if running as Windows app
    if sys.platform != 'win32':
        print("This version is designed for Windows only.")
        sys.exit(1)
    
    app = WindowsClipboardMonitor()
    app.start()

if __name__ == "__main__":
    main()