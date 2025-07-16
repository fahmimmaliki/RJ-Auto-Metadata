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

# src/metadata/exif_writer.py
import os
import time
import sys
import subprocess
from src.utils.logging import log_message
from src.api.gemini_api import check_stop_event, is_stop_requested

def check_exiftool_exists():
    try:
        result = subprocess.run(["exiftool", "-ver"], check=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        log_message(f"Exiftool found (version: {result.stdout.strip()}).")
        global EXIFTOOL_PATH
        EXIFTOOL_PATH = "exiftool"
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            if getattr(sys, 'frozen', False):
                if hasattr(sys, '_MEIPASS'):
                    base_dir = sys._MEIPASS
                elif hasattr(sys, '_MEIPASS2'):
                     base_dir = sys._MEIPASS2
                else:
                    base_dir = os.path.dirname(sys.executable)
                log_message(f"Using base_dir for Nuitka/PyInstaller: {base_dir}")
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                base_dir = os.path.dirname(os.path.dirname(base_dir))

            potential_paths = [
                os.path.join(base_dir, "tools", "exiftool", "exiftool.exe"),
                os.path.join(os.path.dirname(sys.executable), "tools", "exiftool", "exiftool.exe"),
                os.path.join(os.environ.get('TEMP', ''), "_MEI", "tools", "exiftool", "exiftool.exe"),
                os.path.abspath("tools/exiftool/exiftool.exe")
            ]

            for path in potential_paths:
                normalized_path = os.path.normpath(path)
                log_message(f"Checking exiftool at: {normalized_path}")
                if os.path.exists(normalized_path):
                    try:
                         test_result = subprocess.run([normalized_path, "-ver"], check=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                         log_message(f"Exiftool found and valid at: {normalized_path} (version: {test_result.stdout.strip()})")
                         EXIFTOOL_PATH = normalized_path
                         return True
                    except Exception as e_test:
                         log_message(f"Found but failed execution: {normalized_path} - Error: {e_test}")
                         continue

            log_message("Error: 'exiftool' not found in expected location.", "error")
            return False
        except Exception as e:
            log_message(f"Unexpected error checking exiftool: {e}", "error")
            return False

# Menyimpan path exiftool saat ditemukan
EXIFTOOL_PATH = None

def write_exif_with_exiftool(image_path, output_path, metadata, stop_event):
    """
    Write EXIF metadata to image file using exiftool.

    Args:
        image_path: Source file path
        output_path: Output file path
        metadata: Dictionary containing metadata (title, description, tags)
        stop_event: Event threading to stop the process

    Returns:
        Tuple(bool, str): (True/False indicating if processing should continue, status string)
                           Possible status strings: "exif_ok", "exif_failed", "no_metadata",
                           "stopped", "copy_failed", "exiftool_not_found", "unknown_error"
    """
    title = metadata.get('title', '')
    description = metadata.get('description', '')
    tags = metadata.get('tags', [])
    keyword_count = metadata.get('keyword_count', 49)
    try:
        max_kw = int(keyword_count)
        if max_kw < 1: max_kw = 49
    except Exception:
        max_kw = 49
    cleaned_tags = [tag.strip() for tag in tags if tag.strip()]
    cleaned_tags = list(dict.fromkeys(cleaned_tags))
    cleaned_tags = cleaned_tags[:max_kw]

    if stop_event.is_set() or is_stop_requested():
        log_message("Process stopped before writing EXIF.")
        return False, "stopped"

    if not os.path.exists(output_path):
        try:
            import shutil
            shutil.copy2(image_path, output_path)
        except Exception as e:
            log_message(f"Failed to copy file '{os.path.basename(image_path)}' to output: {e}")
            return False, "copy_failed"

    if stop_event.is_set() or is_stop_requested():
        log_message("Process stopped after copying file.")
        return False, "stopped"

    if not title and not description and not cleaned_tags:
        log_message("Info: No valid metadata to write to EXIF.")
        return True, "no_metadata"

    if not EXIFTOOL_PATH:
        log_message("Error: Exiftool path not set.", "error")
        return True, "exiftool_not_found"

    exiftool_cmd = EXIFTOOL_PATH

    clear_command = [
        exiftool_cmd,
        "-XMP:Title=",
        "-XMP:Description=",
        "-XMP:Subject=",
        "-IPTC:Keywords=",
        "-overwrite_original",
        output_path
    ]
    try:
        if stop_event.is_set() or is_stop_requested():
            log_message("Process stopped before cleaning metadata.")
            return False, "stopped"

        result = subprocess.run(clear_command, check=False, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=30,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0:
            log_message("Old metadata cleaned from file")
        else:
             log_message(f"Warning: Failed to clean old metadata (Code: {result.returncode}). Error: {result.stderr.strip()}", "warning")

    except subprocess.TimeoutExpired:
         log_message(f"Warning: Timeout cleaning old metadata.", "warning")
    except Exception as e:
        log_message(f"Warning: Failed to clean old metadata: {e}", "warning")

    if stop_event.is_set() or is_stop_requested():
        log_message("Process stopped after trying to clean metadata.")
        return False, "stopped"

    command = [
        exiftool_cmd,
        "-overwrite_original",
        "-charset", "UTF8",
        "-codedcharacterset=utf8"
    ]

    if title:
        truncated_title = title[:160].strip()
        command.extend([f'-Title={truncated_title}', f'-ObjectName={truncated_title}'])

    if description:
        command.extend([f'-XPComment={description}', f'-UserComment={description}', f'-ImageDescription={description}'])

    if cleaned_tags:
        command.append("-Keywords=")
        command.append("-Subject=")
        for tag in cleaned_tags:
             command.append(f"-Keywords+={tag}")
             command.append(f"-Subject+={tag}")

    command.append(output_path)

    exiftool_process = None
    try:
        if stop_event.is_set() or is_stop_requested():
            log_message("Process stopped before writing new metadata.")
            return False, "stopped"

        exiftool_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        while exiftool_process.poll() is None:
            if stop_event.is_set() or is_stop_requested():
                log_message("Stopping running exiftool process.")
                try:
                    exiftool_process.terminate()
                    time.sleep(0.5)
                    if exiftool_process.poll() is None:
                        exiftool_process.kill()
                except Exception as kill_e:
                     log_message(f"Error stopping exiftool: {kill_e}")
                return False, "stopped"
            time.sleep(0.1)

        stdout, stderr = exiftool_process.communicate()
        return_code = exiftool_process.returncode

        if return_code == 0:
            if stdout and "1 image files updated" in stdout:
                 log_message(f"EXIF metadata successfully written to {os.path.basename(output_path)}")
            else:
                 log_message(f"EXIF metadata written (return code 0, output: {stdout.strip()})")
            if stderr:
                 pass
            return True, "exif_ok"
        else:
            log_message(f"Failed to write EXIF (exit code {return_code}) on {os.path.basename(output_path)}")
            if stderr:
                pass
            if stdout:
                 pass
            return True, "exif_failed"

    except subprocess.TimeoutExpired:
        log_message(f"Error: Exiftool timeout processing {os.path.basename(output_path)}")
        if exiftool_process and exiftool_process.poll() is None:
            try: exiftool_process.kill()
            except: pass
        return True, "exif_failed"
    except FileNotFoundError:
        log_message("Error: 'exiftool' not found during execution.", "error")
        return True, "exiftool_not_found"
    except Exception as e:
        log_message(f"Error running exiftool: {e}", "error")
        if exiftool_process and exiftool_process.poll() is None:
             try: exiftool_process.kill()
             except: pass
        import traceback
        log_message(f"Traceback: {traceback.format_exc()}", "error")
        return True, "exif_failed"

def write_exif_to_video(input_path, output_path, metadata, stop_event):
    title = metadata.get('title', '')
    description = metadata.get('description', '')
    tags = metadata.get('tags', [])
    keyword_count = metadata.get('keyword_count', 49)
    try:
        max_kw = int(keyword_count)
        if max_kw < 1: max_kw = 49
    except Exception:
        max_kw = 49
    cleaned_tags = [tag.strip() for tag in tags if tag.strip()]
    cleaned_tags = list(dict.fromkeys(cleaned_tags))
    cleaned_tags = cleaned_tags[:max_kw]

    if stop_event.is_set() or is_stop_requested():
        log_message("Process stopped before writing metadata to video.")
        return False, "stopped"

    if not os.path.exists(output_path):
         log_message(f"Error: Video output file not found: {output_path}", "error")
         return False, "output_missing"

    if not title and not description and not cleaned_tags:
        log_message("Info: No valid metadata to write to video.")
        return True, "no_metadata"

    if not EXIFTOOL_PATH:
        log_message("Error: Exiftool path not set.", "error")
        return True, "exiftool_not_found"

    exiftool_cmd = EXIFTOOL_PATH
    log_message(f"Using exiftool command for video: {exiftool_cmd}")

    command = [
        exiftool_cmd,
        "-overwrite_original",
        "-charset", "UTF8",
        "-codedcharacterset=utf8"
    ]

    if title:
        truncated_title = title[:160].strip()
        command.extend([f'-Title={truncated_title}', f'-Track1:Title={truncated_title}', f'-Movie:Title={truncated_title}'])

    if description:
        command.extend([
            f'-Description={description}',
            f'-Comment={description}',
            f'-UserComment={description}',
            f'-Track1:Comment={description}',
            f'-Movie:Comment={description}',
            f'-Caption-Abstract={description}'
        ])

    if cleaned_tags:
        command.append("-Keywords=")
        command.append("-Subject=")
        command.append("-Category=")
        for tag in cleaned_tags:
             command.append(f"-Keywords+={tag}")
             command.append(f"-Subject+={tag}")
             command.append(f"-Category+={tag}")

    command.append(output_path)

    exiftool_process = None
    try:
        if stop_event.is_set() or is_stop_requested():
            log_message("Process stopped before writing metadata to video.")
            return False, "stopped"

        exiftool_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        while exiftool_process.poll() is None:
            if stop_event.is_set() or is_stop_requested():
                log_message("Stopping exiftool process for video.")
                try:
                    exiftool_process.terminate()
                    time.sleep(0.5)
                    if exiftool_process.poll() is None:
                        exiftool_process.kill()
                except Exception as kill_e:
                     log_message(f"Error stopping exiftool for video: {kill_e}")
                return False, "stopped"
            time.sleep(0.1)

        stdout, stderr = exiftool_process.communicate()
        return_code = exiftool_process.returncode

        if return_code == 0:
            log_message(f"Metadata successfully written to video file {os.path.basename(output_path)}")
            return True, "exif_ok"
        else:
            log_message(f"Failed to write metadata to video (exit code {return_code}) on {os.path.basename(output_path)}")
            return True, "exif_failed"

    except subprocess.TimeoutExpired:
        log_message(f"Error: Exiftool timeout processing video {os.path.basename(output_path)}")
        if exiftool_process and exiftool_process.poll() is None:
            try: exiftool_process.kill()
            except: pass
        return True, "exif_failed"
    except FileNotFoundError:
        log_message("Error: 'exiftool' not found during video execution.", "error")
        return True, "exiftool_not_found"
    except Exception as e:
        log_message(f"Error running exiftool for video: {e}", "error")
        if exiftool_process and exiftool_process.poll() is None:
             try: exiftool_process.kill()
             except: pass
        import traceback
        log_message(f"Traceback: {traceback.format_exc()}", "error")
        return True, "exif_failed"
