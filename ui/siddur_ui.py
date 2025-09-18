"""
Hebrew Audio Siddur - User Interface
A simple, accessible UI for generating and playing prayer services.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import sys
from pathlib import Path
from datetime import datetime, date
import os

# Add paths for imports
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))

# Import our existing modules
from tts_generate import build_tefilla_for_date, get_current_tefilla_type, show_hebrew_calendar_info
from tefilla_rules import HebrewCalendar


class SiddurUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hebrew Audio Siddur")
        self.root.geometry("600x500")
        self.root.configure(bg='#f0f0f0')
        
        # Make window resizable but set minimum size
        self.root.minsize(500, 400)
        
        # Center the window on screen
        self.center_window()
        
        # Audio playback variables
        self.current_process = None
        self.is_playing = False
        
        # Create the UI
        self.create_widgets()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create all UI widgets."""
        # Main title
        title_label = tk.Label(
            self.root,
            text="🎵 Hebrew Audio Siddur",
            font=("Arial", 24, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # Date and time info
        self.create_date_info()
        
        # Main buttons frame
        buttons_frame = tk.Frame(self.root, bg='#f0f0f0')
        buttons_frame.pack(expand=True, fill='both', padx=40, pady=20)
        
        # "Now" button (top, prominent)
        self.create_now_button(buttons_frame)
        
        # Separator
        separator = tk.Frame(buttons_frame, height=2, bg='#bdc3c7')
        separator.pack(fill='x', pady=20)
        
        # Tefilla buttons
        self.create_tefilla_buttons(buttons_frame)
        
        # Status frame
        self.create_status_frame()
    
    def create_date_info(self):
        """Create date and time information display."""
        info_frame = tk.Frame(self.root, bg='#f0f0f0')
        info_frame.pack(pady=10)
        
        # Current date
        current_date = date.today().strftime("%A, %B %d, %Y")
        date_label = tk.Label(
            info_frame,
            text=f"📅 {current_date}",
            font=("Arial", 14),
            bg='#f0f0f0',
            fg='#34495e'
        )
        date_label.pack()
        
        # Current time and suggested tefilla
        current_time = datetime.now().strftime("%I:%M %p")
        suggested_tefilla = get_current_tefilla_type().title()
        time_label = tk.Label(
            info_frame,
            text=f"🕐 {current_time} - Suggested: {suggested_tefilla}",
            font=("Arial", 12),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        time_label.pack()
    
    def create_now_button(self, parent):
        """Create the prominent 'Now' button."""
        now_frame = tk.Frame(parent, bg='#f0f0f0')
        now_frame.pack(fill='x', pady=10)
        
        self.now_button = tk.Button(
            now_frame,
            text="🎯 NOW\nPlay Current Prayer",
            font=("Arial", 18, "bold"),
            bg='#27ae60',
            fg='white',
            relief='raised',
            bd=3,
            height=3,
            command=self.play_current_tefilla,
            cursor='hand2'
        )
        self.now_button.pack(fill='x', padx=20)
        
        # Add hover effects
        self.now_button.bind("<Enter>", lambda e: self.now_button.config(bg='#2ecc71'))
        self.now_button.bind("<Leave>", lambda e: self.now_button.config(bg='#27ae60'))
    
    def create_tefilla_buttons(self, parent):
        """Create the three tefilla buttons."""
        tefilla_frame = tk.Frame(parent, bg='#f0f0f0')
        tefilla_frame.pack(fill='x', pady=10)
        
        # Button configurations
        tefilla_configs = [
            {
                'name': 'Shacharis',
                'icon': '🌅',
                'color': '#3498db',
                'hover_color': '#5dade2',
                'command': lambda: self.play_tefilla('shacharis')
            },
            {
                'name': 'Mincha',
                'icon': '☀️',
                'color': '#f39c12',
                'hover_color': '#f7dc6f',
                'command': lambda: self.play_tefilla('mincha')
            },
            {
                'name': 'Maariv',
                'icon': '🌙',
                'color': '#8e44ad',
                'hover_color': '#bb8fce',
                'command': lambda: self.play_tefilla('maariv')
            }
        ]
        
        # Create buttons in a row
        for i, config in enumerate(tefilla_configs):
            button = tk.Button(
                tefilla_frame,
                text=f"{config['icon']}\n{config['name']}",
                font=("Arial", 16, "bold"),
                bg=config['color'],
                fg='white',
                relief='raised',
                bd=3,
                height=2,
                command=config['command'],
                cursor='hand2'
            )
            button.pack(side='left', expand=True, fill='x', padx=5)
            
            # Add hover effects
            button.bind("<Enter>", lambda e, color=config['hover_color']: e.widget.config(bg=color))
            button.bind("<Leave>", lambda e, color=config['color']: e.widget.config(bg=color))
    
    def create_status_frame(self):
        """Create status and progress frame."""
        status_frame = tk.Frame(self.root, bg='#f0f0f0')
        status_frame.pack(fill='x', padx=20, pady=10)
        
        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="Ready to play prayers",
            font=("Arial", 12),
            bg='#f0f0f0',
            fg='#27ae60'
        )
        self.status_label.pack()
        
        # Progress bar
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=300
        )
        self.progress.pack(pady=5)
        self.progress.pack_forget()  # Hide initially
        
        # Stop button (hidden initially)
        self.stop_button = tk.Button(
            status_frame,
            text="⏹️ Stop",
            font=("Arial", 12),
            bg='#e74c3c',
            fg='white',
            command=self.stop_playback,
            cursor='hand2'
        )
        self.stop_button.pack(pady=5)
        self.stop_button.pack_forget()  # Hide initially
    
    def update_status(self, message, color='#34495e'):
        """Update the status message."""
        self.status_label.config(text=message, fg=color)
        self.root.update()
    
    def show_progress(self, show=True):
        """Show or hide the progress bar."""
        if show:
            self.progress.pack(pady=5)
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.pack_forget()
    
    def show_stop_button(self, show=True):
        """Show or hide the stop button."""
        if show:
            self.stop_button.pack(pady=5)
        else:
            self.stop_button.pack_forget()
    
    def play_current_tefilla(self):
        """Play the tefilla appropriate for current time."""
        tefilla_type = get_current_tefilla_type()
        self.play_tefilla(tefilla_type)
    
    def play_tefilla(self, tefilla_type):
        """Play a specific tefilla type."""
        if self.is_playing:
            messagebox.showwarning("Already Playing", "A prayer is already being played. Please stop it first.")
            return
        
        # Run in a separate thread to avoid blocking the UI
        thread = threading.Thread(target=self._build_and_play_tefilla, args=(tefilla_type,))
        thread.daemon = True
        thread.start()
    
    def _build_and_play_tefilla(self, tefilla_type):
        """Build and play tefilla in a separate thread."""
        try:
            self.is_playing = True
            self.root.after(0, lambda: self.update_status(f"Building {tefilla_type.title()}...", '#f39c12'))
            self.root.after(0, lambda: self.show_progress(True))
            self.root.after(0, lambda: self.show_stop_button(True))
            
            # Build the tefilla
            output_file = build_tefilla_for_date(tefilla_type, date.today())
            
            if not output_file.exists():
                raise FileNotFoundError(f"Generated file not found: {output_file}")
            
            self.root.after(0, lambda: self.update_status(f"Playing {tefilla_type.title()}...", '#27ae60'))
            
            # Play the audio file
            self._play_audio_file(output_file)
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda: self.update_status(error_msg, '#e74c3c'))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.is_playing = False
            self.root.after(0, lambda: self.show_progress(False))
            self.root.after(0, lambda: self.show_stop_button(False))
            self.root.after(0, lambda: self.update_status("Ready to play prayers", '#27ae60'))
    
    def _play_audio_file(self, file_path):
        """Play an audio file using the system's default player."""
        try:
            # Try different methods to play audio on Windows
            if sys.platform == "win32":
                # Use Windows Media Player or default audio player
                self.current_process = subprocess.Popen([
                    "cmd", "/c", "start", "", str(file_path)
                ], shell=True)
            else:
                # For other platforms, try common audio players
                for player in ["vlc", "mplayer", "mpv", "play"]:
                    try:
                        self.current_process = subprocess.Popen([player, str(file_path)])
                        break
                    except FileNotFoundError:
                        continue
                else:
                    raise FileNotFoundError("No audio player found")
            
            # Wait for playback to complete
            if self.current_process:
                self.current_process.wait()
                
        except Exception as e:
            raise Exception(f"Could not play audio file: {e}")
    
    def stop_playback(self):
        """Stop the current audio playback."""
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process = None
            except:
                pass
        
        self.is_playing = False
        self.show_progress(False)
        self.show_stop_button(False)
        self.update_status("Playback stopped", '#e74c3c')
    
    def on_closing(self):
        """Handle window closing."""
        if self.is_playing:
            self.stop_playback()
        self.root.destroy()
    
    def run(self):
        """Start the UI main loop."""
        self.root.mainloop()


def main():
    """Main entry point for the UI."""
    try:
        app = SiddurUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Startup Error", f"Could not start the application: {e}")


if __name__ == "__main__":
    main()
