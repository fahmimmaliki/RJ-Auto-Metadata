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

# src/api/groq_api.py
from __future__ import annotations

import base64
import json
import os
import threading
import time
from typing import Dict, Iterable, List, Optional, Tuple, Union

import requests

from src.api.prompts import select_prompt
from src.utils.logging import log_message

API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
API_TIMEOUT = 60
API_MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 8
MAX_OUTPUT_TOKENS: Optional[int] = None
FORCE_STOP_FLAG = False

GROQ_MODEL_PRESETS: Dict[str, Dict[str, Optional[Union[str, int, float]]]] = {
    "Llama 4 Scout": {
        "api_model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "temperature": 0.5,
        "max_output_tokens": 4096,
        "description": "Llama 4 Scout (Vision capable)",
    },
    "Llama 4 Maverick": {
        "api_model": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "temperature": 0.5,
        "max_output_tokens": 4096,
        "description": "Llama 4 Maverick (Vision capable)",
    },
}

GROQ_MODELS: List[str] = list(GROQ_MODEL_PRESETS.keys())
DEFAULT_MODEL = "Llama 4 Maverick"

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
_API_KEY_LOCK = threading.Lock()
_API_KEY_INDEX = 0


def _normalize_keyword_count(keyword_count: Union[str, int]) -> int:
    try:
        value = int(keyword_count)
        if value <= 0:
            return 10
        return min(value, 60)
    except Exception:
        return 49


def select_api_key(api_keys: Iterable[str]) -> Optional[str]:
    keys = list(api_keys) if not isinstance(api_keys, list) else api_keys
    if not keys:
        return None
    global _API_KEY_INDEX
    with _API_KEY_LOCK:
        key = keys[_API_KEY_INDEX % len(keys)]
        _API_KEY_INDEX = (_API_KEY_INDEX + 1) % len(keys)
        return key


def is_stop_requested() -> bool:
    return FORCE_STOP_FLAG


def set_force_stop() -> None:
    global FORCE_STOP_FLAG
    FORCE_STOP_FLAG = True
    log_message("Force stop flag activated for Groq provider.", "warning")


def reset_force_stop() -> None:
    global FORCE_STOP_FLAG
    FORCE_STOP_FLAG = False


def check_stop_event(stop_event, message: Optional[str] = None) -> bool:
    if is_stop_requested():
        if message:
            log_message(message)
        return True
    if stop_event is None:
        return False
    try:
        is_set = stop_event.is_set()
        if is_set and message:
            log_message(message)
        return is_set
    except Exception as exc:
        log_message(f"Failed to inspect stop_event: {exc}")
    return False


def _encode_image(path: str) -> Tuple[str, str]:
    _, ext = os.path.splitext(path)
    mime_type = "image/jpeg"
    if ext.lower() == ".png":
        mime_type = "image/png"
    elif ext.lower() == ".webp":
        mime_type = "image/webp"
    elif ext.lower() in {".heic", ".heif"}:
        mime_type = "image/heic"
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded, mime_type


def _build_payload(
    images: List[str],
    prompt_text: str,
    keyword_count: Union[str, int],
    model: str,
    max_output_tokens: Optional[int],
    temperature: Optional[float],
) -> dict:
    system_instruction = (
        "You generate stock photography metadata. Respond strictly with JSON that "
        "includes the keys 'title', 'description', 'keywords', 'adobe_stock_category', "
        "and 'shutterstock_category'. Limit text fields to 200 characters and keep the "
        "keywords array relevant. Do not include extra commentary."
    )

    user_content: List[dict] = []
    if prompt_text:
        user_content.append(
            {
                "type": "text",
                "text": (
                    f"{prompt_text}\n"
                    "Return 60 single-word keywords; ensure at least 55 are unique. "
                    "If you generate more, keep the top 60 most relevant. No multi-word phrases."
                ),
            }
        )

    for image_path in images:
        encoded, mime_type = _encode_image(image_path)
        data_url = f"data:{mime_type};base64,{encoded}"
        user_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": data_url,
                },
            }
        )

    messages: List[dict] = [
        {"role": "system", "content": system_instruction},
    ]

    if user_content:
        messages.append({"role": "user", "content": user_content})

    payload = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }

    if max_output_tokens:
        payload["max_completion_tokens"] = max_output_tokens

    if temperature is not None:
        payload["temperature"] = temperature
    else:
        payload["temperature"] = 0.5

    return payload


def _extract_metadata_from_json(raw_json: dict, keyword_count: Union[str, int]) -> dict:
    keyword_limit = 60
    keywords = raw_json.get("keywords") or []
    raw_keywords: List[str] = []
    if isinstance(keywords, list):
        raw_keywords = [str(item).strip() for item in keywords if str(item).strip()]
        tags = list(raw_keywords)
    elif isinstance(keywords, str):
        raw_keywords = [part.strip() for part in keywords.split(",") if part.strip()]
        tags = list(raw_keywords)
    else:
        tags = []
    tags = list(dict.fromkeys(tags))[:keyword_limit]
    # try:
    #     log_message(f"[Groq] Raw keywords: {len(raw_keywords)}, after dedup/limit: {len(tags)} (limit {keyword_limit})", "debug")
    # except Exception:
    #     pass
    return {
        "title": raw_json.get("title", ""),
        "description": raw_json.get("description", ""),
        "tags": tags,
        "as_category": raw_json.get("adobe_stock_category", ""),
        "ss_category": raw_json.get("shutterstock_category", ""),
    }


def _parse_groq_response(response_data: dict, keyword_count: Union[str, int]) -> Optional[dict]:
    choices = response_data.get("choices") or []
    
    for choice in choices:
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            try:
                raw_json = json.loads(content)
                if isinstance(raw_json, dict):
                    return _extract_metadata_from_json(raw_json, keyword_count)
            except (json.JSONDecodeError, TypeError):
                continue
    return None


def _validate_images(images: Iterable[str]) -> Tuple[bool, Optional[str]]:
    for image in images:
        _, ext = os.path.splitext(image)
        if ext.lower() not in _ALLOWED_EXTENSIONS:
            return False, f"File type {ext} not supported for Groq: {os.path.basename(image)}"
        if not os.path.exists(image):
            return False, f"Image not found for Groq request: {image}"
    return True, None


def get_groq_metadata(
    image_path: Union[str, List[str]],
    api_key: str,
    stop_event,
    use_png_prompt: bool = False,
    use_video_prompt: bool = False,
    selected_model_input: Optional[str] = None,
    keyword_count: Union[str, int] = "49",
    priority: str = "Detailed",
    is_vector_conversion: bool = False,
):
    images: List[str] = image_path if isinstance(image_path, list) else [image_path]
    is_valid, error_message = _validate_images(images)
    if not is_valid:
        log_message(error_message or "Invalid image for Groq request", "warning")
        return {"error": error_message or "unsupported_image_format"}

    if check_stop_event(stop_event, "Groq request cancelled before submission"):
        return "stopped"

    model_to_use = (selected_model_input or DEFAULT_MODEL).strip()
    if model_to_use not in GROQ_MODELS:
        log_message(
            f"Unknown Groq model '{model_to_use}', falling back to {DEFAULT_MODEL}",
            "warning",
        )
        model_to_use = DEFAULT_MODEL

    model_settings = GROQ_MODEL_PRESETS.get(model_to_use, {"api_model": model_to_use})
    api_model = model_settings.get("api_model", model_to_use)
    temperature = model_settings.get("temperature")
    max_output_tokens = model_settings.get("max_output_tokens")
    if MAX_OUTPUT_TOKENS is not None:
        max_output_tokens = MAX_OUTPUT_TOKENS

    prompt_text = select_prompt(
        priority,
        use_png_prompt=use_png_prompt,
        use_video_prompt=use_video_prompt,
        provider="groq",
    )

    attempt = 0
    while attempt < API_MAX_RETRIES:
        if check_stop_event(stop_event, "Groq request cancelled during retries"):
            return "stopped"

        payload = _build_payload(
            images,
            prompt_text,
            keyword_count,
            api_model,
            max_output_tokens,
            temperature,
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            log_message(
                f"Sending metadata request to Groq model {model_to_use} (key ...{api_key[-5:]})",
                "info",
            )
            response = requests.post(
                API_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=API_TIMEOUT,
            )
        except requests.RequestException as exc:
            if check_stop_event(stop_event):
                return "stopped"
            log_message(f"Groq request failed: {exc}", "error")
            attempt += 1
            if attempt >= API_MAX_RETRIES:
                return {"error": str(exc)}
            sleep_duration = RETRY_DELAY_SECONDS * attempt
            sleep_start = time.time()
            while time.time() - sleep_start < sleep_duration:
                if check_stop_event(stop_event, "Groq retry sleep cancelled"):
                    return "stopped"
                time.sleep(0.1)
            continue

        if response.status_code == 200:
            try:
                response_data = response.json()
            except json.JSONDecodeError as exc:
                log_message(f"Failed to decode Groq response JSON: {exc}", "error")
                return {"error": "invalid_json"}

            metadata = _parse_groq_response(response_data, keyword_count)
            if metadata:
                log_message("Metadata successfully extracted from Groq response", "success")
                return metadata

            log_message("Groq response did not include usable metadata", "warning")
            return {"error": "empty_response"}

        if response.status_code in {401, 403}:
            log_message("Groq authentication error - check API key permissions", "error")
            return {"error": f"Authentication failed ({response.status_code})"}

        if response.status_code == 429:
            if check_stop_event(stop_event):
                return "stopped"
            log_message("Groq rate limit hit, backing off before retry", "warning")
            attempt += 1
            sleep_duration = RETRY_DELAY_SECONDS * attempt
            sleep_start = time.time()
            while time.time() - sleep_start < sleep_duration:
                if check_stop_event(stop_event, "Groq retry sleep cancelled"):
                    return "stopped"
                time.sleep(0.1)
            continue

        if 500 <= response.status_code < 600:
            if check_stop_event(stop_event):
                return "stopped"
            log_message(f"Groq server error {response.status_code}, retrying", "warning")
            attempt += 1
            sleep_duration = RETRY_DELAY_SECONDS * attempt
            sleep_start = time.time()
            while time.time() - sleep_start < sleep_duration:
                if check_stop_event(stop_event, "Groq retry sleep cancelled"):
                    return "stopped"
                time.sleep(0.1)
            continue

        try:
            error_payload = response.json()
            error_block = error_payload.get("error") if isinstance(error_payload, dict) else None
            error_message = None
            if isinstance(error_block, dict):
                error_message = error_block.get("message") or error_block.get("code")
        except Exception:
            error_message = response.text[:200]
        else:
            if not error_message:
                fallback_text = response.text.strip()
                if fallback_text:
                    error_message = fallback_text[:200]

        log_message(
            f"Groq request failed (HTTP {response.status_code}): {error_message}",
            "error",
        )
        return {"error": error_message or f"http_{response.status_code}"}

    return {"error": "groq_max_retries"}


def check_api_keys_status(api_keys: Iterable[str], model: Optional[str] = None) -> dict:
    results: Dict[str, Tuple[int, str]] = {}
    test_model = (model or DEFAULT_MODEL).strip()
    model_settings = GROQ_MODEL_PRESETS.get(test_model, {"api_model": test_model})
    api_model = model_settings.get("api_model", test_model)

    payload = {
        "model": api_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You generate stock photography metadata. Respond with a JSON object"
                    " containing the required keys."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Test connectivity only. Respond with any JSON matching the schema.",
                    }
                ],
            },
        ],
        "response_format": {"type": "json_object"},
    }

    if model_settings.get("temperature") is not None:
        payload["temperature"] = model_settings.get("temperature")
    else:
        payload["temperature"] = 0.5

    if model_settings.get("max_output_tokens"):
        payload["max_completion_tokens"] = model_settings["max_output_tokens"]

    for key in api_keys:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                API_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=20,
            )
            if response.status_code == 200:
                results[key] = (200, "OK")
            else:
                try:
                    error_payload = response.json()
                    status_message = error_payload.get("error", {}).get("message", "Unknown error")
                except Exception:
                    status_message = response.text[:120]
                results[key] = (response.status_code, status_message)
        except Exception as exc:
            results[key] = (-1, str(exc)[:120])

    return results
