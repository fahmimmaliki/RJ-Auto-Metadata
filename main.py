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

# main.py
import os
import sys
import tkinter as tk
import traceback

def main():
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from src.utils.file_utils import IS_NUITKA_EXECUTABLE 
        if getattr(sys, 'frozen', False):
            print("Detected running as executable.")
            IS_NUITKA_EXECUTABLE = True
        from src.ui.app import MetadataApp
        app = MetadataApp()
        app.mainloop()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        traceback.print_exc()
        try:
            tk.messagebox.showerror("Fatal Error", 
                f"Fatal error occurred:\n{e}\nApplication will close.")
        except:
            pass
        sys.exit(1)
if __name__ == "__main__":
    main()
