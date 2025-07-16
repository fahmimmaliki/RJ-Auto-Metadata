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

# src/ui/dialogs.py
import os
import random
import webbrowser
import customtkinter as ctk
import tkinter as tk
from src.utils.logging import log_message

class DonationDialog:
    def __init__(self, parent, message_data, font_normal, font_medium, font_large, iconbitmap_path=None):
        self.parent = parent
        self.message_data = message_data
        self.font_normal = font_normal
        self.font_medium = font_medium 
        self.font_large = font_large
        self.iconbitmap_path = iconbitmap_path
        
        self.dialog = None
        
    def show(self):
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.transient(self.parent)
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.title("INFO!!!")

        def _set_icon():
            try:
                if self.iconbitmap_path and os.path.exists(self.iconbitmap_path):
                    self.dialog.iconbitmap(self.iconbitmap_path)
                    log_message(f"Deferred set icon for DonationDialog using iconbitmap: {self.iconbitmap_path}", "info")
                else:
                    log_message(f"Deferred icon path not valid for DonationDialog: {self.iconbitmap_path}", "warning")
            except Exception as e:
                log_message(f"Error setting deferred icon for DonationDialog: {e}", "error")

        self.dialog.after_idle(_set_icon)
        self.dialog.grab_set()
        self.parent.update_idletasks()
        
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 250) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        title_label = ctk.CTkLabel(main_frame, text=self.message_data["title"], font=self.font_large)
        title_label.pack(pady=(0, 10))
        
        message_label = ctk.CTkLabel(main_frame, text=self.message_data["message"], 
                                     wraplength=350, justify="center", font=self.font_normal)
        message_label.pack(pady=(0, 15))
        
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(10, 0))
        
        donate_button = ctk.CTkButton(
            button_frame,
            text=self.message_data["button"],
            command=lambda: [self._open_donation_link(), self.dialog.destroy()],
            font=self.font_medium,
            fg_color=("#3a7ebf", "#1f538d"),
            height=40
        )
        donate_button.pack(side="left", padx=10)
        
        close_button = ctk.CTkButton(
            button_frame,
            text="Tutup", 
            command=self.dialog.destroy,
            font=self.font_medium,
            fg_color=("gray50", "gray30"),
            height=40
        )
        close_button.pack(side="left", padx=10)
        self.dialog.after(100, self.dialog.lift)
            
    def _open_donation_link(self):
        donation_url = "https://saweria.co/riiicil"
        try:
            webbrowser.open(donation_url)
            log_message(f"Opening donation link: {donation_url}", "info")
        except Exception as e:
            log_message(f"Error opening donation link: {e}", "error")
            tk.messagebox.showerror("Error", f"Failed to open link:\n{donation_url}")

class CompletionMessageManager:
    def __init__(self, parent, config_path, font_normal, font_medium, font_large, iconbitmap_path=None):
        self.parent = parent
        self.config_path = config_path
        self.font_normal = font_normal
        self.font_medium = font_medium
        self.font_large = font_large
        self.iconbitmap_path = iconbitmap_path
        self._completion_counter = 0
        self._load_counter()
        
        self.donation_messages = [
            {
                "title": "Processing Done!",
                "message": "Hopefully RJ Auto Metadata helps you speed up your work.\n\nIf you think this app is useful, you can support the developer by buying him a virtual coffee to keep him motivated!",
                "button": "Send Virtual Coffee ☕"
            },
            {
                "title": "Processing Success!",
                "message": "Good job! All files have been processed.\nThis app is developed with the hope that it can be useful.\n\nIf you want to support the development of new features & improvements, consider giving a small appreciation.",
                "button": "Support Development 🚀"
            },
            {
                "title": "Done!",
                "message": "Great job! All files have been processed.\nThank you for using RJ Auto Metadata!\n\nIf you find it useful, you can support the developer by buying him a virtual coffee to keep him motivated!",
                "button": "Send Virtual Coffee ☕"
            },
            {
                "title": "Done!",
                "message": "All files have been processed!\nTime to rest... or coffee?\n\nIf this app makes your work easier, and you want to keep the developer motivated, you can support the project by buying him a virtual coffee.",
                "button": "Send Virtual Coffee ☕"
            }
        ]
        
    def _load_counter(self):
        try:
            import json
            if os.path.exists(self.config_path):
                 with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self._completion_counter = config.get("completion_counter", 0)
        except Exception as e:
            log_message(f"Warning: Failed to load completion counter: {e}", "warning")
            
    def _save_counter(self):
        try:
            import json
            config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config["completion_counter"] = self._completion_counter
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            log_message(f"Warning: Failed to save completion counter: {e}", "warning")
            
    def show_completion_message(self):
        self._completion_counter += 1
        show_donation_popup = (self._completion_counter % 2 == 0)
        
        self._save_counter()
        
        if show_donation_popup:
            selected_message_data = random.choice(self.donation_messages)
            dialog = DonationDialog(
                self.parent,
                selected_message_data,
                self.font_normal,
                self.font_medium,
                self.font_large,
                self.iconbitmap_path
            )
            dialog.show()
        else:
            tk.messagebox.showinfo("Done", "Processing done!")
