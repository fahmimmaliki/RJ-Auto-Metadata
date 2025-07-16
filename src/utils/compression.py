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

# src/utils/compression.py
import os
import time
import random
from PIL import Image
from src.utils.logging import log_message
from src.api.gemini_api import check_stop_event, is_stop_requested

TEMP_COMPRESSION_FOLDER_NAME = "temp_compressed"
MAX_IMAGE_SIZE_MB = 2
COMPRESSION_QUALITY = 20 
MAX_IMAGE_DIMENSION = 3000 

def get_temp_compression_folder(base_dir=None, output_dir=None):
    if output_dir and os.path.exists(output_dir) and os.path.isdir(output_dir):
        temp_folder = os.path.join(output_dir, TEMP_COMPRESSION_FOLDER_NAME)
        try:
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder, exist_ok=True)
                log_message(f"Folder compression temp created in output: {temp_folder}")
            return temp_folder
        except Exception as e:
            log_message(f"Error creating compression temp folder in output: {e}")
    
    if base_dir and os.path.exists(base_dir) and os.path.isdir(base_dir):
        temp_folder = os.path.join(base_dir, TEMP_COMPRESSION_FOLDER_NAME)
        try:
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder, exist_ok=True)
                log_message(f"Folder compression temp created in input: {temp_folder}")
            return temp_folder
        except Exception as e:
            log_message(f"Error creating compression temp folder in input: {e}")
    
    try:
        import tempfile
        system_temp = os.path.join(tempfile.gettempdir(), TEMP_COMPRESSION_FOLDER_NAME)
        os.makedirs(system_temp, exist_ok=True)
        log_message(f"Using system temp folder: {system_temp}")
        return system_temp
    except Exception as e:
        log_message(f"Error creating compression temp folder in system: {e}")
        return None

def compress_image(input_path, temp_folder=None, max_size_mb=MAX_IMAGE_SIZE_MB, quality=COMPRESSION_QUALITY, max_dimension=MAX_IMAGE_DIMENSION, stop_event=None):
    try:
        if stop_event and stop_event.is_set() or is_stop_requested():
            log_message("Compression cancelled due to stop request.")
            return input_path, False
        
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        filename = os.path.basename(input_path)
        
        if file_size_mb <= max_size_mb:
            log_message(f"File size {file_size_mb:.2f}MB does not need compression: {filename}")
            return input_path, False
        
        if temp_folder is None:
            parent_dir = os.path.dirname(input_path)
            temp_folder = os.path.join(parent_dir, TEMP_COMPRESSION_FOLDER_NAME)
        
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder, exist_ok=True)
            log_message(f"Compression folder created: {temp_folder}")
        
        if stop_event and stop_event.is_set() or is_stop_requested():
            log_message("Compression cancelled due to stop request.")
            return input_path, False
        
        base, ext = os.path.splitext(filename)
        ext_lower = ext.lower()
        
        try:
            with Image.open(input_path) as img:
                original_width, original_height = img.size
                original_mode = img.mode
                has_transparency = original_mode == 'RGBA' or original_mode == 'LA' or 'transparency' in img.info
                
                if stop_event and stop_event.is_set() or is_stop_requested():
                    log_message("Compression cancelled due to stop request (after load image).")
                    return input_path, False
                
                scale_factor = 1.0
                if original_width > max_dimension or original_height > max_dimension:
                    scale_factor = min(max_dimension / original_width, max_dimension / original_height)
                    new_width = int(original_width * scale_factor)
                    new_height = int(original_height * scale_factor)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    log_message(f"Resize {filename}: {original_width}x{original_height} → {new_width}x{new_height}")
                
                if stop_event and stop_event.is_set() or is_stop_requested():
                    log_message("Compression cancelled due to stop request (after resize).")
                    return input_path, False
                
                adaptive_quality = max(10, quality - int(min(file_size_mb, 50) / 10))
                
                if ext_lower == '.png':
                    jpg_path = os.path.join(temp_folder, f"{base}_compressed.jpg")
                    png_path = os.path.join(temp_folder, f"{base}_compressed.png")
                    
                    if stop_event and stop_event.is_set() or is_stop_requested():
                        log_message("Compression cancelled due to stop request (before conversion to JPG).")
                        return input_path, False
                    
                    log_message(f"File PNG needs compression. Trying conversion to JPG.")
                    try:
                        if original_mode in ['RGBA', 'LA']:
                            log_message(f"Conversion PNG (originally transparent) to JPG with white background")
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            alpha_channel = img.split()[-1]
                            background.paste(img, mask=alpha_channel)
                            
                            if stop_event and stop_event.is_set() or is_stop_requested():
                                log_message("Compression cancelled due to stop request (after prepare background).")
                                return input_path, False
                            
                            background.save(jpg_path, 'JPEG', quality=adaptive_quality, optimize=True)
                        else:
                            if stop_event and stop_event.is_set() or is_stop_requested():
                                log_message("Compression cancelled due to stop request (before direct conversion to JPG).")
                                return input_path, False
                            
                            img.convert('RGB').save(jpg_path, 'JPEG', quality=adaptive_quality, optimize=True)
                        
                        if os.path.exists(jpg_path):
                            if stop_event and stop_event.is_set() or is_stop_requested():
                                try:
                                    if os.path.exists(jpg_path):
                                        os.remove(jpg_path)
                                except Exception:
                                    pass
                                log_message("Compression cancelled due to stop request (after conversion to JPG).")
                                return input_path, False
                            
                            jpg_size_mb = os.path.getsize(jpg_path) / (1024 * 1024)
                            compression_ratio = (1 - (jpg_size_mb / file_size_mb)) * 100
                            
                            if jpg_size_mb > max_size_mb and adaptive_quality > 15:
                                if stop_event and stop_event.is_set() or is_stop_requested():
                                    try:
                                        if os.path.exists(jpg_path):
                                            os.remove(jpg_path)
                                    except Exception:
                                        pass
                                    log_message("Compression cancelled due to stop request (before aggressive compression).")
                                    return input_path, False
                                
                                log_message(f"JPG size still too large, compress more aggressively")
                                try:
                                    if original_mode in ['RGBA', 'LA']:
                                         background.save(jpg_path, 'JPEG', quality=max(10, adaptive_quality - 10), optimize=True)
                                    else:
                                         img.convert('RGB').save(jpg_path, 'JPEG', quality=max(10, adaptive_quality - 10), optimize=True)
                                    jpg_size_mb = os.path.getsize(jpg_path) / (1024 * 1024)
                                    compression_ratio = (1 - (jpg_size_mb / file_size_mb)) * 100
                                except Exception as e:
                                    log_message(f"Error aggressive JPG compression: {e}")
                            
                            log_message(f"Conversion PNG→JPG: {file_size_mb:.2f}MB → {jpg_size_mb:.2f}MB ({compression_ratio:.1f}% reduction)")
                            return jpg_path, True
                        else:
                            log_message(f"Error: File JPG conversion result not found.")
                            return input_path, False
                    except Exception as e:
                        log_message(f"Error when trying to convert PNG to JPG: {e}")
                        return input_path, False
                
                elif ext_lower in ['.jpg', '.jpeg']:
                    compressed_path = os.path.join(temp_folder, f"{base}_compressed{ext}")
                    
                    if stop_event and stop_event.is_set() or is_stop_requested():
                        log_message("Compression cancelled due to stop request (before JPG compression).")
                        return input_path, False
                    
                    try:
                        img.save(compressed_path, 'JPEG', quality=adaptive_quality, optimize=True)
                        
                        if stop_event and stop_event.is_set() or is_stop_requested():
                            try:
                                if os.path.exists(compressed_path):
                                    os.remove(compressed_path)
                            except Exception:
                                pass
                            log_message("Compression cancelled due to stop request (after JPG compression).")
                            return input_path, False
                        
                        if os.path.exists(compressed_path):
                            compressed_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
                            compression_ratio = (1 - (compressed_size_mb / file_size_mb)) * 100
                            
                            if compressed_size_mb > max_size_mb and adaptive_quality > 15:
                                if stop_event and stop_event.is_set() or is_stop_requested():
                                    try:
                                        if os.path.exists(compressed_path):
                                            os.remove(compressed_path)
                                    except Exception:
                                        pass
                                    log_message("Compression cancelled due to stop request (before aggressive JPG compression).")
                                    return input_path, False
                                
                                log_message(f"JPG size still too large, compress more aggressively")
                                try:
                                    img.save(compressed_path, 'JPEG', quality=max(10, adaptive_quality - 10), optimize=True)
                                    
                                    if stop_event and stop_event.is_set() or is_stop_requested():
                                        try:
                                            if os.path.exists(compressed_path):
                                                os.remove(compressed_path)
                                        except Exception:
                                            pass
                                        log_message("Compression cancelled due to stop request (after aggressive JPG compression).")
                                        return input_path, False
                                    
                                    compressed_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
                                    compression_ratio = (1 - (compressed_size_mb / file_size_mb)) * 100
                                except Exception as e:
                                    log_message(f"Error aggressive JPG compression: {e}")
                            
                            log_message(f"JPG compression: {file_size_mb:.2f}MB → {compressed_size_mb:.2f}MB ({compression_ratio:.1f}% reduction)")
                            return compressed_path, True
                    except Exception as e:
                        log_message(f"Error JPG compression: {e}")
                        return input_path, False
                
                else:
                    jpg_path = os.path.join(temp_folder, f"{base}_compressed.jpg")
                    try:
                        if has_transparency:
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if original_mode == 'RGBA':
                                background.paste(img, mask=img.split()[3])
                            else:
                                background.paste(img, mask=img.split()[1])
                            background.save(jpg_path, 'JPEG', quality=adaptive_quality, optimize=True)
                        else:
                            img.convert('RGB').save(jpg_path, 'JPEG', quality=adaptive_quality, optimize=True)
                        
                        if os.path.exists(jpg_path):
                            jpg_size_mb = os.path.getsize(jpg_path) / (1024 * 1024)
                            compression_ratio = (1 - (jpg_size_mb / file_size_mb)) * 100
                            log_message(f"Conversion {ext_lower}→JPG: {file_size_mb:.2f}MB → {jpg_size_mb:.2f}MB ({compression_ratio:.1f}% reduction)")
                            return jpg_path, True
                    except Exception as e:
                        log_message(f"Error converting other formats to JPG: {e}")
                        return input_path, False
        
        except (IOError, OSError) as e:
            log_message(f"Error I/O during compression {filename}: {e}")
            return input_path, False
        except Exception as e:
            log_message(f"Error compression {filename}: {e}")
            return input_path, False
        
        return input_path, False
    except Exception as e:
        log_message(f"Error compression {os.path.basename(input_path)}: {e}")
        import traceback
        log_message(f"Detail error: {traceback.format_exc()}")
        return input_path, False

def cleanup_temp_files(temp_folder, older_than_hours=1):
    if not temp_folder or not os.path.exists(temp_folder):
        return 0
    
    try:
        count = 0
        now = time.time()
        older_than_seconds = older_than_hours * 3600
        
        for filename in os.listdir(temp_folder):
            if "_compressed" in filename:
                file_path = os.path.join(temp_folder, filename)
                if os.path.isfile(file_path):
                    file_age = now - os.path.getmtime(file_path)
                    if file_age > older_than_seconds:
                        try:
                            os.remove(file_path)
                            count += 1
                        except Exception as e:
                            log_message(f"Error removing temp file {filename}: {e}")
        
        if count > 0:
            log_message(f"Cleaned up {count} temp files from {temp_folder}")
        
        return count
    except Exception as e:
        log_message(f"Error cleaning up temp folder: {e}")
        return 0

def cleanup_temp_compression_folder(folder_path):
    if not folder_path or not os.path.exists(folder_path):
        return
    
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        os.rmdir(folder_path)
        log_message(f"Cleaned up temp compression folder")
    except Exception as e:
        log_message(f"Error cleaning up temp compression folder: {e}")

def manage_temp_folders(input_dir, output_dir):
    temp_folders = {}
    
    try:
        output_temp = os.path.join(output_dir, TEMP_COMPRESSION_FOLDER_NAME)
        os.makedirs(output_temp, exist_ok=True)
        temp_folders['output'] = output_temp
    except Exception as e:
        log_message(f"Error setting up output temp folder: {e}")
    
    if not temp_folders:
        import tempfile
        system_temp = os.path.join(tempfile.gettempdir(), TEMP_COMPRESSION_FOLDER_NAME)
        os.makedirs(system_temp, exist_ok=True)
        temp_folders['system'] = system_temp
        log_message(f"Using system temp folder: {system_temp}")
    
    return temp_folders