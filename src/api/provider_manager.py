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

# src/api/provider_manager.py
from __future__ import annotations

from typing import Iterable, List, Optional
import re

from src.api import gemini_api, openai_api, openrouter_api, groq_api
from src.utils.logging import log_message

PROVIDER_GEMINI = "Gemini"
PROVIDER_OPENAI = "OpenAI"
PROVIDER_OPENROUTER = "OpenRouter"
PROVIDER_GROQ = "Groq"
_DEFAULT_PROVIDER = PROVIDER_GEMINI

_PROVIDERS = {
    PROVIDER_GEMINI: {
        "module": gemini_api,
        "models": list(gemini_api.GEMINI_MODELS),
        "supports_auto_rotation": False,
        "default_model": gemini_api.DEFAULT_MODEL,
    },
    PROVIDER_OPENAI: {
        "module": openai_api,
        "models": list(openai_api.OPENAI_MODELS),
        "supports_auto_rotation": False,
        "default_model": openai_api.DEFAULT_MODEL,
    },
    PROVIDER_OPENROUTER: {
        "module": openrouter_api,
        "models": list(openrouter_api.OPENROUTER_MODELS),
        "supports_auto_rotation": False,
        "default_model": openrouter_api.DEFAULT_MODEL,
    },
    PROVIDER_GROQ: {
        "module": groq_api,
        "models": list(groq_api.GROQ_MODELS),
        "supports_auto_rotation": False,
        "default_model": groq_api.DEFAULT_MODEL,
    },
}


def list_providers() -> List[str]:
    return list(_PROVIDERS.keys())


def get_default_provider() -> str:
    return _DEFAULT_PROVIDER


def get_provider_module(provider: str):
    provider_key = provider if provider in _PROVIDERS else _DEFAULT_PROVIDER
    return _PROVIDERS[provider_key]["module"], provider_key


def get_model_choices(provider: str) -> List[str]:
    module, provider_key = get_provider_module(provider)
    provider_config = _PROVIDERS[provider_key]
    models = provider_config["models"]
    if provider_config.get("supports_auto_rotation"):
        return ["Auto Rotation"] + models
    return models


def get_default_model(provider: str) -> str:
    _, provider_key = get_provider_module(provider)
    return _PROVIDERS[provider_key]["default_model"]


def supports_auto_rotation(provider: str) -> bool:
    _, provider_key = get_provider_module(provider)
    return bool(_PROVIDERS[provider_key].get("supports_auto_rotation", False))


def select_api_key(provider: str, api_keys: Iterable[str]):
    module, provider_key = get_provider_module(provider)
    if provider_key == PROVIDER_GEMINI:
        return module.select_smart_api_key(list(api_keys))
    return module.select_api_key(list(api_keys))


def get_metadata(
    provider: str,
    image_path,
    api_key: str,
    stop_event,
    use_png_prompt: bool = False,
    use_video_prompt: bool = False,
    selected_model: Optional[str] = None,
    keyword_count: str = "49",
    priority: str = "Detailed",
    is_vector_conversion: bool = False,
):
    module, provider_key = get_provider_module(provider)

    def _fill_keywords_if_short(metadata: dict, keyword_count_value: str):
        try:
            limit = int(keyword_count_value)
            if limit < 1:
                limit = 49
            if limit > 100:
                limit = limit
        except Exception:
            limit = 49

        raw_tags = metadata.get("tags") or []
        title = metadata.get("title", "") or ""
        description = metadata.get("description", "") or ""

        seen = set()
        final_tags: List[str] = []

        def add_tag(tag_value):
            tag_text = str(tag_value).strip()
            if not tag_text:
                return
            tag_text = re.sub(r"[^\w\-]", " ", tag_text)
            tag_text = re.sub(r"\s+", " ", tag_text).strip()
            if not tag_text:
                return
            if " " in tag_text:
                tag_text = tag_text.replace(" ", "")
                if not tag_text:
                    return
            lower = tag_text.lower()
            if lower in seen:
                return
            seen.add(lower)
            final_tags.append(tag_text)

        for tag in raw_tags:
            add_tag(tag)

        if len(final_tags) >= limit:
            metadata["tags"] = final_tags[:limit]
            return metadata

        filler_words: List[str] = []

        def collect_words(text: str):
            for word in re.split(r"[^A-Za-z0-9]+", text or ""):
                if len(word) >= 3:
                    filler_words.append(word)

        collect_words(title)
        collect_words(description)

        for word in filler_words:
            if len(final_tags) >= limit:
                break
            add_tag(word)

        metadata["tags"] = final_tags[:limit]
        return metadata
    effective_model = selected_model
    if provider_key == PROVIDER_GEMINI:
        if selected_model in (None, "", "Auto Rotation"):
            effective_model = None
        result = module.get_gemini_metadata(
            image_path,
            api_key,
            stop_event,
            use_png_prompt=use_png_prompt,
            use_video_prompt=use_video_prompt,
            selected_model_input=effective_model,
            keyword_count=keyword_count,
            priority=priority,
            is_vector_conversion=is_vector_conversion,
        )
        if isinstance(result, dict) and "error" not in result:
            return _fill_keywords_if_short(result, keyword_count)
        return result
    if provider_key == PROVIDER_OPENROUTER:
        result = module.get_openrouter_metadata(
            image_path,
            api_key,
            stop_event,
            use_png_prompt=use_png_prompt,
            use_video_prompt=use_video_prompt,
            selected_model_input=effective_model,
            keyword_count=keyword_count,
            priority=priority,
            is_vector_conversion=is_vector_conversion,
        )
        if isinstance(result, dict) and "error" not in result:
            return _fill_keywords_if_short(result, keyword_count)
        return result
    if provider_key == PROVIDER_GROQ:
        result = module.get_groq_metadata(
            image_path,
            api_key,
            stop_event,
            use_png_prompt=use_png_prompt,
            use_video_prompt=use_video_prompt,
            selected_model_input=effective_model,
            keyword_count=keyword_count,
            priority=priority,
            is_vector_conversion=is_vector_conversion,
        )
        if isinstance(result, dict) and "error" not in result:
            return _fill_keywords_if_short(result, keyword_count)
        return result
    result = module.get_openai_metadata(
        image_path,
        api_key,
        stop_event,
        use_png_prompt=use_png_prompt,
        use_video_prompt=use_video_prompt,
        selected_model_input=effective_model,
        keyword_count=keyword_count,
        priority=priority,
        is_vector_conversion=is_vector_conversion,
    )
    if isinstance(result, dict) and "error" not in result:
        return _fill_keywords_if_short(result, keyword_count)
    return result


def check_api_keys_status(provider: str, api_keys: Iterable[str], model: Optional[str] = None):
    module, _ = get_provider_module(provider)
    return module.check_api_keys_status(list(api_keys), model=model)


def set_force_stop(provider: Optional[str] = None) -> None:
    if provider is None:
        for provider_name in list_providers():
            module, _ = get_provider_module(provider_name)
            if hasattr(module, "set_force_stop"):
                module.set_force_stop()
        return
    module, _ = get_provider_module(provider)
    if hasattr(module, "set_force_stop"):
        module.set_force_stop()


def reset_force_stop(provider: Optional[str] = None) -> None:
    if provider is None:
        for provider_name in list_providers():
            module, _ = get_provider_module(provider_name)
            if hasattr(module, "reset_force_stop"):
                module.reset_force_stop()
        return
    module, _ = get_provider_module(provider)
    if hasattr(module, "reset_force_stop"):
        module.reset_force_stop()


def is_stop_requested(provider: Optional[str] = None) -> bool:
    if provider is None:
        return any(is_stop_requested(name) for name in list_providers())
    module, _ = get_provider_module(provider)
    if hasattr(module, "is_stop_requested"):
        return module.is_stop_requested()
    return False


def check_stop_event(provider: str, stop_event, message: Optional[str] = None) -> bool:
    module, _ = get_provider_module(provider)
    if hasattr(module, "check_stop_event"):
        return module.check_stop_event(stop_event, message)
    if stop_event is not None:
        try:
            if stop_event.is_set():
                if message:
                    log_message(message)
                return True
        except Exception:
            return False
    return False
