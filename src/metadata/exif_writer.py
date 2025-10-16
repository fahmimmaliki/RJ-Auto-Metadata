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
import re
import platform
from sqlalchemy import text
from src.utils.logging import log_message
from src.api.gemini_api import check_stop_event, is_stop_requested

def check_exiftool_exists():
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        result = subprocess.run(["exiftool", "-ver"], check=True, capture_output=True, text=True, creationflags=creation_flags)
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
                         creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                         test_result = subprocess.run([normalized_path, "-ver"], check=True, capture_output=True, text=True, creationflags=creation_flags)
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
EXIFTOOL_PATH = None

def smart_truncate_title_for_metadata(title, max_length=200):
    if not title:
        return ""
    title = str(title).strip()
    sanitized = re.sub(r'[\r\n\t]+', ' ', str(title))
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    sanitized = sanitized.replace(':', ' -') 
    sanitized = re.sub(r'[^\w\s\-\.\,]', '', sanitized)
    if len(sanitized) <= max_length:
        if not sanitized.endswith('.') and len(sanitized) < max_length:
            sanitized += '.'
        return sanitized
    truncated = sanitized[:max_length]
    last_period_pos = truncated.rfind('.')
    
    if last_period_pos > 0 and last_period_pos < max_length - 1:
        result = sanitized[:last_period_pos + 1]
        return result
    result = sanitized[:max_length - 1] + '.'
    return result

def sanitize_metadata_text(text, max_length=None):
    if not text:
        return ""
    sanitized = re.sub(r'[\r\n\t]+', ' ', str(text))
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    sanitized = sanitized.replace(':', ' -')
    sanitized = re.sub(r'[^\w\s\-\.\,]', '', sanitized)
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()
    return sanitized

def sanitize_keyword(keyword):
    if not keyword:
        return ""
    sanitized = re.sub(r'[\r\n\t]+', ' ', str(keyword))
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    sanitized = re.sub(r'[^\w\s]', '', sanitized) 
    sanitized = sanitized.strip()[:64] 
    return sanitized if sanitized else None

def get_file_format_metadata_support(file_path):
    if not file_path:
        return {'xmp': True, 'iptc': True, 'strategy': 'xmp_first', 'tags': {}} 
    ext = os.path.splitext(file_path)[1].lower()
    format_support = {
        '.jpg': {
            'xmp': True, 
            'iptc': True, 
            'strategy': 'xmp_first',
            'tags': {
                'xmp': {
                    'title': '-XMP-dc:Title',
                    'description': '-XMP-dc:Description', 
                    'keywords': '-XMP-dc:Subject'
                },
                'iptc': {
                    'title': '-IPTC:ObjectName',
                    'description': '-IPTC:Caption-Abstract',
                    'keywords': '-IPTC:Keywords'
                }
            }
        },
        '.jpeg': {
            'xmp': True, 
            'iptc': True, 
            'strategy': 'xmp_first',
            'tags': {
                'xmp': {
                    'title': '-XMP-dc:Title',
                    'description': '-XMP-dc:Description', 
                    'keywords': '-XMP-dc:Subject'
                },
                'iptc': {
                    'title': '-IPTC:ObjectName',
                    'description': '-IPTC:Caption-Abstract',
                    'keywords': '-IPTC:Keywords'
                }
            }
        },
        '.eps': {
            'xmp': False, 
            'iptc': True, 
            'strategy': 'eps_simple',
            'tags': {} 
        },
        
        '.ai': {
            'xmp': True, 
            'iptc': False, 
            'strategy': 'xmp_only',
            'tags': {
                'xmp': {
                    'title': '-XMP-dc:Title',
                    'description': '-XMP-dc:Description', 
                    'keywords': '-XMP-dc:Subject'
                }
            }
        },
        '.svg': {
            'xmp': False, 
            'iptc': False, 
            'strategy': 'not_supported',
            'tags': {}
        },
        '.png': {
            'xmp': False, 
            'iptc': False, 
            'strategy': 'not_supported',
            'tags': {}
        },
        '.tif': {'xmp': True, 'iptc': True, 'strategy': 'xmp_first', 'tags': {}},
        '.tiff': {'xmp': True, 'iptc': True, 'strategy': 'xmp_first', 'tags': {}},
        '.dng': {'xmp': True, 'iptc': True, 'strategy': 'xmp_first', 'tags': {}},
        '.cr2': {'xmp': True, 'iptc': True, 'strategy': 'xmp_first', 'tags': {}},
        '.cr3': {'xmp': True, 'iptc': True, 'strategy': 'xmp_first', 'tags': {}},
        '.nef': {'xmp': True, 'iptc': True, 'strategy': 'xmp_first', 'tags': {}},
        '.arw': {'xmp': True, 'iptc': True, 'strategy': 'xmp_first', 'tags': {}},
        '.mp4': {'xmp': True, 'iptc': False, 'strategy': 'xmp_only', 'tags': {}},
        '.mov': {'xmp': True, 'iptc': False, 'strategy': 'xmp_only', 'tags': {}},
        '.avi': {'xmp': False, 'iptc': False, 'strategy': 'none', 'tags': {}},
    }
    return format_support.get(ext, {'xmp': True, 'iptc': True, 'strategy': 'xmp_first', 'tags': {}})  # Default to XMP first if unknown

def write_exif_with_exiftool(image_path, output_path, metadata, stop_event):
    title = metadata.get('title', '')
    description = metadata.get('description', '')
    tags = metadata.get('tags', [])
    keyword_count = metadata.get('keyword_count', 49)
    try:
        if isinstance(keyword_count, str):
            max_kw = int(keyword_count.strip())
        else:
            max_kw = int(keyword_count)
        if max_kw < 1: max_kw = 49
        if max_kw > 100: max_kw = 49 
    except Exception as e:
        log_message(f"Warning: Invalid keyword_count '{keyword_count}', using default 49: {e}", "warning")
        max_kw = 49
    if isinstance(tags, str):
        raw_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
    else:
        raw_tags = [str(tag).strip() for tag in tags if str(tag).strip()]
    cleaned_tags = []
    for tag in raw_tags:
        sanitized_tag = sanitize_keyword(tag)
        if sanitized_tag and sanitized_tag not in cleaned_tags:  
            cleaned_tags.append(sanitized_tag)
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
    format_support = get_file_format_metadata_support(output_path)
    strategy = format_support.get('strategy', 'xmp_first')
    available_tags = format_support.get('tags', {})
    processed_title = smart_truncate_title_for_metadata(title, 200) if title else ""
    processed_description = sanitize_metadata_text(description, 2000) if description else ""
    exiftool_cmd = EXIFTOOL_PATH
    clear_command = [exiftool_cmd, "-overwrite_original"]
    if 'xmp' in available_tags:
        clear_command.extend([
            "-XMP-dc:Title=",
            "-XMP-dc:Description=", 
            "-XMP-dc:Subject="
        ])
    if 'iptc' in available_tags:
        clear_command.extend([
            "-IPTC:ObjectName=",
            "-IPTC:Caption-Abstract=",
            "-IPTC:Keywords="
        ])
    if 'native' in available_tags:
        ext = os.path.splitext(output_path)[1].lower()
        if ext == '.eps':
            clear_command.extend([
                "-PostScript:Title=",
                "-PostScript:Subject=",
                "-PostScript:Keywords="
            ])
        elif ext == '.png':
            clear_command.extend([
                "-PNG:Title=",
                "-PNG:Description=",
                "-PNG:Subject="
            ])
    if strategy == 'eps_simple':
        clear_command.extend([
            "-Title=",
            "-ObjectName=", 
            "-Keywords=",
            "-Subject=",
            "-XPComment=",
            "-UserComment=",
            "-ImageDescription=",
            "-IPTC:Headline=",
            "-IPTC:Caption-Abstract=",
            "-PostScript:Title=",
            "-PostScript:Subject=",
            "-PostScript:Keywords="
        ])
    if strategy == 'xmp_only':
        clear_command.extend([
            "-XMP-dc:Title=",
            "-XMP-dc:Description=", 
            "-XMP-dc:Subject=",
            "-XMP:Title=",
            "-XMP:Description=",
            "-XMP:Keywords=",
            "-XMP:Subject=",
            "-Title=",
            "-Description=",
            "-Keywords=",
            "-Subject="
        ])
    if strategy == 'eps_comprehensive':
        clear_command.extend([
            "-PostScript:Title=",
            "-PostScript:Subject=", 
            "-PostScript:Keywords=",
            "-IPTC:ObjectName=",
            "-IPTC:Headline=",
            "-IPTC:Caption-Abstract=",
            "-IPTC:Keywords=",
            "-EXIF:ImageDescription=",
            "-EXIF:XPTitle=",
            "-EXIF:UserComment=",
            "-Title=",  
            "-Description=",
            "-Keywords="
        ])
    clear_command.append(output_path)
    try:
        if stop_event.is_set() or is_stop_requested():
            return False, "stopped"
        clearing_fields = [arg for arg in clear_command if '=' in arg and arg.endswith('=')]
        creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        result = subprocess.run(clear_command, check=False, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=30,
                                creationflags=creation_flags)
        if result.returncode == 0:
            log_message(f"Old metadata successfully cleared from {os.path.basename(output_path)}")
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
    if strategy == 'native_first':
        if 'native' in available_tags and processed_title:
            command.append(f"{available_tags['native']['title']}={processed_title}")
        if 'native' in available_tags and processed_description:
            command.append(f"{available_tags['native']['description']}={processed_description}")
        if 'native' in available_tags and cleaned_tags:
            keywords_str = ', '.join(cleaned_tags)
            command.append(f"{available_tags['native']['keywords']}={keywords_str}")
        if 'xmp' in available_tags:
            if processed_title:
                command.append(f"{available_tags['xmp']['title']}={processed_title}")
            if processed_description:
                command.append(f"{available_tags['xmp']['description']}={processed_description}")
            if cleaned_tags:
                for tag in cleaned_tags:
                    command.append(f"{available_tags['xmp']['keywords']}+={tag}")
    elif strategy == 'dual_format':
        if 'xmp' in available_tags:
            if processed_title:
                command.append(f"{available_tags['xmp']['title']}={processed_title}")
            if processed_description:
                command.append(f"{available_tags['xmp']['description']}={processed_description}")
            if cleaned_tags:
                for tag in cleaned_tags:
                    command.append(f"{available_tags['xmp']['keywords']}+={tag}")
        if 'native' in available_tags:
            if processed_title:
                command.append(f"{available_tags['native']['title']}={processed_title}")
            if processed_description:
                command.append(f"{available_tags['native']['description']}={processed_description}")
            if cleaned_tags:
                keywords_str = ', '.join(cleaned_tags)
                command.append(f"{available_tags['native']['keywords']}={keywords_str}")
    elif strategy == 'xmp_first':
        if 'xmp' in available_tags:
            if processed_title:
                command.append(f"{available_tags['xmp']['title']}={processed_title}")
            if processed_description:
                command.append(f"{available_tags['xmp']['description']}={processed_description}")
            if cleaned_tags:
                command.append(f"{available_tags['xmp']['keywords']}=")
                for tag in cleaned_tags:
                    command.append(f"{available_tags['xmp']['keywords']}+={tag}")
        if 'iptc' in available_tags:
            if processed_title:
                iptc_title = processed_title[:64] if len(processed_title) > 64 else processed_title
                command.append(f"{available_tags['iptc']['title']}={iptc_title}")
            if processed_description:
                iptc_description = processed_description[:2000] if len(processed_description) > 2000 else processed_description
                command.append(f"{available_tags['iptc']['description']}={iptc_description}")
            if cleaned_tags:
                command.append(f"{available_tags['iptc']['keywords']}=")
                for tag in cleaned_tags:
                    safe_tag = tag[:64] if len(tag) > 64 else tag
                    command.append(f"{available_tags['iptc']['keywords']}+={safe_tag}")
    elif strategy == 'xmp_only':
        command.extend([
            "-XMP-dc:Title=", "-XMP-dc:Description=", "-XMP-dc:Subject=",
            "-XMP:Title=", "-XMP:Description=", "-XMP:Keywords=", "-XMP:Subject=",
            "-Title=", "-Description=", "-Keywords=", "-Subject="
        ])
        if 'xmp' in available_tags:
            if processed_title:
                command.append(f"{available_tags['xmp']['title']}={processed_title}")
            if processed_description:
                command.append(f"{available_tags['xmp']['description']}={processed_description}")
            if cleaned_tags:
                command.append(f"{available_tags['xmp']['keywords']}=")
                for tag in cleaned_tags:
                    command.append(f"{available_tags['xmp']['keywords']}+={tag}")
                log_message(f"XMP-only: Added {len(cleaned_tags)} keywords after clean reset", "debug")
    elif strategy == 'eps_simple':
        command.extend([
            "-Title=", "-ObjectName=", "-Keywords=", "-Subject=",
            "-XPComment=", "-UserComment=", "-ImageDescription=",
            "-IPTC:Headline=", "-IPTC:Caption-Abstract="
        ])
        if processed_title:
            truncated_title = processed_title[:160].strip()
            command.extend([f'-Title={truncated_title}', f'-ObjectName={truncated_title}'])
            command.append(f'-IPTC:Headline={truncated_title[:64]}')
        if processed_description:
            command.extend([f'-XPComment={processed_description}', f'-UserComment={processed_description}', f'-ImageDescription={processed_description}'])
            iptc_desc = processed_description[:2000] if len(processed_description) > 2000 else processed_description
            command.append(f'-IPTC:Caption-Abstract={iptc_desc}')
        if cleaned_tags:
            command.extend(["-Keywords=", "-Subject="])
            for tag in cleaned_tags:
                command.append(f"-Keywords+={tag}")
                command.append(f"-Subject+={tag}")
    elif strategy == 'eps_comprehensive':
        if 'postscript' in available_tags:
            if processed_title:
                command.append(f"{available_tags['postscript']['title']}={processed_title}")
            if processed_description:
                command.append(f"{available_tags['postscript']['description']}={processed_description}")
            if cleaned_tags:
                keywords_str = ', '.join(cleaned_tags)
                command.append(f"{available_tags['postscript']['keywords']}={keywords_str}")
        if 'iptc' in available_tags:
            if processed_title:
                iptc_title = processed_title[:64] if len(processed_title) > 64 else processed_title
                command.append(f"{available_tags['iptc']['title']}={iptc_title}")
                if 'headline' in available_tags['iptc']:
                    command.append(f"{available_tags['iptc']['headline']}={iptc_title}")
            if processed_description:
                iptc_description = processed_description[:2000] if len(processed_description) > 2000 else processed_description
                command.append(f"{available_tags['iptc']['description']}={iptc_description}")
            if cleaned_tags:
                command.append(f"{available_tags['iptc']['keywords']}=")
                for tag in cleaned_tags:
                    safe_tag = tag[:64] if len(tag) > 64 else tag
                    command.append(f"{available_tags['iptc']['keywords']}+={safe_tag}")
        if 'exif' in available_tags:
            if processed_title:
                command.append(f"{available_tags['exif']['title']}={processed_title}")
                if 'title2' in available_tags['exif']:
                    command.append(f"{available_tags['exif']['title2']}={processed_title}")
            if processed_description:
                command.append(f"{available_tags['exif']['description']}={processed_description}")
        if 'generic' in available_tags:
            if processed_title:
                command.append(f"{available_tags['generic']['title']}={processed_title}")
            if processed_description:
                command.append(f"{available_tags['generic']['description']}={processed_description}")
            if cleaned_tags:
                keywords_str = ', '.join(cleaned_tags)
                command.append(f"{available_tags['generic']['keywords']}={keywords_str}")
    elif strategy == 'postscript_only':
        if 'native' in available_tags:
            if processed_title:
                command.append(f"{available_tags['native']['title']}={processed_title}")
            if processed_description:
                command.append(f"{available_tags['native']['description']}={processed_description}")
            if cleaned_tags:
                keywords_str = ', '.join(cleaned_tags)
                command.append(f"{available_tags['native']['keywords']}={keywords_str}")
    else:
        if processed_title:
            command.append(f'-XMP-dc:Title={processed_title}')
        if processed_description:
            command.append(f'-XMP-dc:Description={processed_description}')
        if cleaned_tags:
            for tag in cleaned_tags:
                command.append(f'-XMP-dc:Subject+={tag}')
    command.append(output_path)
    exiftool_process = None
    try:
        if stop_event.is_set() or is_stop_requested():
            log_message("Process stopped before writing new metadata.")
            return False, "stopped"
        creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        exiftool_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace',
            creationflags=creation_flags
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
                 log_message(f"Metadata successfully written to {os.path.basename(output_path)}")
            else:
                 log_message(f"Metadata written (return code 0, output: {stdout.strip()})")
            if stderr:
                 pass
            return True, "exif_ok"
        else:
            log_message(f"Failed to write metadata (exit code {return_code}) on {os.path.basename(output_path)}")
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
        if isinstance(keyword_count, str):
            max_kw = int(keyword_count.strip())
        else:
            max_kw = int(keyword_count)
        if max_kw < 1: max_kw = 49
        if max_kw > 100: max_kw = 49  
    except Exception as e:
        max_kw = 49
    if isinstance(tags, str):
        raw_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
    else:
        raw_tags = [str(tag).strip() for tag in tags if str(tag).strip()]
    cleaned_tags = []
    for tag in raw_tags:
        sanitized_tag = sanitize_keyword(tag)
        if sanitized_tag and sanitized_tag not in cleaned_tags:  
            cleaned_tags.append(sanitized_tag)
    cleaned_tags = cleaned_tags[:max_kw]
    if len(cleaned_tags) > 0:
        log_message(f"Video keywords processed: {len(cleaned_tags)}/{max_kw} keywords will be embedded", "debug")
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
    processed_title = smart_truncate_title_for_metadata(title, 200) if title else ""
    processed_description = sanitize_metadata_text(description, 200) if description else ""
    format_support = get_file_format_metadata_support(output_path)
    log_message(f"Video format support for {os.path.splitext(output_path)[1]}: XMP={format_support['xmp']}, IPTC={format_support['iptc']}")
    exiftool_cmd = EXIFTOOL_PATH
    command = [
        exiftool_cmd,
        "-overwrite_original",
        "-charset", "UTF8",
        "-codedcharacterset=utf8"
    ]
    if processed_title:
        command.extend([
            f'-Title={processed_title}',
            f'-XMP:Title={processed_title}',
            f'-QuickTime:Title={processed_title}',
            f'-IPTC:Title={processed_title}'
        ])
    if processed_description:
        command.extend([
            f'-Description={processed_description}',
            f'-XMP:Description={processed_description}',
            f'-Comment={processed_description}',
            f'-QuickTime:Description={processed_description}',
            f'-IPTC:Description={processed_description}'
        ])
    if cleaned_tags:
        limited_tags = cleaned_tags[:49]
        command.extend(["-Keywords=", "-Subject="])
        keywords_str = ",".join(limited_tags)
        command.extend([f"-Keywords={keywords_str}"])
        command.extend([f"-Subject={keywords_str}"])
        if format_support['xmp']:
            command.extend([
                f"-XMP:Keywords={keywords_str}",
                f"-XMP:Subject={keywords_str}"
            ])
    command.append(output_path)
    return _execute_video_exiftool_command(command, output_path, stop_event, processed_title, processed_description, cleaned_tags[:49] if cleaned_tags else [])

def _execute_video_exiftool_command(command, output_path, stop_event, title, description, tags):
    exiftool_process = None
    try:
        if stop_event.is_set() or is_stop_requested():
            log_message("Process stopped before writing metadata to video.")
            return False, "stopped"
        
        creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        exiftool_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace',
            creationflags=creation_flags
        )

        timeout_seconds = 45
        start_time = time.time()
        
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
            
            if time.time() - start_time > timeout_seconds:
                log_message(f"Exiftool timeout ({timeout_seconds}s) reached for video. Trying minimal fallback.")
                try:
                    exiftool_process.terminate()
                    time.sleep(1)
                    if exiftool_process.poll() is None:
                        exiftool_process.kill()
                        time.sleep(0.5)
                except Exception as timeout_e:
                    log_message(f"Error terminating timed-out exiftool process: {timeout_e}")
                
                return _try_minimal_video_metadata(output_path, stop_event, title, description)
            
            time.sleep(0.1)

        stdout, stderr = exiftool_process.communicate()
        return_code = exiftool_process.returncode

        if return_code == 0:
            return True, "exif_ok"
        else:
            return _try_minimal_video_metadata(output_path, stop_event, title, description)

    except subprocess.TimeoutExpired:
        log_message(f"Error: Exiftool timeout processing video {os.path.basename(output_path)}")
        if exiftool_process and exiftool_process.poll() is None:
            try: exiftool_process.kill()
            except: pass
        return _try_minimal_video_metadata(output_path, stop_event, title, description)
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

def _try_minimal_video_metadata(output_path, stop_event, title, description):
    if stop_event.is_set() or is_stop_requested():
        return False, "stopped"
    minimal_command = [
        EXIFTOOL_PATH,
        "-overwrite_original",
        "-charset", "UTF8"
    ]
    if title:
        title_short = title[:200] 
        minimal_command.extend([
            f"-Title={title_short}",
            f"-XMP:Title={title_short}"
        ])
    if description:
        desc_short = description[:200]
        minimal_command.extend([
            f"-Description={desc_short}",
            f"-XMP:Description={desc_short}"
        ])
    
    minimal_command.append(output_path)
    
    try:
        log_message(f"Running minimal command with {len(minimal_command)} arguments")
        creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        result = subprocess.run(
            minimal_command,
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=creation_flags
        )
    except subprocess.TimeoutExpired:
        log_message("Minimal video metadata command also timed out")
        return True, "exif_timeout"
    except Exception as e:
        log_message(f"Error in minimal video metadata: {e}")
        return True, "exif_failed"
