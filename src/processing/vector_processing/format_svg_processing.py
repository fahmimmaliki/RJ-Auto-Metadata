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

# src/processing/vector_processing/format_svg_processing.py
import os
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from src.utils.logging import log_message
from src.api.gemini_api import check_stop_event

def convert_svg_to_jpg(svg_path, output_jpg_path, stop_event=None):
    filename = os.path.basename(svg_path)
    log_message(f"Trying to convert SVG to JPG: {filename}")
    
    if check_stop_event(stop_event, f"Conversion of SVG cancelled: {filename}"):
        return False, f"Conversion cancelled: {filename}"

    try:
        drawing = svg2rlg(svg_path)
        if drawing is None:
             return False, f"Failed to read or parse SVG: {filename}"
        
        if check_stop_event(stop_event, f"Conversion cancelled after parse: {filename}"):
            return False, f"Conversion cancelled after parse: {filename}"
        
        renderPM.drawToFile(drawing, output_jpg_path, fmt="JPEG", bg=0xFFFFFF)
        
        if os.path.exists(output_jpg_path) and os.path.getsize(output_jpg_path) > 0:
            log_message(f"Conversion of SVG to JPG successful: {os.path.basename(output_jpg_path)}")
            return True, None
        else:
            return False, f"Failed to render SVG to JPG or output file is empty: {filename}"
    except FileNotFoundError:
        return False, f"File SVG not found: {svg_path}"
    except Exception as e:
        error_type = type(e).__name__
        return False, f"Error when converting SVG ({error_type}): {e}"