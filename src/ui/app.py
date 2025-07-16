# RJ Auto Metadata
# Copyright (C) 2025 Riiicil
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# src/ui/app.py
import os
import sys
import threading
import time
import queue
import random
import json
import platform
import re
import sys
import uuid
import webbrowser
import tkinter as tk
import tkinter.messagebox
import customtkinter as ctk
import importlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from src.utils.logging import log_message
from src.utils.file_utils import read_api_keys, is_writable_directory
from src.utils.analytics import send_analytics_event
from src.config.config import MEASUREMENT_ID, API_SECRET, ANALYTICS_URL
from src.processing.batch_processing import batch_process_files
from src.ui.widgets import ToolTip
from src.ui.dialogs import CompletionMessageManager
from src.utils.system_checks import (
    check_ghostscript, check_ffmpeg, check_gtk_dependencies,
    set_console_visibility
)
from src.metadata.exif_writer import check_exiftool_exists
from src.api.api_key_checker import check_api_keys_status

APP_VERSION = "3.7.0"
CONFIG_FILE = "config.json"

class MetadataApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.default_font_family = "Aptos_display"
        from src.utils.logging import set_log_handler
        set_log_handler(self._log)
        def font_exists(font_name):
            try:
                test_label = tk.Label(text="Test", font=(font_name, 12))
                exists = test_label.cget("font").split()[0] == font_name
                test_label.destroy()
                return exists
            except Exception:
                return False

        if not font_exists(self.default_font_family):
            self._log(f"Font '{self.default_font_family}' not found, using default system font", "warning")
            self.default_font_family = "Arial"

        self.font_small = ctk.CTkFont(family=self.default_font_family, size=10)
        self.font_normal = ctk.CTkFont(family=self.default_font_family, size=12)
        self.font_medium = ctk.CTkFont(family=self.default_font_family, size=13)
        self.font_large = ctk.CTkFont(family=self.default_font_family, size=15, weight="bold")
        self.font_title = ctk.CTkFont(family=self.default_font_family, size=18, weight="bold")

        self.start_time = None
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self._log_queue_after_id = None
        self._stop_request_time = None
        self._in_summary_block = False

        self._perform_startup_checks()

        self.configure(fg_color=("#f0f0f5", "#2d2d30"))

        self.analytics_enabled_var = tk.BooleanVar(value=True)
        self.installation_id = tk.StringVar(value="")

        self.title("Auto Metadata")

        from src.utils.system_checks import _get_base_dir
        base_dir = _get_base_dir()

        try:
            self.iconbitmap_path = os.path.join(base_dir, 'assets', 'icon1.ico')
            if os.path.exists(self.iconbitmap_path):
                self.iconbitmap(self.iconbitmap_path)
            else:
                self.iconbitmap_path = None
        except Exception as e:
            self.iconbitmap_path = None

        self.geometry("600x800")
        self.minsize(600, 800)

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.rename_files_var = tk.BooleanVar(value=False)
        self.delay_var = tk.StringVar(value="10")
        self.workers_var = tk.StringVar(value="1")
        self._actual_api_keys = []
        self.show_api_keys_var = tk.BooleanVar(value=False)
        self.console_visible_var = tk.BooleanVar(value=True)

        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.stopped_count = 0

        self.theme_folder = os.path.join(os.path.dirname(__file__), "themes")
        self.available_themes = ["dark", "light", "system"]

        if os.path.exists(self.theme_folder):
            import glob
            custom_themes = glob.glob(os.path.join(self.theme_folder, "*.json"))
            for theme_path in custom_themes:
                theme_name = os.path.splitext(os.path.basename(theme_path))[0]
                self.available_themes.append(theme_name)

        self.config_path = self._get_config_path()
        self.processed_cache = {}
        self.cache_file = os.path.join(os.path.dirname(self.config_path), "processed_cache.json")

        self.auto_kategori_var = tk.BooleanVar(value=False)
        self.auto_foldering_var = tk.BooleanVar(value=False)
        self._needs_initial_save = False

        try:
            gemini_api = importlib.import_module('src.api.gemini_api')
            gemini_models = list(getattr(gemini_api, 'GEMINI_MODELS', []))
        except Exception:
            gemini_models = []
        self.available_models = ["Auto Rotation"] + [m for m in gemini_models if m not in ("Auto Rotation",)]
        self.model_var = tk.StringVar(value="Auto Rotation")
        self.keyword_count_var = tk.StringVar(value="49")
        self.priority_var = tk.StringVar(value="Detailed")
        self.available_priorities = ["Detailed", "Balanced", "Less"]

        self._create_ui()
        self._process_log_queue()
        self._load_settings()
        self._init_analytics()
        self._load_cache()

        if self._needs_initial_save:
            self._save_settings()
            self._needs_initial_save = False

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.is_executable = self._is_running_as_executable()

        self.completion_manager = CompletionMessageManager(
            self,
            self.config_path,
            self.font_normal,
            self.font_medium,
            self.font_large,
            self.iconbitmap_path
        )

        if self.is_executable:
            print("Application is running as executable.")
            self.executable_timeout = 2.0
            self.executable_max_wait = 5.0
        else:
            print("Application is running as script Python.")
            self.executable_timeout = 3.0
            self.executable_max_wait = 10.0

    def _perform_startup_checks(self):
        self._log("Checking external dependencies...", "info")

        self._log("Checking availability of Exiftool...", "info")
        exiftool_ok = check_exiftool_exists()
        if not exiftool_ok:
            self._log("Exiftool not found.", "error")
            tkinter.messagebox.showerror("Critical Error",
                "Exiftool not found or not working.\n"
                "Application cannot run without Exiftool.\n"
                "Please make sure it is installed and in PATH.")
            self.destroy()
            sys.exit(1)
        else:
            self._log("Exiftool found.", "success")

        self._log("Checking availability of Ghostscript...", "info")
        gs_ok = check_ghostscript()
        if not gs_ok:
            self._log("Ghostscript not found. Processing AI/EPS will fail.", "warning")
            tkinter.messagebox.showwarning("Warning",
                "Ghostscript not found or not working.\n"
                "Please make sure it is installed and in PATH.\n"
                "Processing AI/EPS will fail.")
        else:
            self._log("Ghostscript found.", "success")

        self._log("Checking availability of FFmpeg...", "info")
        ffmpeg_ok = check_ffmpeg()
        if not ffmpeg_ok:
            self._log("FFmpeg not found. Processing Video will fail.", "warning")
            tkinter.messagebox.showwarning("Warning",
                "FFmpeg not found or not working.\n"
                "Please make sure it is installed and in PATH.\n"
                "Processing Video (MP4/MKV) will fail.")
        else:
            self._log("FFmpeg ditemukan.", "success")

        self._log("Checking availability of GTK dependencies (cairocffi)...", "info")
        gtk_ok = check_gtk_dependencies()
        if not gtk_ok:
            self._log("GTK dependencies (cairocffi) not found. Processing SVG might fail.", "warning")
            tkinter.messagebox.showwarning("Warning",
                "Failed to import GTK dependencies (cairocffi).\n"
                "This might be due to missing GTK3 Runtime or incorrect configuration.\n"
                "Processing SVG might fail.")
        else:
             self._log("GTK dependencies (cairocffi) found.", "success")

        self._log("Dependency checks completed.", "info")


    def _is_running_as_executable(self):
        if getattr(sys, 'frozen', False):
            return True
        for attr in ['__compiled__', '_MEIPASS', '_MEIPASS2']:
            if hasattr(sys, attr):
                return True
        try:
            exe_path = os.path.realpath(sys.executable).lower()
            if (exe_path.endswith('.exe') and 'python' not in exe_path) or '.exe.' in exe_path:
                return True
        except Exception:
            pass
        return False

    def _create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_panel = ctk.CTkFrame(self, corner_radius=10)
        main_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_panel.grid_columnconfigure(0, weight=1)
        main_panel.grid_rowconfigure(0, weight=0)
        main_panel.grid_rowconfigure(1, weight=0)
        main_panel.grid_rowconfigure(2, weight=0)
        main_panel.grid_rowconfigure(3, weight=1)

        settings_center_status_frame = ctk.CTkFrame(main_panel, fg_color="transparent")
        settings_center_status_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        settings_center_status_frame.grid_columnconfigure(0, weight=1)
        settings_center_status_frame.grid_columnconfigure(1, weight=1)
        settings_center_status_frame.grid_columnconfigure(2, weight=1)

        self._create_folder_frame(main_panel)
        self._create_api_frame(main_panel)
        self._create_options_frame(settings_center_status_frame)
        self._create_center_frame(settings_center_status_frame)
        self._create_checkbox_frame(settings_center_status_frame)
        self._create_log_frame(main_panel)
        self._create_watermark(main_panel)

        main_panel.grid_rowconfigure(3, weight=1)

    def _create_folder_frame(self, parent):
        folder_frame = ctk.CTkFrame(parent, corner_radius=8)
        folder_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        folder_frame.grid_columnconfigure(1, weight=1)
        older_header_tooltip = """
Select source (input) and destination (output) folders for images.

• Input Folder: Folder containing\n   images to be processed
• Output Folder: Folder where processed\n   images will be saved

Images from input folder will be processed with API, then copied to output folder with new metadata.
"""
        folder_header = self._create_header_with_help(folder_frame, "Folder Input/Output", older_header_tooltip, font=ctk.CTkFont(size=15, weight="bold"))
        folder_header.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(folder_frame, text="Input Folder:").grid( row=1, column=0, padx=10, pady=5, sticky="w")
        self.input_entry = ctk.CTkEntry(folder_frame, textvariable=self.input_dir)
        self.input_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.input_button = ctk.CTkButton(folder_frame, text="Browse", command=self._select_input_folder, width=70, fg_color="#079183")
        self.input_button.grid(row=1, column=2, padx=5, pady=5)

        ctk.CTkLabel(folder_frame, text="Output Folder:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.output_entry = ctk.CTkEntry(folder_frame, textvariable=self.output_dir)
        self.output_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.output_button = ctk.CTkButton(folder_frame, text="Browse", command=self._select_output_folder, width=70, fg_color="#079183")
        self.output_button.grid(row=2, column=2, padx=5, pady=5)

        folder_tooltip_text = "Input and Output must be different.\nDo not use the same folder for both."
        ToolTip(self.input_entry, folder_tooltip_text)
        ToolTip(self.output_entry, folder_tooltip_text)

    def _create_api_frame(self, parent):
        api_frame = ctk.CTkFrame(parent, corner_radius=8)
        api_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        api_frame.grid_columnconfigure(0, weight=1)
        api_frame.grid_columnconfigure(1, weight=0)
        api_frame.grid_columnconfigure(2, weight=0)

        api_header_tooltip = """
Add one or more Gemini API keys to process images. Each line is one API key.

    • You can get API key\n       from Google AI Studio
    • Processing limit is 60 images\n       per minute per API key
    • Automatic rotation of some API\n       keys occurs during batch processing
    • API key paid? is for API key that\n       has been paid for
    
The more API keys, the faster the batch process.
        """
        api_header_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        api_header_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsw")

        api_header = self._create_header_with_help(api_header_frame, "API Keys", api_header_tooltip, font=ctk.CTkFont(size=15, weight="bold"))
        api_header.pack(side=tk.LEFT, padx=(0, 5))

        self.show_api_keys_switch = ctk.CTkSwitch(api_header_frame,text="Hide/Show", variable=self.show_api_keys_var, command=self._toggle_api_key_visibility)
        self.show_api_keys_switch.pack(side=tk.LEFT, padx=(0, 0))

        self.extra_settings_var = tk.BooleanVar(value=False)
        self.extra_settings_checkbox = ctk.CTkCheckBox(api_header_frame, text="API key paid?", variable=self.extra_settings_var)
        self.extra_settings_checkbox.pack(side=tk.RIGHT, padx=(10, 0))

        self.api_textbox = ctk.CTkTextbox(api_frame, height=105, corner_radius=5, wrap=tk.WORD, font=self.font_normal)
        self.api_textbox.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="nsew")
        self.api_textbox.bind("<KeyRelease>", self._sync_actual_keys_from_textbox)

        api_load_save_buttons = ctk.CTkFrame(api_frame, fg_color="transparent")
        api_load_save_buttons.grid(row=1, column=1, padx=5, pady=(12, 10), sticky="ns")

        self.cek_api_button = ctk.CTkButton(api_load_save_buttons,text="Check API", width=70, command=self._cek_api_keys, fg_color="#079183")
        self.cek_api_button.pack(pady=2, fill=tk.X)

        self.load_api_button = ctk.CTkButton(api_load_save_buttons, text="Load", width=70, command=self._load_api_keys, fg_color="#079183")
        self.load_api_button.pack(pady=2, fill=tk.X)

        self.save_api_button = ctk.CTkButton(api_load_save_buttons, text="Save", width=70, command=self._save_api_keys, fg_color="#079183")
        self.save_api_button.pack(pady=2, fill=tk.X)

        self.delete_api_button = ctk.CTkButton(api_load_save_buttons, text="Delete", width=70, command=self._delete_selected_api_key, fg_color="#079183")
        self.delete_api_button.pack(pady=2, fill=tk.X)

        process_buttons_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        process_buttons_frame.grid(row=1, column=2, padx=(5, 10), pady=(0, 10), sticky="ns")

        self.start_button = ctk.CTkButton(process_buttons_frame, text="Start Processing", command=self._start_processing, font=self.font_medium, height=35, fg_color="#079183")
        self.start_button.pack(pady=7, fill=tk.X)

        self.stop_button = ctk.CTkButton(process_buttons_frame, text="Stop Processing", command=self._stop_processing, font=self.font_medium, height=35, state=tk.DISABLED, fg_color=("#bf3a3a", "#8d1f1f"))
        self.stop_button.pack(pady=7, fill=tk.X)

        self.clear_button = ctk.CTkButton(process_buttons_frame, text="Clear Log", command=self._clear_log, font=self.font_medium, height=35, fg_color="#079183")
        self.clear_button.pack(pady=7, fill=tk.X)

    def _cek_api_keys(self):
        api_keys = self._actual_api_keys
        if not api_keys:
            self._log("No API key to check.", "warning")
            return
        self.cek_api_button.configure(state=tk.DISABLED)
        self._log("Checking status of all API keys...", "info")
        try:
            results = check_api_keys_status(api_keys)
            ok_keys = [k for k, (s, msg) in results.items() if s == 200]
            err_keys = [(k, s, msg) for k, (s, msg) in results.items() if s != 200]
            if len(ok_keys) == len(api_keys):
                self._log(f"All API keys OK ({len(ok_keys)}/{len(api_keys)})", "success")
            else:
                self._log(f"{len(ok_keys)} API keys OK, {len(err_keys)} API key errors:", "warning")
                for k, s, msg in err_keys:
                    self._log(f"  - ...{k[-5:]}: {s} - {msg}", "error")
        except Exception as e:
            self._log(f"Error checking API key: {e}", "error")
        self.cek_api_button.configure(state=tk.NORMAL)

    def _create_options_frame(self, parent):
        options_frame = ctk.CTkFrame(parent, corner_radius=8)
        options_frame.grid(row=0, column=0, padx=(0, 3), pady=0, sticky="nsew")
        options_frame.grid_columnconfigure(1, weight=1)

        settings_header_tooltip = """
Configuration of application behavior:

• Keywords: Number of keywords/tags\n  taken from API results (min 8, max 49)
• Workers: Number of parallel threads\n  for processing files (e.g. 1-10). 
• Delay (s): Time delay (seconds)\n   between API requests. 
• Rename Files: If active, file names\n  will be automatically changed\n  based on the 'title' metadata from API.
• Auto Category: If active, automatically\n  categorize files according to metadata\n  from API. 
• Auto Foldering: If active, files\n  being processed will be automatically\n  placed in folders based on their type\n  

*NB: This setting is automatically saved\n        for the next session.
"""
        settings_header = self._create_header_with_help(options_frame, "Settings", settings_header_tooltip, font=ctk.CTkFont(size=15, weight="bold"))
        settings_header.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="wns")

        ctk.CTkLabel(options_frame, text="Keywords:", font=self.font_normal).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.keyword_entry = ctk.CTkEntry(options_frame, textvariable=self.keyword_count_var, width=100, justify='center', font=self.font_normal)
        self.keyword_entry.grid(row=1, column=1, padx=5, pady=5, sticky="wns")
        
        ctk.CTkLabel(options_frame, text="Workers:", font=self.font_normal).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.workers_entry = ctk.CTkEntry(options_frame, textvariable=self.workers_var, width=100, justify='center', font=self.font_normal)
        self.workers_entry.grid(row=2, column=1, padx=5, pady=5, sticky="wns")

        ctk.CTkLabel(options_frame, text="Delay (s):", font=self.font_normal).grid(row=3, column=0, padx=10, pady=5, sticky="wns")
        self.delay_entry = ctk.CTkEntry(options_frame, textvariable=self.delay_var, width=100, justify='center', font=self.font_normal)
        self.delay_entry.grid(row=3, column=1, padx=5, pady=5, sticky="wns")

    def _create_checkbox_frame(self, parent):
        checkbox_frame = ctk.CTkFrame(parent, corner_radius=8)
        checkbox_frame.grid(row=0, column=2, padx=3, pady=0, sticky="nesw")
        checkbox_frame.grid_columnconfigure(0, weight=1)

        self.rename_switch = ctk.CTkSwitch(checkbox_frame, text="Rename File?", variable=self.rename_files_var, font=self.font_normal)
        self.rename_switch.grid(row=2, column=0, padx=10, pady=8, sticky="w")
        self.auto_kategori_switch = ctk.CTkSwitch(checkbox_frame, text="Auto Category?", variable=self.auto_kategori_var, font=self.font_normal)
        self.auto_kategori_switch.grid(row=3, column=0, padx=10, pady=8, sticky="w")
        self.auto_foldering_switch = ctk.CTkSwitch(checkbox_frame, text="Auto Foldering?", variable=self.auto_foldering_var, font=self.font_normal)
        self.auto_foldering_switch.grid(row=4, column=0, padx=10, pady=8, sticky="w")

        ctk.CTkLabel(checkbox_frame, text="").grid(row=0, column=0, pady=5)

    def _create_log_frame(self, parent):
        log_frame = ctk.CTkFrame(parent, corner_radius=8)
        log_frame.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(log_frame, text="Logs", font=self.font_large).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.log_text = ctk.CTkTextbox(log_frame, wrap=tk.WORD, height=200, font=self.font_normal)
        self.log_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.log_text.configure(state=tk.DISABLED)

        theme_mode = ctk.get_appearance_mode()
        success_color = ("#21a645", "#21a645")
        error_color = ("#ff0000", "#ff0000")
        warning_color = ("#ff9900", "#ff9900")
        info_color = ("#0088ff", "#0088ff")
        cooldown_color = ("#8800ff", "#8800ff")
        bold_font = (self.default_font_family, 11, "bold")

        self.log_text._textbox.tag_configure("success", foreground=success_color[1 if theme_mode == "dark" else 0])
        self.log_text._textbox.tag_configure("error", foreground=error_color[1 if theme_mode == "dark" else 0])
        self.log_text._textbox.tag_configure("warning", foreground=warning_color[1 if theme_mode == "dark" else 0])
        self.log_text._textbox.tag_configure("info", foreground=info_color[1 if theme_mode == "dark" else 0])
        self.log_text._textbox.tag_configure("cooldown", foreground=cooldown_color[1 if theme_mode == "dark" else 0])
        self.log_text._textbox.tag_configure("bold", font=bold_font)

    def _create_watermark(self, parent):
        bottom_frame = ctk.CTkFrame(parent, fg_color="transparent")
        bottom_frame.grid(row=4, column=0, padx=5, pady=(0, 5), sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        if platform.system() == "Windows":
            self.console_toggle_switch = ctk.CTkSwitch(
                bottom_frame,
                text="",
                variable=self.console_visible_var,
                command=self._toggle_console_visibility,
                font=self.font_small
            )
            self.console_toggle_switch.grid(row=0, column=0, sticky="w", padx=(10, 5))
            ToolTip(self.console_toggle_switch, "Show/Hide Console Window")

        watermark_label = ctk.CTkLabel(bottom_frame, text=f"© Riiicil 2025 - Ver {APP_VERSION}", font=ctk.CTkFont(size=10), text_color=("gray50", "gray70"))
        watermark_label.grid(row=0, column=1, sticky="e", padx=(5, 10))

    def _toggle_console_visibility(self):
        if platform.system() == "Windows":
            show = self.console_visible_var.get()
            set_console_visibility(show)
            self._update_console_toggle_text()
            self._save_settings()
        else:
             log_message("Console toggle attempted on non-Windows system.", "warning")

    def _update_console_toggle_text(self):
         if platform.system() == "Windows" and hasattr(self, 'console_toggle_switch'):
             pass

    def _create_header_with_help(self, parent, text, tooltip_text, font=None):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")

        if font:
            header_label = ctk.CTkLabel(header_frame, text=text, font=font)
        else:
            header_label = ctk.CTkLabel(header_frame, text=text, font=("Segoe UI", 12, "bold"))

        header_label.pack(side=tk.LEFT, padx=(0, 5))

        help_icon_size = 16
        help_icon = ctk.CTkLabel(header_frame, text="?", width=help_icon_size, height=help_icon_size, fg_color=("#3a7ebf", "#1f538d"), corner_radius=8, text_color="white", font=("Segoe UI", 10, "bold"))
        help_icon.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(help_icon, tooltip_text)

        return header_frame

    def _create_center_frame(self, parent):
        center_frame = ctk.CTkFrame(parent, corner_radius=8)
        center_frame.grid(row=0, column=1, padx=3, pady=0, sticky="nsew")
        center_frame.grid_columnconfigure(1, weight=1)

        self.theme_var = tk.StringVar(value="dark")
        self.theme_dropdown = ctk.CTkComboBox(center_frame, values=self.available_themes, variable=self.theme_var, command=self._change_theme, width=120, justify='center')
        ctk.CTkLabel(center_frame, text="Theme:", font=self.font_normal).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.theme_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="ns")
        self.model_dropdown = ctk.CTkComboBox(center_frame, values=self.available_models, variable=self.model_var, width=120, justify='center')
        ctk.CTkLabel(center_frame, text="Models:", font=self.font_normal).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.model_dropdown.grid(row=3, column=1, padx=5, pady=5, sticky="ns")
        ctk.CTkLabel(center_frame, text="Quality:", font=self.font_normal).grid(row=4, column=0, padx=10, pady=5, sticky="wns")
        self.priority_dropdown = ctk.CTkComboBox(center_frame, values=self.available_priorities, variable=self.priority_var, width=120, justify='center')
        self.priority_dropdown.grid(row=4, column=1, padx=5, pady=5, sticky="ns")
        ctk.CTkLabel(center_frame, text="").grid(row=0, column=0, pady=5)

    def _init_analytics(self):
        if not self.installation_id.get():
            new_id = str(uuid.uuid4())
            self.installation_id.set(new_id)
            self._log(f"Creating new installation ID: {new_id}", "info")
            self._needs_initial_save = True

        self._send_analytics_event("app_start")

    def _send_analytics_event(self, event_name, params={}):
        if not self.analytics_enabled_var.get():
            return

        if not MEASUREMENT_ID or not API_SECRET:
            self._log("Analytics configuration is incomplete, event not sent.", "warning")
            return

        system_params = {
            "operating_system": platform.system(),
            "os_version": platform.release(),
        }

        full_params = {**system_params, **params}

        send_analytics_event(
            self.installation_id.get(),
            event_name,
            APP_VERSION,
            full_params
        )

    def _select_input_folder(self):
        directory = tk.filedialog.askdirectory(title="Select Input Folder")
        if directory:
            output_dir = self.output_dir.get().strip()
            if output_dir and os.path.normpath(directory) == os.path.normpath(output_dir):
                tk.messagebox.showwarning(
                    "Same Folder",
                    "Input folder cannot be the same as output folder.\nPlease select a different folder."
                )
                return
            self.input_dir.set(directory)

    def _select_output_folder(self):
        directory = tk.filedialog.askdirectory(title="Select Output Folder")
        if directory:
            input_dir = self.input_dir.get().strip()
            if input_dir and os.path.normpath(directory) == os.path.normpath(input_dir):
                tk.messagebox.showwarning(
                    "Same Folder",
                    "Output folder cannot be the same as input folder.\nPlease select a different folder."
                )
                return
            self.output_dir.set(directory)

    def _load_cache(self):
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.processed_cache = json.load(f)
        except Exception as e:
            self._log(f"Error loading cache: {e}", "error")
            self.processed_cache = {}

    def _save_cache(self):
        try:
            if len(self.processed_cache) > 1000:
                cache_items = sorted(self.processed_cache.items(),
                                key=lambda x: x[1].get('timestamp', 0),
                                reverse=True)
                self.processed_cache = dict(cache_items[:1000])

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_cache, f, indent=4)
        except Exception as e:
            self._log(f"Error saving cache: {e}", "error")

    def _load_api_keys(self):
        filepath = tk.filedialog.askopenfilename(
            title="Select API Keys File (.txt)",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")))

        if not filepath:
            return

        try:
            keys = read_api_keys(filepath)
            if keys:
                self._actual_api_keys = keys
                self._update_api_textbox()
                self._log(f"Successfully loaded {len(keys)} API key", "success")
            else:
                tk.messagebox.showwarning("Empty File",
                    f"API keys file is empty or invalid.")
        except Exception as e:
            self._log(f"Error loading API keys: {e}")
            tk.messagebox.showerror("Error", f"Failed to load API keys: {e}")

    def _save_api_keys(self):
        keys_to_save = self._get_keys_from_textbox()
        if not keys_to_save:
            tk.messagebox.showwarning("No APIKey",
                "No API key to save.")
            return

        filepath = tk.filedialog.asksaveasfilename(
            title="Save API Keys",
            defaultextension=".txt",
            initialfile="api_keys.txt",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")))

        if not filepath:
            return

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(keys_to_save))
            self._log(f"API Keys ({len(keys_to_save)}) saved to file", "success")
        except Exception as e:
            self._log(f"Error saving API keys: {e}")
            tk.messagebox.showerror("Error", f"Failed to save API keys: {e}")

    def _delete_selected_api_key(self):
        start_line_idx = -1
        end_line_idx = -1
        num_keys_to_delete = 0
        delete_mode = ""

        try:
            start_index_str = self.api_textbox._textbox.index("sel.first")
            end_index_str = self.api_textbox._textbox.index("sel.last")
            start_line_idx = int(start_index_str.split('.')[0]) - 1
            end_line_idx = int(end_index_str.split('.')[0]) - 1
            delete_mode = "selection"
            num_keys_to_delete = end_line_idx - start_line_idx + 1

        except tk.TclError:
            try:
                cursor_index_str = self.api_textbox.index(tk.INSERT)
                start_line_idx = int(cursor_index_str.split('.')[0]) - 1
                end_line_idx = start_line_idx
                delete_mode = "cursor"
                num_keys_to_delete = 1
            except ValueError:
                self._log("Error mendapatkan posisi kursor.", "error")
                tk.messagebox.showerror("Error", "Cannot determine target line to delete.")
                return
            except Exception as e:
                 self._log(f"Unexpected error when getting cursor position: {e}", "error")
                 tk.messagebox.showerror("Error", f"Unexpected error when checking cursor: {e}")
                 return

        except ValueError:
            self._log("Error converting selection line index when deleting key.", "error")
            tk.messagebox.showerror("Error", "Error converting selection line index when deleting key.")
            return

        if start_line_idx < 0 or start_line_idx >= len(self._actual_api_keys):
            if delete_mode == "cursor" and start_line_idx == len(self._actual_api_keys):
                 tk.messagebox.showinfo("No API Key", "No API key in this line to delete.")
                 return
            self._log(f"Initial line index ({start_line_idx}) is invalid.", "warning")
            tk.messagebox.showwarning("Invalid Index", "Target line is invalid for deletion.")
            return

        if delete_mode == "selection" and (end_line_idx < 0 or end_line_idx >= len(self._actual_api_keys) or start_line_idx > end_line_idx):
            self._log(f"Selection line index ({end_line_idx}) is invalid or inconsistent.", "warning")
            tk.messagebox.showwarning("Invalid Selection", "Selection line is invalid for deletion.")
            return

        confirm_message = f"Are you sure you want to delete {num_keys_to_delete} selected API keys permanently?" \
                          if delete_mode == "selection" else \
                          f"Are you sure you want to delete API key in line {start_line_idx + 1} permanently?"

        confirm_delete = tk.messagebox.askyesno("Confirm Delete", confirm_message)
        if not confirm_delete:
            self._log("API key deletion cancelled by user.", "info")
            return

        try:
            del self._actual_api_keys[start_line_idx : end_line_idx + 1]
            self._log(f"{num_keys_to_delete} API keys deleted from internal list (line {start_line_idx+1} - {end_line_idx+1}).", "info")
            self._update_api_textbox()
        except IndexError:
            self._log("Error: Index out of range when deleting key from internal list.", "error")
            tk.messagebox.showerror("Error", "Error: Index out of range when deleting key from internal list.")
        except Exception as e:
            self._log(f"Error deleting API keys from list: {e}", "error")
            tk.messagebox.showerror("Error", f"Failed to delete API keys from list: {e}")


    def _toggle_api_key_visibility(self):
        self._update_api_textbox()


    def _update_api_textbox(self):
        cursor_pos = self.api_textbox.index(tk.INSERT)
        selection = None
        try:
            selection = self.api_textbox.tag_ranges("sel")
        except tk.TclError:
            pass

        try:
            self.api_textbox.configure(state=tk.NORMAL)
            self.api_textbox.delete("1.0", tk.END)

            if self.show_api_keys_var.get():
                if self._actual_api_keys:
                    self.api_textbox.insert("1.0", "\n".join(self._actual_api_keys))
            else:
                if self._actual_api_keys:
                    placeholders = ["•" * 39] * len(self._actual_api_keys)
                    self.api_textbox.insert("1.0", "\n".join(placeholders))

            self.api_textbox.configure(state=tk.NORMAL)

            self.api_textbox.mark_set(tk.INSERT, cursor_pos)
            if selection:
                 self.api_textbox.tag_add("sel", selection[0], selection[1])
            self.api_textbox.see(tk.INSERT)

        except tk.TclError:
            pass
        except Exception as e:
             self._log(f"Error updating API textbox display: {e}", "error")

    def _get_keys_from_textbox(self):
        self._sync_actual_keys_from_textbox()
        return self._actual_api_keys

    def _sync_actual_keys_from_textbox(self, event=None):
        if self.show_api_keys_var.get():
            try:
                keys_text = self.api_textbox.get("1.0", "end-1c")
                self._actual_api_keys = [line.strip() for line in keys_text.splitlines() if line.strip()]
            except tk.TclError:
                 self._actual_api_keys = []
            except Exception as e:
                 self._log(f"Error syncing keys from textbox: {e}", "error")

    def _get_config_path(self):
        try:
            keys_text = self.api_textbox.get("1.0", "end-1c")
            return [line.strip() for line in keys_text.splitlines() if line.strip()]
        except tk.TclError:
            return []

    def _get_config_path(self):
        if os.name == 'nt':
            documents_path = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents')
            if os.path.exists(documents_path):
                config_dir = os.path.join(documents_path, "RJ Auto Metadata")
                os.makedirs(config_dir, exist_ok=True)
                return os.path.join(config_dir, CONFIG_FILE)

        try:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(base_dir, CONFIG_FILE)
        except Exception as e:
            print(f"Error getting config path: {e}")
            return CONFIG_FILE

    def _load_settings(self):
        try:
            self._log(f"Loading settings...", "info")

            if os.path.exists(self.config_path):
                self.analytics_enabled_var.set(True)
                self.installation_id.set("")

                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        config_content = f.read()
                        settings = json.loads(config_content)

                        self.input_dir.set(settings.get("input_dir", ""))
                        self.output_dir.set(settings.get("output_dir", ""))
                        self.delay_var.set(str(settings.get("delay", "10")))
                        self.workers_var.set(str(settings.get("workers", "3")))
                        self.rename_files_var.set(settings.get("rename", False))
                        self.auto_kategori_var.set(settings.get("auto_kategori", True))
                        self.auto_foldering_var.set(settings.get("auto_foldering", False))
                        self._actual_api_keys = settings.get("api_keys", [])
                        self.show_api_keys_var.set(settings.get("show_api_keys", False))
                        self.console_visible_var.set(settings.get("console_visible", True))
                        self.extra_settings_var.set(settings.get("api_key_paid", False))

                        loaded_theme = settings.get("theme", "dark")
                        self.theme_var.set(loaded_theme)
                        ctk.set_appearance_mode(loaded_theme)

                        loaded_install_id = settings.get("installation_id")
                        if loaded_install_id:
                            self.installation_id.set(loaded_install_id)
                            self._log(f"Installation ID found: {loaded_install_id[:8]}...", "info")
                        else:
                              self._log("Installation ID not found in config.", "info")

                        self._update_api_textbox()
                        self._log("Other settings loaded from configuration", "info")

                        if platform.system() == "Windows":
                             initial_console_state = self.console_visible_var.get()
                             log_message(f"Setting initial console visibility to: {initial_console_state}", "info")
                             set_console_visibility(initial_console_state)
                             self.after(50, self._update_console_toggle_text)

                        self.model_var.set(settings.get("model", "Auto Rotation"))
                        self.keyword_count_var.set(str(settings.get("keyword_count", "49")))
                        self.priority_var.set(settings.get("priority", "Detailed"))
                        self.available_models = [
                            "Auto Rotation",
                            "gemini-1.5-flash",
                            "gemini-1.5-flash-8b"
                            # "gemini-1.5-pro", 
                            "gemini-2.0-flash",
                            "gemini-2.0-flash-lite",
                            "gemini-2.5-flash",
                            "gemini-2.5-flash-lite-preview-06-17",
                            "gemini-2.5-pro"
                        ]
                        self.available_priorities = ["Detailed", "Balanced", "Less"]

                except Exception as inner_e:
                    self._log(f"Error loading configuration file: {inner_e}", "error")
            else:
                self._log(f"Configuration file not found", "warning")
                self.analytics_enabled_var.set(True)
                self.installation_id.set("")
                self._needs_initial_save = True
                self._log("New configuration file will be created after initialization", "info")
        except Exception as e:
            self._log(f"Error loading settings: {e}", "error")
            import traceback
            self._log(traceback.format_exc(), "error")
            self.analytics_enabled_var.set(True)
            self.installation_id.set("")

    def _save_settings(self):
        self._sync_actual_keys_from_textbox()

        settings = {
            "config_version": "1.0",
            "input_dir": self.input_dir.get(),
            "output_dir": self.output_dir.get(),
            "delay": self.delay_var.get(),
            "workers": self.workers_var.get(),
            "rename": self.rename_files_var.get(),
            "auto_kategori": self.auto_kategori_var.get(),
            "auto_foldering": self.auto_foldering_var.get(),
            "api_keys": self._actual_api_keys,
            "show_api_keys": self.show_api_keys_var.get(),
            "console_visible": self.console_visible_var.get(),
            "theme": self.theme_var.get(),
            "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analytics_enabled": self.analytics_enabled_var.get(),
            "installation_id": self.installation_id.get(),
            "model": self.model_var.get(),
            "keyword_count": self.keyword_count_var.get(),
            "priority": self.priority_var.get(),
            "api_key_paid": self.extra_settings_var.get(),
        }

        try:
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                self._log(f"Creating configuration directory: {config_dir}", "info")
                os.makedirs(config_dir, exist_ok=True)

            if not os.access(config_dir, os.W_OK):
                self._log(f"Warning: Configuration directory is not writable: {config_dir}", "warning")
                if os.name == 'nt':
                    self.config_path = os.path.join(os.environ.get('USERPROFILE', ''), "RJ Auto Metadata - config.json")
                    self._log(f"Trying fallback to home directory: {self.config_path}", "info")

            self._log(f"Saving settings...", "info")
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json_data = json.dumps(settings, indent=4)
                f.write(json_data)
                self._log(f"Settings saved successfully ({len(json_data)} bytes)", "info")
        except PermissionError as pe:
            self._log(f"Error permission: {pe}", "error")
            alt_path = os.path.join(os.getcwd(), "rjmetadata_config.json")
            self._log(f"Trying to write to alternative location: {alt_path}", "warning")

            try:
                with open(alt_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4)
                self.config_path = alt_path
                self._log(f"Settings saved to alternative location", "info")
            except Exception as alt_e:
                self._log(f"Failed to write to alternative location: {alt_e}", "error")
        except Exception as e:
            self._log(f"Error saving settings: {e}", "error")
            import traceback
            self._log(traceback.format_exc(), "error")

    def _change_theme(self, selected_theme):
        try:
            if selected_theme in ["dark", "light", "system"]:
                ctk.set_appearance_mode(selected_theme)
            else:
                theme_file = os.path.join(self.theme_folder, f"{selected_theme}.json")
                if os.path.exists(theme_file):
                    ctk.set_default_color_theme(theme_file)
                else:
                    self._log(f"Theme '{selected_theme}' not found.", "error")
                    return

            self._log(f"Theme changed to: {selected_theme}", "info")
            self._update_log_colors()
            self._save_settings()
        except Exception as e:
            self._log(f"Error changing theme: {e}", "error")

    def _update_log_colors(self):
        theme_mode = ctk.get_appearance_mode()
        success_color = ("#21a645")
        error_color = ("#aa0000")
        warning_color = ("#aa5500")
        info_color = ("#000077",)
        cooldown_color = ("#550055")

        self.log_text._textbox.tag_configure("success", foreground=success_color)
        self.log_text._textbox.tag_configure("error", foreground=error_color)
        self.log_text._textbox.tag_configure("warning", foreground=warning_color)
        self.log_text._textbox.tag_configure("info", foreground=info_color[0])
        self.log_text._textbox.tag_configure("cooldown", foreground=cooldown_color)

    def _validate_folders(self):
        input_dir = self.input_dir.get().strip()
        output_dir = self.output_dir.get().strip()

        if input_dir and output_dir and os.path.normpath(input_dir) == os.path.normpath(output_dir):
            self.input_entry.configure(border_color=("red", "#aa0000"))
            self.output_entry.configure(border_color=("red", "#aa0000"))
            self.start_button.configure(state=tk.DISABLED)
            return False
        else:
            self.input_entry.configure(border_color=None)
            self.output_entry.configure(border_color=None)

            if self.start_button['state'] == tk.DISABLED and not self.processing_thread:
                self.start_button.configure(state=tk.NORMAL)

            return True

    def _validate_path_permissions(self, path, check_write=True):
        try:
            if not os.path.exists(path):
                self._log(f"Path not found: {path}", "info")
                return False

            if os.path.isdir(path):
                if check_write:
                    return is_writable_directory(path)
                return True
            elif os.path.isfile(path):
                can_read = os.access(path, os.R_OK)
                can_write = os.access(path, os.W_OK) if check_write else True
                self._log(f"File {path}: can read = {can_read}, can write = {can_write}", "info")
                return can_read and can_write

            return False
        except Exception as e:
            self._log(f"Error validating path: {e}", "error")
            return False

    def _start_processing(self):
        input_dir = self.input_dir.get().strip()
        output_dir = self.output_dir.get().strip()

        self._disable_ui_during_processing()

        if not input_dir or not output_dir:
            self._reset_ui_after_processing()
            tk.messagebox.showwarning("Input Less",
                "Please select input and output folders.")
            return

        if os.path.normpath(input_dir) == os.path.normpath(output_dir):
            self._reset_ui_after_processing()
            tk.messagebox.showwarning("Same Folder",
                "Input and output folders cannot be the same.\nPlease select different folders.")
            return

        if not os.path.isdir(input_dir):
            self._reset_ui_after_processing()
            tk.messagebox.showerror("Error",
                f"Invalid input folder:\n{input_dir}")
            return

        if not os.path.isdir(output_dir):
            if tk.messagebox.askyesno("Create Folder?",
                f"Output folder '{os.path.basename(output_dir)}' not found.\n\nCreate folder?"):
                try:
                    os.makedirs(output_dir)
                except Exception as e:
                    self._reset_ui_after_processing()
                    tk.messagebox.showerror("Error",
                        f"Failed to create output folder:\n{e}")
                    return
            else:
                self._reset_ui_after_processing()
                return

        current_api_keys = self._get_keys_from_textbox()
        if not current_api_keys:
            self._reset_ui_after_processing()
            tk.messagebox.showwarning("Input Less",
                "Please enter at least one API Key.")
            return

        try:
            delay_sec = int(self.delay_var.get().strip() or "0")
            if delay_sec < 0:
                delay_sec = 0
            elif delay_sec > 300:
                delay_sec = 300
            self.delay_var.set(str(delay_sec))
        except ValueError:
            self.delay_var.set("10")
            delay_sec = 10

        if self.extra_settings_var.get():
            try:
                num_workers = int(self.workers_var.get().strip() or "3")
                if num_workers <= 0:
                    num_workers = 1
                elif num_workers > 100:
                    num_workers = 100
                self.workers_var.set(str(num_workers))
            except ValueError:
                self.workers_var.set("3")
                num_workers = 3
        else:
            num_api_keys = len(current_api_keys)
            max_workers = 25
            try:
                num_workers = int(self.workers_var.get().strip() or "3")
                if num_workers <= 0:
                    num_workers = 1
                elif num_workers > num_api_keys:
                    num_workers = num_api_keys
                elif num_workers > max_workers:
                    num_workers = max_workers
                self.workers_var.set(str(num_workers))
            except ValueError:
                self.workers_var.set("3")
                num_workers = 3

        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.stopped_count = 0

        rename_enabled = self.rename_files_var.get()
        auto_kategori_enabled = self.auto_kategori_var.get()
        auto_foldering_enabled = self.auto_foldering_var.get()

        self.stop_event.clear()
        self.start_time = time.monotonic()
        self.start_button.configure(state=tk.DISABLED, text="Processing....")
        self.stop_button.configure(state=tk.NORMAL)

        self._log("Auto compression active for large files", "warning")

        if self.analytics_enabled_var.get():
            self._send_analytics_event("process_started", {
                "input_files_count": -1,
                "workers": num_workers,
                "delay": delay_sec,
                "rename_enabled": rename_enabled,
                "auto_kategori": auto_kategori_enabled,
                "auto_foldering": auto_foldering_enabled
            })

        try:
            keyword_count = int(self.keyword_count_var.get().strip() or "49")
            if keyword_count < 8:
                keyword_count = 8
            elif keyword_count > 49:
                keyword_count = 49
            self.keyword_count_var.set(str(keyword_count))
        except ValueError:
            self.keyword_count_var.set("49")
            keyword_count = 49
        priority = self.priority_var.get() if hasattr(self, 'priority_var') else "Kualitas"
        self.processing_thread = threading.Thread(
            target=self._run_processing,
            args=(input_dir, output_dir, current_api_keys,
                  rename_enabled, delay_sec, num_workers,
                  auto_kategori_enabled, auto_foldering_enabled, self.model_var.get(), str(keyword_count), priority),
            kwargs={
                'bypass_api_key_limit': self.extra_settings_var.get()
            },
            daemon=True
        )
        self.processing_thread.start()

    def _disable_ui_during_processing(self):
        self.start_button.configure(state=tk.DISABLED)
        self.clear_button.configure(state=tk.DISABLED)
        self.rename_switch.configure(state=tk.DISABLED)
        self.auto_kategori_switch.configure(state=tk.DISABLED)
        self.auto_foldering_switch.configure(state=tk.DISABLED)
        self.api_textbox.configure(state=tk.DISABLED)
        self.theme_dropdown.configure(state=tk.DISABLED)
        self.model_dropdown.configure(state=tk.DISABLED)
        self.priority_dropdown.configure(state=tk.DISABLED)
        self.keyword_entry.configure(state=tk.DISABLED)
        self.workers_entry.configure(state=tk.DISABLED)
        self.delay_entry.configure(state=tk.DISABLED)
        self.input_entry.configure(state=tk.DISABLED)
        self.output_entry.configure(state=tk.DISABLED)
        self.cek_api_button.configure(state=tk.DISABLED)
        self.load_api_button.configure(state=tk.DISABLED)
        self.save_api_button.configure(state=tk.DISABLED)
        self.delete_api_button.configure(state=tk.DISABLED)
        self.input_button.configure(state=tk.DISABLED)
        self.output_button.configure(state=tk.DISABLED)
        self.extra_settings_checkbox.configure(state=tk.DISABLED)

    def _run_processing(self, input_dir, output_dir, api_keys, rename_enabled, delay_seconds, num_workers, auto_kategori_enabled, auto_foldering_enabled, selected_model=None, keyword_count="49", priority="Details", bypass_api_key_limit=False):
        from src.utils.system_checks import GHOSTSCRIPT_PATH as gs_path_found

        try:
            result = batch_process_files(
                input_dir=input_dir,
                output_dir=output_dir,
                api_keys=api_keys,
                ghostscript_path=gs_path_found,
                rename_enabled=rename_enabled,
                delay_seconds=delay_seconds,
                num_workers=num_workers,
                auto_kategori_enabled=auto_kategori_enabled,
                auto_foldering_enabled=auto_foldering_enabled,
                selected_model=selected_model,
                keyword_count=keyword_count,
                priority=priority,
                bypass_api_key_limit=bypass_api_key_limit
            )

            self.processed_count = result.get("processed_count", 0)
            self.failed_count = result.get("failed_count", 0)
            self.skipped_count = result.get("skipped_count", 0)
            self.stopped_count = result.get("stopped_count", 0)

            if self.analytics_enabled_var.get():
                total_files = result.get("total_files", 0)
                self._send_analytics_event("process_completed", {
                    "total_files": total_files,
                    "processed_count": self.processed_count,
                    "failed_count": self.failed_count,
                    "skipped_count": self.skipped_count,
                    "stopped_count": self.stopped_count,
                    "success_rate": (self.processed_count / total_files) * 100 if total_files > 0 else 0
                })

            final_message = "Unknown error occurred."

            if result.get("status") == "no_files":
                final_message = "No files found in input folder."
                self.after(100, lambda msg=final_message: tk.messagebox.showinfo("Info Proses", msg))
                self.after(200, self._reset_ui_after_processing)
            elif self.stop_event.is_set():
                final_message = "Processing stopped by user."
                self.after(100, lambda: self.completion_manager.show_completion_message())
                self.after(200, self._reset_ui_after_processing)
            else:
                final_message = "Processing completed!"
                final_completed = self.processed_count + self.failed_count + self.skipped_count + self.stopped_count
                total_files = result.get("total_files", final_completed)
                self.after(100, lambda: self.completion_manager.show_completion_message())
                self.after(200, self._reset_ui_after_processing)

        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            self._log(f"Fatal error in processing thread: {e}\nTraceback:\n{tb_str}", "error")
            self.after(0, self._reset_ui_after_processing)

    def _update_progress(self, current, total):
        self.update_idletasks()

    def _format_time(self, seconds):
        if seconds is None or not isinstance(seconds, (int, float)) or seconds < 0:
            return "00:00:00"

        hours = int(seconds) // 3600
        minutes = (int(seconds) % 3600) // 60
        secs = int(seconds) % 60

        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _stop_processing(self):
        if self.processing_thread and self.processing_thread.is_alive():
            if tk.messagebox.askyesno("Stop Processing", "Stop processing? Active tasks will be signaled to stop."):
                self._log("Received stop request...", "warning")
                self.stop_event.set()

                from src.api.gemini_api import set_force_stop
                set_force_stop()

                self.stop_button.configure(state=tk.DISABLED, text="Stopping...")
                self._stop_request_time = time.monotonic()
                self.update_idletasks()
                self.update()

                try:
                    if self.is_executable:
                        self._log("Executable mode detected, using interrupt force...", "warning")
                    else:
                        self._log("Stopping all active processes...", "warning")
                except Exception as e:
                    self._log(f"Error when trying to force interrupt: {e}", "error")

                self._check_thread_ended()
        else:
            self.stop_button.configure(state=tk.DISABLED)
            self._reset_ui_after_processing()

    def _check_thread_ended(self):
        self.update_idletasks()
        thread_ended = not self.processing_thread or not self.processing_thread.is_alive()
        force_reset = False

        if hasattr(self, '_stop_request_time') and self._stop_request_time is not None:
            elapsed_since_stop = time.monotonic() - self._stop_request_time
            timeout_threshold = 1.5 if self.is_executable else 2.5

            if elapsed_since_stop > timeout_threshold:
                self._log(f"Thread did not respond after {elapsed_since_stop:.1f} seconds, performing force reset UI...", "warning")
                force_reset = True

                if self.is_executable and self.processing_thread and self.processing_thread.is_alive():
                    self._log("Performing hard reset on thread worker...", "warning")
                    from src.api.gemini_api import set_force_stop
                    set_force_stop()

        if thread_ended or force_reset:
            self.after(10, self._reset_ui_after_processing)
        else:
            self.after(50, self._check_thread_ended)

    def _reset_ui_after_processing(self):
        try:
            self._stop_request_time = None
            from src.api.gemini_api import reset_force_stop
            reset_force_stop()
            self.start_button.configure(state=tk.NORMAL, text="Start Processing")
            self.stop_button.configure(state=tk.DISABLED, text="Stop")
            self.processing_thread = None
            self.start_time = None
            self.stop_event.clear()
            self.update_idletasks()
            self._save_cache()
            self._save_settings()
            self.start_button.configure(state=tk.NORMAL)
            self.clear_button.configure(state=tk.NORMAL)
            self.rename_switch.configure(state=tk.NORMAL)
            self.auto_kategori_switch.configure(state=tk.NORMAL)
            self.auto_foldering_switch.configure(state=tk.NORMAL)
            self.workers_entry.configure(state=tk.NORMAL)
            self.theme_dropdown.configure(state=tk.NORMAL)
            self.model_dropdown.configure(state=tk.NORMAL)
            self.priority_dropdown.configure(state=tk.NORMAL)
            self.keyword_entry.configure(state=tk.NORMAL)
            self.delay_entry.configure(state=tk.NORMAL)
            self.input_entry.configure(state=tk.NORMAL)
            self.output_entry.configure(state=tk.NORMAL)
            self.cek_api_button.configure(state=tk.NORMAL)
            self.load_api_button.configure(state=tk.NORMAL)
            self.save_api_button.configure(state=tk.NORMAL)
            self.delete_api_button.configure(state=tk.NORMAL)
            self.input_button.configure(state=tk.NORMAL)
            self.output_button.configure(state=tk.NORMAL)
            self.extra_settings_checkbox.configure(state=tk.NORMAL)
        except Exception as e:
            print(f"Error when resetting UI: {e}")
            import traceback
            traceback.print_exc()

            try:
                self.start_button.configure(state=tk.NORMAL, text="Start Processing")
                self.stop_button.configure(state=tk.DISABLED, text="Stop")
                self.update_idletasks()
            except:
                pass

    def _log(self, message, tag=None):
        self.log_queue.put((message, tag))

    def _process_log_queue(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if isinstance(item, tuple) and len(item) == 2:
                    message, tag = item
                    self._write_to_log(message, tag)
                else:
                    self._write_to_log(item)
        except queue.Empty:
            pass
        finally:
            if self.winfo_exists():
                self._log_queue_after_id = self.after(100, self._process_log_queue)

    def _should_display_in_gui(self, message):
        allowed_patterns = [
            r"^Auto compression active for large files$",
            r"^Starting process \(\d+ worker, delay \d+s\)$",
            r"^Found \d+ files to process$",
            r"^Output CSV will be saved in subfolder: metadata_csv$",
            r"^ → Processing .+\.\w+\.\.\.$",
            r"^Batch \d+: Waiting for \d+ file\.\.\.$",
            r"^Batch \d+ \(\d+/\d+\): Waiting for \d+ file\.\.\.$",
            r"^✓ .+\.\w+ → .+\.\w+$",
            r"^✓ .+\.\w+$",
            r"^✗ .+\.\w+ \(.*\)$",
            r"^✗ .+\.\w+$",
            r"^⚠  .+\.\w+$",
            r"^⚠ .+\.\w+ \(.*\)$",
            r"^Cool-down \d+ seconds before processing\.\.\.$",
            r"^Successfully loaded \d+ API key$",
            r"^API Keys \(\d+\) saved to file$",
            r"^Adjusting worker count to \d+ to match available API keys\.$",
            r"^Received stop request\.\.\.$",
            r"^Executable mode detected, using interrupt force\.\.\.$",
            r"^Stopping all active processes\.\.\.$",
            r"^Thread did not respond after \d+\.\d+ seconds, performing force reset UI\.\.\.$",
            r"^Processing stopped before starting \(initial detection\)$",
            r"^Stop detected after processing batch results\.$",
            r"^Processing stopped by user \(cooldown detection\)$",
            r"^Cancelling remaining tasks\.\.\.$",
            r"^Creating new installation ID: .+$",
            r"^Installation ID found: .+\.\.\.$",
            r"^Installation ID not found in config\.$",
            r"^Loading other settings\.\.\.$",
            r"^Other settings loaded from configuration$",
            r"^Config file not found$",
            r"^New config file created$",
            r"^============= Summary Process =============",
            r"^Total file: \d+$",
            r"^Successfully processed: \d+$",
            r"^Failed: \d+$",
            r"^Skipped: \d+$",
            r"^Stopped: \d+$",
            r"^=========================================$",
            r"^All API keys OK \(\d+/\d+\)$",
            r"^\d+ API keys OK, \d+ API keys error:$",
            r"^No API keys to check\.$",
            r"^Error when checking API keys:.*$",
            r"^    - \.\.\.[A-Za-z0-9]{5}: \d+ - .+$",
        ]

        for pattern in allowed_patterns:
            if re.match(pattern, message):
                if message == "\n============= Summary Process =============":
                    self._in_summary_block = True
                elif message == "=========================================\n":
                    self._in_summary_block = False
                return True

        if self._in_summary_block:
            if re.match(r"^=========================================$", message):
                self._in_summary_block = False
            return True

        return False

    def _write_to_log(self, message, tag=None):
        if not self._should_display_in_gui(message):
            if self._in_summary_block and not message.startswith("="):
                 self._in_summary_block = False
            return

        try:
            self.log_text.configure(state=tk.NORMAL)

            if tag is None:
                if message.startswith("✓"):
                    tag = "success"
                elif message.startswith("✗"):
                    tag = "error"
                elif message.startswith("⚠"):
                    tag = "warning"
                elif message.startswith("⋯"):
                    tag = "info"
                elif "Error" in message or "Gagal" in message:
                    tag = "error"
                elif "Warning" in message:
                    tag = "warning"
                elif "Cool-down" in message:
                    tag = "cooldown"
                elif "===" in message:
                    tag = "bold"

            if not message.startswith((" ✓", " ⋯", " ✗", " ⊘", " ⚠")) or message.startswith("==="):
                timestamp = time.strftime("%H:%M:%S")
                self.log_text._textbox.insert(tk.END, f"[{timestamp}] ", "")
                self.log_text._textbox.insert(tk.END, f"{message}\n", tag if tag else "")
            else:
                self.log_text._textbox.insert(tk.END, f"{message}\n", tag if tag else "")

            self.log_text._textbox.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        except tk.TclError:
            pass

    def _clear_log(self):
        try:
            self.log_text.configure(state=tk.NORMAL)
            self.log_text._textbox.delete("1.0", tk.END)
            self.log_text.configure(state=tk.DISABLED)
        except tk.TclError:
            pass

    def on_closing(self):
        try:
            self._save_settings()
            self._save_cache()

            if self.processing_thread and self.processing_thread.is_alive():
                if tk.messagebox.askyesno("Exit",
                        "Processing is running. Are you sure you want to exit?\nProcessing will be stopped."):
                    self.stop_event.set()

                    from src.api.gemini_api import set_force_stop
                    set_force_stop()

                    self.after(300, self._force_close)
                return

            self._force_close()
        except Exception as e:
            print(f"Error when closing application: {e}")
            self.destroy()

    def _force_close(self):
        if hasattr(self, '_log_queue_after_id') and self._log_queue_after_id:
            try:
                self.after_cancel(self._log_queue_after_id)
            except tk.TclError:
                pass
        self.destroy()
