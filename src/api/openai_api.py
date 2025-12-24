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

# src/api/openai_api.py
from __future__ import annotations

import base64
import json
import os
import threading
import time
from typing import Dict, Iterable, List, Optional, Tuple, Union
import re

import requests

from src.api.prompts import select_prompt
from src.utils.logging import log_message
API_ENDPOINT = "https://api.openai.com/v1/responses"
API_TIMEOUT = 60
API_MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 8
MAX_OUTPUT_TOKENS = None
FORCE_STOP_FLAG = False

OPENAI_MODEL_PRESETS: Dict[str, Dict[str, Optional[Union[str, int, float]]]] = {
    "gpt-5": {
        "api_model": "gpt-5",
        "reasoning_effort": "medium",
        "verbosity": "medium",
        "max_output_tokens": 3072,
    },
    "gpt-5-mini": {
        "api_model": "gpt-5-mini",
        "reasoning_effort": "medium",
        "verbosity": "medium",
        "max_output_tokens": 2048,
    },
    "gpt-5-nano": {
        "api_model": "gpt-5-nano",
        "reasoning_effort": "medium",
        "verbosity": "medium",
        "max_output_tokens": 4096,
    },
    "gpt-5 (low)": {
        "api_model": "gpt-5",
        "reasoning_effort": "low",
        "verbosity": "low",
        "max_output_tokens": 2048,
    },
    "gpt-5-mini (low)": {
        "api_model": "gpt-5-mini",
        "reasoning_effort": "low",
        "verbosity": "low",
        "max_output_tokens": 2048,
    },
    "gpt-5-nano (low)": {
        "api_model": "gpt-5-nano",
        "reasoning_effort": "low",
        "verbosity": "low",
        "max_output_tokens": 2048,
    },
    "gpt-4.1": {
        "api_model": "gpt-4.1",
        "temperature": 0.4,
    },
    "gpt-4.1-mini": {
        "api_model": "gpt-4.1-mini",
        "temperature": 0.3,
    },
    "gpt-4.1-nano": {
        "api_model": "gpt-4.1-nano",
        "temperature": 0.2,
    },
    "gpt-4o": {
        "api_model": "gpt-4o",
        "temperature": 0.2,
    },
    "gpt-4o-mini": {
        "api_model": "gpt-4o-mini",
        "temperature": 0.2,
    },
}

OPENAI_MODELS: List[str] = list(OPENAI_MODEL_PRESETS.keys())
DEFAULT_MODEL = OPENAI_MODELS[0]

_API_KEY_LOCK = threading.Lock()
_API_KEY_INDEX = 0

_STRUCTURED_OUTPUT_MODEL_PREFIXES: Tuple[str, ...] = (
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
)

_WARNED_MODELS_FOR_SCHEMA = set()


def _is_gpt5_model(model: str) -> bool:
    normalized = (model or "").strip()
    return normalized.startswith("gpt-5")


def _model_supports_structured_outputs(model: str) -> bool:
    normalized = (model or "").strip()
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}-")
        for prefix in _STRUCTURED_OUTPUT_MODEL_PREFIXES
    )

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
_JSON_SCHEMA = {
    "name": "metadata_response",
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "maxLength": 200},
            "description": {"type": "string", "maxLength": 200},
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 60,
            },
            "adobe_stock_category": {"type": "string"},
            "shutterstock_category": {"type": "string"},
        },
        "required": [
            "title",
            "description",
            "keywords",
            "adobe_stock_category",
            "shutterstock_category",
        ],
        "additionalProperties": False,
    },
}


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
    log_message("Force stop flag activated for OpenAI provider.", "warning")


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
    if ext.lower() in {".png"}:
        mime_type = "image/png"
    elif ext.lower() in {".webp"}:
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
    reasoning_effort: Optional[str],
    verbosity: Optional[str],
    max_output_tokens: Optional[int],
    temperature: Optional[float],
) -> dict:
    keyword_instruction = (
        "Return 60 single-word keywords; ensure at least 55 are unique. "
        "If you generate more, keep only the top 60 most relevant. No multi-word phrases."
    )
    input_content = [
        {"type": "input_text", "text": f"{prompt_text}\n{keyword_instruction}"}
    ]
    for image_path in images:
        encoded, mime_type = _encode_image(image_path)
        data_url = f"data:{mime_type};base64,{encoded}"
        input_content.append(
            {
                "type": "input_image",
                "image_url": data_url,
            }
        )
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You generate stock photography metadata. Respond strictly "
                            "with JSON matching the provided schema. Do not include "
                            "extra commentary."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": input_content,
            },
        ],
    }
    
    if max_output_tokens:
        payload["max_output_tokens"] = max_output_tokens

    if _is_gpt5_model(model):
        payload["reasoning"] = {"effort": reasoning_effort or "medium"}
    else:
        payload["temperature"] = temperature if temperature is not None else 0.2

    if _model_supports_structured_outputs(model):
        payload["text"] = {
            "format": {
                "type": "json_schema",
                "name": _JSON_SCHEMA["name"],
                "schema": _JSON_SCHEMA["schema"],
                "strict": True,
            }
        }
        if _is_gpt5_model(model) and verbosity:
            payload["text"]["verbosity"] = verbosity
    else:
        if model not in _WARNED_MODELS_FOR_SCHEMA:
            log_message(
                (
                    "OpenAI model %s does not support Responses API JSON schema enforcement; "
                    "falling back to prompt-only formatting."
                )
                % model,
                "warning",
            )
            _WARNED_MODELS_FOR_SCHEMA.add(model)
    return payload


def _extract_metadata_from_json(raw_json: dict, keyword_count: Union[str, int]):
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
    #     log_message(f"[OpenAI] Raw keywords: {len(raw_keywords)}, after dedup/limit: {len(tags)} (limit {keyword_limit})", "debug")
    # except Exception:
    #     pass
    return {
        "title": raw_json.get("title", ""),
        "description": raw_json.get("description", ""),
        "tags": tags,
        "as_category": raw_json.get("adobe_stock_category", ""),
        "ss_category": raw_json.get("shutterstock_category", ""),
    }


def _extract_metadata_from_text_fallback(text_value: str, keyword_count: Union[str, int]):
    if not isinstance(text_value, str) or not text_value.strip():
        return None

    keyword_limit = _normalize_keyword_count(keyword_count)
    title = ""
    description = ""
    tags = []
    as_category = ""
    ss_category = ""

    title_match = re.search(r"^Title:\s*(.*)", text_value, re.MULTILINE | re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
    desc_match = re.search(r"^Description:\s*(.*)", text_value, re.MULTILINE | re.IGNORECASE)
    if desc_match:
        description = desc_match.group(1).strip()
    keywords_match = re.search(r"^Keywords:\s*(.*)", text_value, re.MULTILINE | re.IGNORECASE)
    if keywords_match:
        keywords_line = keywords_match.group(1).strip()
        keywords_line = re.split(r"AdobeStockCategory:|ShutterstockCategory:", keywords_line)[0].strip()
        tags = [k.strip() for k in keywords_line.split(",") if k.strip()]
        tags = list(dict.fromkeys(tags))[:keyword_limit]
    as_cat_match = re.search(r"AdobeStockCategory:\s*([\d]+\.?\s*[^\n]*)", text_value)
    if as_cat_match:
        as_category = as_cat_match.group(1).strip()
    ss_cat_match = re.search(r"ShutterstockCategory:\s*([^\n]*)", text_value)
    if ss_cat_match:
        ss_category = ss_cat_match.group(1).strip()

    if not title and not description and not tags and not as_category and not ss_category:
        return None

    return {
        "title": title,
        "description": description,
        "tags": tags[:keyword_limit],
        "as_category": as_category,
        "ss_category": ss_category,
    }


def _parse_openai_response(response_data: dict, keyword_count: Union[str, int]):
    outputs = response_data.get("output") or []
    observed_types = set()
    text_candidates: List[str] = []
    for output in outputs:
        content = output.get("content") or []
        for item in content:
            item_type = item.get("type")
            if item_type:
                observed_types.add(item_type)

            if item_type in {"text", "output_text"}:
                text_value = item.get("text")
                if isinstance(text_value, str):
                    text_candidates.append(text_value)
                    try:
                        raw_json = json.loads(text_value)
                        if isinstance(raw_json, dict):
                            return _extract_metadata_from_json(raw_json, keyword_count)
                    except (json.JSONDecodeError, TypeError):
                        fallback = _extract_metadata_from_text_fallback(text_value, keyword_count)
                        if fallback:
                            return fallback
                        continue
            elif item_type == "json_schema":
                schema_payload = item.get("json_schema") or {}
                candidates = [
                    schema_payload.get("parsed"),
                    schema_payload.get("content"),
                    schema_payload.get("data"),
                    schema_payload.get("output"),
                ]
                for candidate in candidates:
                    if isinstance(candidate, dict):
                        return _extract_metadata_from_json(candidate, keyword_count)
                    if isinstance(candidate, str):
                        text_candidates.append(candidate)
                        try:
                            raw_json = json.loads(candidate)
                            if isinstance(raw_json, dict):
                                return _extract_metadata_from_json(raw_json, keyword_count)
                        except (json.JSONDecodeError, TypeError):
                            fallback = _extract_metadata_from_text_fallback(candidate, keyword_count)
                            if fallback:
                                return fallback
                            continue
                # Fallback: try common text fields inside schema payload
                for key in ("text", "raw", "string"):
                    maybe_text = schema_payload.get(key)
                    if isinstance(maybe_text, str):
                        text_candidates.append(maybe_text)
                        fallback = _extract_metadata_from_text_fallback(maybe_text, keyword_count)
                        if fallback:
                            return fallback
    # Final fallback: try any collected text candidates (last first)
    for text_value in reversed(text_candidates):
        try:
            raw_json = json.loads(text_value)
            if isinstance(raw_json, dict):
                return _extract_metadata_from_json(raw_json, keyword_count)
        except Exception:
            pass
        fallback = _extract_metadata_from_text_fallback(text_value, keyword_count)
        if fallback:
            return fallback
    if outputs and observed_types:
        log_message(
            "OpenAI response content types not parsed: %s"
            % ", ".join(sorted(observed_types)),
            "warning",
        )
    return None


def _validate_images(images: Iterable[str]) -> Tuple[bool, Optional[str]]:
    for image in images:
        _, ext = os.path.splitext(image)
        if ext.lower() not in _ALLOWED_EXTENSIONS:
            return False, f"File type {ext} not supported for OpenAI: {os.path.basename(image)}"
        if not os.path.exists(image):
            return False, f"Image not found for OpenAI request: {image}"
    return True, None


def get_openai_metadata(
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
        log_message(error_message or "Invalid image for OpenAI request", "warning")
        return {"error": error_message or "unsupported_image_format"}
    if check_stop_event(stop_event, "OpenAI request cancelled before submission"):
        return "stopped"

    model_to_use = (selected_model_input or DEFAULT_MODEL).strip()
    if model_to_use not in OPENAI_MODELS:
        log_message(f"Unknown OpenAI model '{model_to_use}', falling back to {DEFAULT_MODEL}", "warning")
        model_to_use = DEFAULT_MODEL

    model_settings = OPENAI_MODEL_PRESETS.get(model_to_use, {"api_model": model_to_use})
    api_model = model_settings.get("api_model", model_to_use)
    reasoning_effort = model_settings.get("reasoning_effort")
    verbosity = model_settings.get("verbosity")
    temperature = model_settings.get("temperature")
    max_output_tokens = model_settings.get("max_output_tokens")
    if MAX_OUTPUT_TOKENS is not None:
        max_output_tokens = MAX_OUTPUT_TOKENS

    prompt_text = select_prompt(
        priority,
        use_png_prompt=use_png_prompt,
        use_video_prompt=use_video_prompt,
        provider="openai",
    )

    attempt = 0
    while attempt < API_MAX_RETRIES:
        if check_stop_event(stop_event, "OpenAI request cancelled during retries"):
            return "stopped"

        payload = _build_payload(
            images,
            prompt_text,
            keyword_count,
            api_model,
            reasoning_effort,
            verbosity,
            max_output_tokens,
            temperature,
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            log_message(
                f"Sending metadata request to OpenAI model {model_to_use} (key ...{api_key[-5:]})",
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
            log_message(f"OpenAI request failed: {exc}", "error")
            attempt += 1
            if attempt >= API_MAX_RETRIES:
                return {"error": str(exc)}
            sleep_duration = RETRY_DELAY_SECONDS * attempt
            sleep_start = time.time()
            while time.time() - sleep_start < sleep_duration:
                if check_stop_event(stop_event, "OpenAI retry sleep cancelled"):
                    return "stopped"
                time.sleep(0.1)
            continue

        if response.status_code == 200:
            try:
                response_data = response.json()
            except json.JSONDecodeError as exc:
                log_message(f"Failed to decode OpenAI response JSON: {exc}", "error")
                return {"error": "invalid_json"}
            usage_payload = response_data.get("usage") or {}
            output_tokens = usage_payload.get("output_tokens")
            if isinstance(output_tokens, int) and output_tokens > 600:
                log_message(
                    (
                        "OpenAI model %s returned %s output tokens despite schema constraints;"
                        " response may include additional text."
                    )
                    % (model_to_use, output_tokens),
                    "warning",
                )
            metadata = _parse_openai_response(response_data, keyword_count)
            if metadata:
                log_message("Metadata successfully extracted from OpenAI response", "success")
                return metadata
            log_message("OpenAI response did not include usable metadata", "warning")
            return {"error": "empty_response"}

        if response.status_code in {401, 403}:
            log_message("OpenAI authentication error - check API key permissions", "error")
            return {"error": f"Authentication failed ({response.status_code})"}
        if response.status_code == 429:
            if check_stop_event(stop_event):
                return "stopped"
            log_message("OpenAI rate limit hit, backing off before retry", "warning")
            attempt += 1
            sleep_duration = RETRY_DELAY_SECONDS * attempt
            sleep_start = time.time()
            while time.time() - sleep_start < sleep_duration:
                if check_stop_event(stop_event, "OpenAI retry sleep cancelled"):
                    return "stopped"
                time.sleep(0.1)
            continue
        if 500 <= response.status_code < 600:
            if check_stop_event(stop_event):
                return "stopped"
            log_message(f"OpenAI server error {response.status_code}, retrying", "warning")
            attempt += 1
            sleep_duration = RETRY_DELAY_SECONDS * attempt
            sleep_start = time.time()
            while time.time() - sleep_start < sleep_duration:
                if check_stop_event(stop_event, "OpenAI retry sleep cancelled"):
                    return "stopped"
                time.sleep(0.1)
            continue

        try:
            error_payload = response.json()
            error_message = error_payload.get("error", {}).get("message")
        except Exception:
            error_message = response.text[:200]
        log_message(
            f"OpenAI request failed (HTTP {response.status_code}): {error_message}",
            "error",
        )
        return {"error": error_message or f"http_{response.status_code}"}

    return {"error": "openai_max_retries"}


def check_api_keys_status(api_keys: Iterable[str], model: Optional[str] = None) -> dict:
    results = {}
    test_model = (model or DEFAULT_MODEL).strip()
    model_settings = OPENAI_MODEL_PRESETS.get(test_model, {"api_model": test_model})
    api_model = model_settings.get("api_model", test_model)
    payload = {
        "model": api_model,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Test connectivity only. Respond with any JSON matching the schema.",
                    }
                ],
            }
        ],
    }

    if _model_supports_structured_outputs(api_model):
        payload["text"] = {
            "format": {
                "type": "json_schema",
                "name": _JSON_SCHEMA["name"],
                "schema": _JSON_SCHEMA["schema"],
                "strict": True,
            }
        }
        if _is_gpt5_model(api_model):
            verbosity = model_settings.get("verbosity")
            if verbosity:
                payload["text"]["verbosity"] = verbosity

    if _is_gpt5_model(api_model):
        payload["reasoning"] = {"effort": model_settings.get("reasoning_effort", "medium")}
    else:
        payload["temperature"] = model_settings.get("temperature", 0.2)

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
