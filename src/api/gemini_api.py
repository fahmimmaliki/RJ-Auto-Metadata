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

# src/api/gemini_api.py
import os
import sys
import random
import requests
import base64
import json
import time
import re
import threading
from collections import defaultdict
from src.utils.logging import log_message

try:
    from google import genai
    from google.genai import types
    GENAI_SDK_AVAILABLE = True
except ImportError:
    GENAI_SDK_AVAILABLE = False
    log_message("Google Generative AI SDK not available. Using REST API fallback.", "warning")
from src.api.gemini_prompts import (
    PROMPT_TEXT, PROMPT_TEXT_PNG, PROMPT_TEXT_VIDEO,
    PROMPT_TEXT_BALANCED, PROMPT_TEXT_PNG_BALANCED, PROMPT_TEXT_VIDEO_BALANCED,
    PROMPT_TEXT_FAST, PROMPT_TEXT_PNG_FAST, PROMPT_TEXT_VIDEO_FAST
)

_genai_client = None
_genai_client_lock = threading.Lock()

def _get_genai_client(api_key):
    global _genai_client
    
    if not GENAI_SDK_AVAILABLE:
        return None
        
    with _genai_client_lock:
        if _genai_client is None:
            try:
                _genai_client = genai.Client(api_key=api_key)
                log_message("Google Generative AI SDK client initialized", "info")
            except Exception as e:
                log_message(f"Failed to initialize genai client: {e}", "error")
                return None
        return _genai_client

def _make_genai_request(model_name, prompt_text, image_data, max_output_tokens, api_key, thinking_budget=None, stop_event=None):
    try:
        if stop_event and stop_event.is_set():
            return None, "Process stopped before SDK request"
        client = _get_genai_client(api_key)
        if not client:
            return None, "Failed to get genai client"
        content_parts = [prompt_text]
        
        if image_data:
            import io
            from PIL import Image
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            content_parts.append(image)
        
        if stop_event and stop_event.is_set():
            return None, "Process stopped during content preparation"
        
        thinking_config = None
        if thinking_budget is not None and "gemini-2.5" in model_name:
            thinking_config = types.ThinkingConfig(thinking_budget=thinking_budget)
        
        generation_config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=max_output_tokens,
            top_p=0.8,
            top_k=40,
            thinking_config=thinking_config
        )
        
        if stop_event and stop_event.is_set():
            return None, "Process stopped before API call"
        
        response = client.models.generate_content(
            model=model_name,
            contents=content_parts,
            config=generation_config
        )
        
        return response, None
        
    except Exception as e:
        return None, str(e)

GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    # "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",  
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite-preview-06-17",
    "gemini-2.5-pro"
]

THINKING_BUDGET_PRO = -1
THINKING_BUDGET_FLASH = -1
THINKING_BUDGET_FLASH_LITE = 0

DEFAULT_MODEL = "gemini-1.5-flash"
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash"
]
MODEL_LAST_USED = defaultdict(float)
MODEL_LOCK = threading.Lock()
API_KEY_LAST_USED = defaultdict(float) 
API_KEY_LOCK = threading.Lock() 
API_KEY_MIN_INTERVAL = 2.0 


API_TIMEOUT = 60
API_MAX_RETRIES = 3
API_RETRY_DELAY = 10

FORCE_STOP_FLAG = False

def select_smart_api_key(api_keys_list: list) -> str | None:
    if not api_keys_list:
        return None

    with API_KEY_LOCK:
        key_statuses = []
        for key in api_keys_list:
            last_used_time = API_KEY_LAST_USED.get(key, 0)
            key_statuses.append((last_used_time, key))

        key_statuses.sort(key=lambda x: x[0])

        if not key_statuses:
            return None
            
        selected_key = key_statuses[0][1]
        API_KEY_LAST_USED[selected_key] = time.time() 
        return selected_key

def select_best_fallback_model(fallback_models_list: list, excluded_model_name: str | None = None) -> str | None:
    if not fallback_models_list:
        return None

    model_statuses = []
    for model_name in fallback_models_list:
        if model_name == excluded_model_name:
            log_message(f"Model fallback '{model_name}' skipped because it's the same as the failed new model.", "info")
            continue
        if model_name not in GEMINI_MODELS:
            log_message(f"Model fallback '{model_name}' not in GEMINI_MODELS list, skipped.", "warning")
            continue
        last_used_time = MODEL_LAST_USED.get(model_name, 0)
        model_statuses.append((last_used_time, model_name))

    if not model_statuses:
        return None

    model_statuses.sort(key=lambda x: x[0])
        
    return model_statuses[0][1]

def is_stop_requested():
    global FORCE_STOP_FLAG
    return FORCE_STOP_FLAG

def set_force_stop():
    global FORCE_STOP_FLAG
    FORCE_STOP_FLAG = True
    log_message("Force stop flag has been activated. All processes will stop immediately.", "warning")

def reset_force_stop():
    global FORCE_STOP_FLAG
    FORCE_STOP_FLAG = False

def check_stop_event(stop_event, message=None):
    if is_stop_requested():
        if message: log_message(message)
        return True
    if stop_event is not None:
        try:
            is_set = stop_event.is_set()
            if is_set and message: log_message(message)
            return is_set
        except Exception as e:
            log_message(f"Error checking stop_event: {e}")
            return False
    return False

def get_api_endpoint(model_name):
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

def select_next_model():
    with MODEL_LOCK:
        sorted_models = sorted(GEMINI_MODELS, key=lambda m: MODEL_LAST_USED.get(m, 0))
        
        selected_model = sorted_models[0]
        
        MODEL_LAST_USED[selected_model] = time.time()
        return selected_model

def wait_for_model_cooldown(model_name, stop_event=None):
    return

def wait_for_api_key_cooldown(api_key, stop_event=None):
    return

def _attempt_gemini_request(
    image_paths,
    current_api_key: str,
    model_to_use: str,
    stop_event,
    use_png_prompt: bool,
    use_video_prompt: bool,
    priority: str,
    image_basename: str,
    is_vector_conversion: bool = False
) -> tuple:

    if check_stop_event(stop_event, f"API request cancelled before model cooldown: {image_basename}"):
        return -2, None, "stopped", "Process stopped before model cooldown"

    wait_for_model_cooldown(model_to_use, stop_event)

    if check_stop_event(stop_event, f"API request cancelled after model cooldown: {image_basename}"):
        return -2, None, "stopped", "Process stopped after model cooldown"

    api_endpoint = get_api_endpoint(model_to_use)
    
    if isinstance(image_paths, str):
        image_paths = [image_paths]
        log_message(f"Sending {image_basename} to model {model_to_use} (API Key: ...{current_api_key[-5:]})", "info")
    else:
        log_message(f"Sending {len(image_paths)} frame(s) from {image_basename} to model {model_to_use} (API Key: ...{current_api_key[-5:]})", "info")

    final_is_vector_conversion = is_vector_conversion or "converted" in image_basename.lower()
    is_video_processing = isinstance(image_paths, list) and len(image_paths) > 1

    selected_prompt_text = PROMPT_TEXT
    if priority == "Less":
        if use_video_prompt: selected_prompt_text = PROMPT_TEXT_VIDEO_FAST
        elif use_png_prompt: selected_prompt_text = PROMPT_TEXT_PNG_FAST
        else: selected_prompt_text = PROMPT_TEXT_FAST
    elif priority == "Balanced":
        if use_video_prompt: selected_prompt_text = PROMPT_TEXT_VIDEO_BALANCED
        elif use_png_prompt: selected_prompt_text = PROMPT_TEXT_PNG_BALANCED
        else: selected_prompt_text = PROMPT_TEXT_BALANCED
    else:
        if use_video_prompt: selected_prompt_text = PROMPT_TEXT_VIDEO
        elif use_png_prompt: selected_prompt_text = PROMPT_TEXT_PNG
        else: selected_prompt_text = PROMPT_TEXT
    
    prompt_name = "UNKNOWN"
    if selected_prompt_text == PROMPT_TEXT: prompt_name = "PROMPT_TEXT (Detailed)"
    elif selected_prompt_text == PROMPT_TEXT_PNG: prompt_name = "PROMPT_TEXT_PNG (Detailed)"
    elif selected_prompt_text == PROMPT_TEXT_VIDEO: prompt_name = "PROMPT_TEXT_VIDEO (Detailed)"
    elif selected_prompt_text == PROMPT_TEXT_BALANCED: prompt_name = "PROMPT_TEXT_BALANCED (Balanced)"
    elif selected_prompt_text == PROMPT_TEXT_PNG_BALANCED: prompt_name = "PROMPT_TEXT_PNG_BALANCED (Balanced)"
    elif selected_prompt_text == PROMPT_TEXT_VIDEO_BALANCED: prompt_name = "PROMPT_TEXT_VIDEO_BALANCED (Balanced)"
    elif selected_prompt_text == PROMPT_TEXT_FAST: prompt_name = "PROMPT_TEXT_FAST (Less)"
    elif selected_prompt_text == PROMPT_TEXT_PNG_FAST: prompt_name = "PROMPT_TEXT_PNG_FAST (Less)"
    elif selected_prompt_text == PROMPT_TEXT_VIDEO_FAST: prompt_name = "PROMPT_TEXT_VIDEO_FAST (Less)"
    
    parts = [{"text": selected_prompt_text}]
    
    for img_path in image_paths:
        try:
            file_size = os.path.getsize(img_path)
            
            with open(img_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")
            
            _, ext = os.path.splitext(img_path)
            mime_type = f"image/{ext.lower().replace('.', '')}"
            if mime_type == "image/jpg": mime_type = "image/jpeg"
            if mime_type not in ["image/png", "image/jpeg", "image/webp", "image/heic", "image/heif"]:
                mime_type = "image/jpeg"
            
            parts.append({"inline_data": {"mime_type": mime_type, "data": image_data}})
            
        except Exception as e:
            log_message(f"Error reading image file ({os.path.basename(img_path)}): {e}", "error")
            return -3, None, "file_read", str(e)

    max_output_tokens = 800
    
    if "gemini-2.5-pro" in model_to_use:
        max_output_tokens = 15000
            
    elif "gemini-2.5-flash" in model_to_use and "lite" not in model_to_use:
        max_output_tokens = 12000
            
    elif "gemini-2.5-flash-lite-preview-06-17" in model_to_use:
        max_output_tokens = 15000
    
    payload = {
        "contents": [{"parts": parts}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
        ],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": max_output_tokens, "topP": 0.8, "topK": 40}
    }
    
    if GENAI_SDK_AVAILABLE:
        thinking_budget = None
        if "gemini-2.5" in model_to_use:
            if "flash-lite-preview-06-17" in model_to_use:
                thinking_budget = THINKING_BUDGET_FLASH_LITE
                log_message(f"Thinking disabled for {model_to_use}", "info")
            elif "pro" in model_to_use:
                thinking_budget = THINKING_BUDGET_PRO
                log_message(f"Thinking configured for {model_to_use}", "info")
            elif "flash" in model_to_use:
                thinking_budget = THINKING_BUDGET_FLASH
                log_message(f"Thinking configured for {model_to_use}", "info")
        
        image_data = None
        prompt_text = parts[0]["text"]
        if len(parts) > 1 and "inline_data" in parts[1]:
            image_data = parts[1]["inline_data"]["data"]
        
        sdk_response_event = threading.Event()
        sdk_response_container = {'response': None, 'error': None}
        
        def perform_sdk_request_in_thread():
            try:
                resp, err = _make_genai_request(
                    model_to_use, prompt_text, image_data, max_output_tokens, current_api_key, thinking_budget, stop_event
                )
                sdk_response_container['response'] = resp
                sdk_response_container['error'] = err
            except Exception as e_req:
                sdk_response_container['error'] = str(e_req)
            finally:
                sdk_response_event.set()
        
        sdk_thread = threading.Thread(target=perform_sdk_request_in_thread)
        sdk_thread.daemon = True
        sdk_thread.start()
        
        sdk_timeout = 0
        while not sdk_response_event.is_set() and sdk_timeout < API_TIMEOUT:
            if check_stop_event(stop_event, f"SDK request cancelled while waiting for response: {image_basename}"):
                return -2, None, "stopped", "Process stopped while waiting for SDK response"
            sdk_response_event.wait(0.1)
            sdk_timeout += 0.1
        
        if not sdk_response_event.is_set():
            log_message(f"SDK request timed out for {image_basename}, falling back to REST API", "warning")
            log_message(f"Falling back to REST API for {model_to_use}", "info")
        else:
            response = sdk_response_container['response']
            error = sdk_response_container['error']
            
            if error:
                log_message(f"Error with genai SDK for {image_basename}: {error}", "error")
                log_message(f"Falling back to REST API for {model_to_use}", "info")
            else:
                if response and response.text:
                    mock_response_data = {
                        "candidates": [{
                            "content": {
                                "parts": [{"text": response.text}],
                                "role": "model"
                            },
                            "finishReason": "STOP",
                            "index": 0
                        }]
                    }
                    return 200, mock_response_data, None, None
                else:
                    log_message(f"Empty response from genai SDK for {image_basename}", "error")
                    log_message(f"Falling back to REST API for {model_to_use}", "info")
    
    log_message(f"Using REST API fallback for {model_to_use}", "info")
    
    headers = {"Content-Type": "application/json", "User-Agent": "MetadataProcessor/1.0"}
    api_url = f"{api_endpoint}?key={current_api_key}"

    if check_stop_event(stop_event, f"API request dibatalkan sebelum POST: {image_basename}"):
        return -2, None, "stopped", "Process stopped before API POST"

    session = requests.Session()
    session.mount('https://', requests.adapters.HTTPAdapter(
        max_retries=requests.adapters.Retry(total=1, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504], allowed_methods=["POST"], respect_retry_after_header=True)
    ))
    
    response_event = threading.Event()
    response_container = {'response': None, 'error': None}

    def perform_api_request_in_thread():
        try:
            resp = session.post(api_url, headers=headers, json=payload, timeout=API_TIMEOUT, verify=True)
            response_container['response'] = resp
        except Exception as e_req:
            response_container['error'] = e_req
        finally:
            response_event.set()

    api_thread = threading.Thread(target=perform_api_request_in_thread)
    api_thread.daemon = True
    api_thread.start()

    while not response_event.is_set():
        if check_stop_event(stop_event, f"API request cancelled while waiting for response: {image_basename}"):
            return -2, None, "stopped", "Process stopped while waiting for API response"
        response_event.wait(0.1)
    
    if response_container['error']:
        e = response_container['error']
        err_msg = f"RequestException ({type(e).__name__}): {str(e)}"
        log_message(f"Error request API for {image_basename} to {model_to_use}: {err_msg}", "error")
        error_type = "timeout" if isinstance(e, requests.exceptions.Timeout) else "connection_error" if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.SSLError)) else "request_exception"
        return -4, None, error_type, str(e)

    response = response_container['response']
    if response is None:
        log_message(f"Error: Response from API is None without error in container ({image_basename}, {model_to_use}). This should not happen.", "error")
        return -1, None, "internal_null_response", "Response object was None without explicit error."
    
    http_status_code = response.status_code
    try:
        response_data = response.json()
    except json.JSONDecodeError:
        log_message(f"Error: API response is not valid JSON (Status: {http_status_code}) from {model_to_use} for {image_basename}. Response: {response.text[:200]}...", "error")
        return http_status_code, None, "json_decode_error", response.text[:500]

    if http_status_code == 200:
        if "candidates" in response_data and response_data["candidates"]:
            return 200, response_data, None, None 
        elif "promptFeedback" in response_data and response_data.get("promptFeedback", {}).get("blockReason"):
            feedback = response_data["promptFeedback"]
            block_reason = feedback["blockReason"]
            log_message(f"Content blocked by Gemini ({model_to_use}) for {image_basename}. Reason: {block_reason}", "warning")
            return 200, response_data, "blocked", block_reason
        else:
            log_message(f"Success response (200) from {model_to_use} for {image_basename} but no clear 'candidates' or 'blockReason'. Data: {str(response_data)[:200]}...", "warning")
            return 200, response_data, "success_no_candidates_or_block", "No candidates or blockReason in 200 response."
    else:
        error_details = response_data.get("error", {})
        api_error_code = error_details.get("code", "UNKNOWN_API_ERR_CODE")
        api_error_message = error_details.get("message", "No specific error message from API.")
        
        log_message(f"API Error [{model_to_use}] untuk {image_basename}: HTTP {http_status_code}, Code API: {api_error_code} - {api_error_message}", "error")
        return http_status_code, response_data, "api_error", api_error_message

def _extract_metadata_from_text(generated_text: str, keyword_count: str) -> dict | None:
    title = ""
    description = ""
    tags = []
    as_category = ""
    ss_category = ""
    try:
        title_match = re.search(r"^Title:\s*(.*)", generated_text, re.MULTILINE | re.IGNORECASE)
        if title_match: title = title_match.group(1).strip()
        desc_match = re.search(r"^Description:\s*(.*)", generated_text, re.MULTILINE | re.IGNORECASE)
        if desc_match: description = desc_match.group(1).strip()
        keywords_match = re.search(r"^Keywords:\s*(.*)", generated_text, re.MULTILINE | re.IGNORECASE)
        if keywords_match:
            keywords_line = keywords_match.group(1).strip()
            keywords_line = re.split(r"AdobeStockCategory:|ShutterstockCategory:", keywords_line)[0].strip()
            tags = [k.strip() for k in keywords_line.split(",") if k.strip()]
            tags = list(dict.fromkeys(tags))
            try:
                max_kw = int(keyword_count)
                if max_kw < 1: max_kw = 49
            except Exception:
                max_kw = 49
            tags = tags[:max_kw]
        as_cat_match = re.search(r"AdobeStockCategory:\s*([\d]+\.?\s*[^\n]*)", generated_text)
        if as_cat_match:
            as_category = as_cat_match.group(1).strip()
        ss_cat_match = re.search(r"ShutterstockCategory:\s*([^\n]*)", generated_text)
        if ss_cat_match:
            ss_category = ss_cat_match.group(1).strip()
    except Exception as e:
        log_message(f"[ERROR] Failed to parse metadata from Gemini: {e}")
        return None
    return {
        "title": title,
        "description": description,
        "tags": tags,
        "as_category": as_category,
        "ss_category": ss_category
    }

def get_gemini_metadata(image_path, api_key, stop_event, use_png_prompt=False, use_video_prompt=False, selected_model_input=None, keyword_count="49", priority="Detailed", is_vector_conversion=False):
    is_multi_image = isinstance(image_path, list)
    
    if is_multi_image:
        image_basename = f"{os.path.basename(image_path[0])} (+{len(image_path)-1} other frames)"
        log_message(f"Starting get_gemini_metadata for {len(image_path)} video frames with quality: {priority}, model input: {selected_model_input}")
    else:
        image_basename = os.path.basename(image_path)
        log_message(f"Starting get_gemini_metadata for {image_basename} with quality: {priority}, model input: {selected_model_input}")
    
    allowed_api_ext = ('.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif')
    
    if is_multi_image:
        for img in image_path:
            _, ext = os.path.splitext(img)
            if not ext.lower() in allowed_api_ext:
                log_message(f"File type {ext.lower()} not supported for API call ({os.path.basename(img)}).", "warning")
                return None
    else:
        _, ext = os.path.splitext(image_path)
        if not ext.lower() in allowed_api_ext:
            log_message(f"File type {ext.lower()} not supported for API call ({image_basename}).", "warning")
            return None

    if check_stop_event(stop_event, f"get_gemini_metadata cancelled before loop retry: {image_basename}"):
        return "stopped"

    wait_for_api_key_cooldown(api_key, stop_event)
    if check_stop_event(stop_event, f"get_gemini_metadata cancelled after API key cooldown: {image_basename}"):
        return "stopped"

    current_retries = 0
    last_attempted_model = None
    
    model_to_use = DEFAULT_MODEL
    is_auto_rotate_mode = (selected_model_input is None or selected_model_input == "Auto Rotation")

    if not is_auto_rotate_mode:
        if selected_model_input not in GEMINI_MODELS:
            log_message(f"WARNING: Model input '{selected_model_input}' is not valid. Using default: {DEFAULT_MODEL}", "warning")
            model_to_use = DEFAULT_MODEL
        else:
            model_to_use = selected_model_input
            log_message(f"Using fixed model: {model_to_use} (user selected)", "info")
    
    while current_retries < API_MAX_RETRIES:
        if check_stop_event(stop_event, f"get_gemini_metadata loop retry ({current_retries + 1}) cancelled: {image_basename}"):
            return "stopped"

        model_for_this_attempt = model_to_use
        if is_auto_rotate_mode:
            model_for_this_attempt = select_next_model() 
            log_message(f"Auto Rotation: Model selected {model_for_this_attempt} for attempt {current_retries + 1}", "info")
        
        last_attempted_model = model_for_this_attempt

        log_message(f"Attempt {current_retries + 1}/{API_MAX_RETRIES} using model: {model_for_this_attempt}", "info")
        
        http_status, response_data, error_type, error_detail = _attempt_gemini_request(
            image_path, api_key, model_for_this_attempt, stop_event,
            use_png_prompt, use_video_prompt, priority, image_basename, is_vector_conversion
        )
    
        if http_status == 200 and error_type is None:
            if response_data and "candidates" in response_data and response_data["candidates"]:
                candidate = response_data["candidates"][0]
                content = candidate.get("content", {})
                parts = content.get("parts", [])
                
                finish_reason = candidate.get("finishReason", "")
                if finish_reason == "MAX_TOKENS" and len(parts) == 0:
                    log_message(f"Response truncated due to MAX_TOKENS from {model_for_this_attempt} ({image_basename}). Consider increasing maxOutputTokens.", "warning")
                    error_type = "max_tokens_no_content"
                
                generated_text = ""
                if parts:
                    for part in parts:
                        if part.get("text") and not part.get("thought"):
                            generated_text = part.get("text", "")
                            break
                    
                    if not generated_text:
                        text_parts = [part for part in parts if part.get("text")]
                        if text_parts:
                            generated_text = text_parts[-1].get("text", "")
                    
                    if not generated_text:
                        for part in parts:
                            if part.get("text"):
                                generated_text = part.get("text", "")
                                break
                    
                    if not generated_text:
                        log_message(f"Debug: Response parts structure from {model_for_this_attempt}: {[list(part.keys()) for part in parts]}", "debug")
                    else:
                        thinking_parts = [part for part in parts if part.get("thought")]
                        non_thinking_parts = [part for part in parts if part.get("text") and not part.get("thought")]
                
                if generated_text:
                    extracted_metadata = _extract_metadata_from_text(generated_text, keyword_count)
                    
                    if extracted_metadata:
                        log_message(f"Metadata successfully extracted from {model_for_this_attempt} for {image_basename}", "success")
                        return extracted_metadata
                    else:
                        log_message(f"Failed to extract metadata structure (via helper) from Gemini text ({model_for_this_attempt}, {image_basename}).", "warning")
                        error_type = "extraction_failed"
                else:
                    log_message(f"Gemini response structure is invalid (no 'parts'/'text') from {model_for_this_attempt} ({image_basename}).", "warning")
                    error_type = "invalid_response_structure"
            else:
                log_message(f"Success response (200) but no 'candidates' from {model_for_this_attempt} ({image_basename}).", "warning")
                error_type = "success_no_candidates_data"
        
        if error_type == "stopped":
            log_message(f"Processing stopped during API attempt for {image_basename}. Detail: {error_detail}", "warning")
            return "stopped"
        elif error_type == "blocked":
            log_message(f"Content blocked for {image_basename} by {model_for_this_attempt}. Reason: {error_detail}. No retry.", "error")
            return {"error": f"Content blocked by {model_for_this_attempt}: {error_detail}"}
        elif http_status == 429 or (error_type == "api_error" and response_data and response_data.get("error", {}).get("code") == 429):
            log_message(f"Rate limit (429) received for model {model_for_this_attempt} / API key ...{api_key[-4:]} on {image_basename}.", "warning")
            if not is_auto_rotate_mode:
                log_message(f"Warning: The model you selected ({model_for_this_attempt}) is reaching the quota limit. Try using a different model or Auto Rotation mode.", "warning")
        elif http_status in [400, 401, 403] or (error_type == "api_error" and response_data and response_data.get("error",{}).get("code",0) in [400,401,403]):
            err_msg = error_detail if error_detail else "Bad request/Auth error"
            log_message(f"Client error (HTTP {http_status}) for {image_basename} with {model_for_this_attempt}: {err_msg}. No retry.", "error")
            return {"error": f"{err_msg} (HTTP {http_status}, Model {model_for_this_attempt})"}

        current_retries += 1
        if current_retries < API_MAX_RETRIES:
            base_delay = API_RETRY_DELAY * (2 ** (current_retries -1 if current_retries > 0 else 0))
            jitter = random.uniform(0, 0.5 * base_delay)
            actual_delay = base_delay + jitter
            log_message(f"Waiting {actual_delay:.1f} seconds before retry ({current_retries + 1}/{API_MAX_RETRIES}) for {image_basename} (Last model: {model_for_this_attempt}, Error: {error_type or 'N/A'}) ...")
            
            wait_start_time = time.time()
            while time.time() - wait_start_time < actual_delay:
                if check_stop_event(stop_event, f"Retry delay stopped for {image_basename}"):
                    return "stopped"
                time.sleep(0.1)

    if is_auto_rotate_mode and last_attempted_model and http_status == 429:
        log_message(f"Last model '{last_attempted_model}' failed due to rate limit after all retries. No fallback attempt because Auto Rotation is already in use.", "warning")
    
    log_message(f"All attempts ({current_retries}) failed for {image_basename}. Last model tried: {last_attempted_model}", "error")
    return {"error": f"Maximum retries exceeded for {image_basename}. Last model: {last_attempted_model}"}