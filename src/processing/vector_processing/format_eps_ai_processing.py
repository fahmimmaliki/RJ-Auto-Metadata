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

# src/processing/vector_processing/format_eps_ai_processing.py
import os
import time
import subprocess
import platform
from src.utils.logging import log_message
from src.api.gemini_api import check_stop_event

def convert_eps_to_jpg(eps_path, output_jpg_path, ghostscript_path, stop_event=None):
    filename = os.path.basename(eps_path)
    log_message(f"Starting conversion of EPS/AI to JPG: {filename}")

    if not ghostscript_path:
        error_message = "Error: Ghostscript executable path not found during application startup check."
        log_message(f"✗ {error_message}")
        return False, error_message

    if check_stop_event(stop_event, f"Conversion of EPS/AI cancelled before start: {filename}"):
        return False, f"Conversion cancelled before start: {filename}"

    command = [
        ghostscript_path,
        "-sDEVICE=jpeg",
        "-dEPSCrop",
        "-dJPEGQ=90",
        "-dBATCH",
        "-dNOPAUSE",
        "-dSAFER",
        "-dGraphicsAlphaBits=4",
        "-dTextAlphaBits=4",
        f"-sOutputFile={output_jpg_path}",
        eps_path
    ]

    success = False
    final_error_message = f"Unknown error during Ghostscript conversion for {filename}."
    process = None

    try:
        creationflags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags
        )

        start_time = time.time()
        timeout_seconds = 180

        while process.poll() is None:
            if check_stop_event(stop_event, f"Stopping Ghostscript conversion: {filename}"):
                log_message(f"Stop event triggered, terminating Ghostscript process for {filename}")
                try:
                    process.terminate()
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    log_message(f"Ghostscript did not terminate, killing process for {filename}")
                    process.kill()
                except Exception as term_err:
                    log_message(f"Error during termination of Ghostscript for {filename}: {term_err}")
                return False, f"Ghostscript conversion stopped: {filename}"

            if time.time() - start_time > timeout_seconds:
                log_message(f"Ghostscript process timed out (> {timeout_seconds}s) for {filename}, terminating.")
                try:
                    process.terminate()
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    log_message(f"Ghostscript did not terminate after timeout, killing process for {filename}")
                    process.kill()
                except Exception as term_err:
                    log_message(f"Error during termination of Ghostscript after timeout for {filename}: {term_err}")
                return False, f"Ghostscript conversion timeout: {filename}"

            time.sleep(0.1)

        try:
            stdout, stderr = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            log_message(f"Ghostscript communicate() timed out for {filename}. Killing process.")
            process.kill()
            try:
                stdout, stderr = process.communicate()
            except Exception as final_comm_err:
                 log_message(f"Error getting output even after kill for {filename}: {final_comm_err}")
                 stdout, stderr = b"", b""
        except Exception as comm_err:
            log_message(f"Error during Ghostscript communicate() for {filename}: {comm_err}")
            stdout, stderr = b"", b""

        return_code = process.returncode

        if return_code == 0:
            if os.path.exists(output_jpg_path) and os.path.getsize(output_jpg_path) > 100:
                try:
                    from PIL import Image
                    with Image.open(output_jpg_path) as img:
                        img.verify()
                    log_message(f"✓ Conversion of EPS/AI to JPG successful and file valid: {os.path.basename(output_jpg_path)}")
                except Exception as img_err:
                    log_message(f"✗ JPEG result of conversion corrupt or invalid: {img_err}")
                    if os.path.exists(output_jpg_path):
                        try: os.remove(output_jpg_path)
                        except Exception: pass
                    return False, f"Ghostscript successful but JPEG result corrupt: {img_err}"
                
                success = True
                final_error_message = None
            else:
                final_error_message = f"Ghostscript finished (code 0) but output file '{os.path.basename(output_jpg_path)}' is invalid or too small."
                log_message(f"✗ {final_error_message}")
                if os.path.exists(output_jpg_path):
                    try: os.remove(output_jpg_path)
                    except Exception: pass
        else:
            try:
                error_output = stderr.decode(errors='replace').strip()
            except Exception as decode_err:
                error_output = f"(Failed to decode stderr: {decode_err})"
            final_error_message = f"Failed conversion of EPS/AI with Ghostscript (code {return_code}): {error_output[:350]}{'...' if len(error_output) > 350 else ''}"
            log_message(f"✗ {final_error_message}")

    except FileNotFoundError:
        final_error_message = f"Fatal Error: Ghostscript executable not found at the expected path: {ghostscript_path}"
        log_message(f"✗ {final_error_message}")
    except Exception as e:
        final_error_message = f"Unexpected error when running Ghostscript process: {e}"
        log_message(f"✗ {final_error_message}")
        if process and process.poll() is None:
             try: process.kill()
             except Exception: pass

    if not success and os.path.exists(output_jpg_path):
        try:
            os.remove(output_jpg_path)
            log_message(f"Removing failed output file: {os.path.basename(output_jpg_path)}")
        except Exception as del_err:
            log_message(f"Failed to remove output file {os.path.basename(output_jpg_path)}: {del_err}")

    return success, final_error_message