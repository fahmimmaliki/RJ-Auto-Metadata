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

# src/api/prompts.py
PROMPT_TEXT = '''Analyze image, generate JSON metadata:
{"title": ["minimum 6 words, max 180 chars, descriptive, unique, dont use special characters"], "description": ["detailed, max 180 chars, unique, dont use special characters"], "keywords": ["Give me 60 unique keywords, ensure at least 55 unique; if fewer are obvious, add closely-related synonyms/variations. No multi-word phrases. Array"], "adobe_stock_category": ["pick number and name: 1.Animals, 2.Architecture, 3.Business, 4.Drinks, 5.Environment, 6.Mind, 7.Food, 8.Graphics, 9.Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants, 15.Religion, 16.Science, 17.Social, 18.Sports, 19.Technology, 20.Transport, 21.Travel"], "shutterstock_category": ["pick: 'Abstract', 'Animals/Wildlife', 'Arts', 'Backgrounds/Textures', 'Beauty/Fashion', 'Buildings/Landmarks', 'Business/Finance', 'Education', 'Food and drink', 'Healthcare/Medical', 'Industrial', 'Nature', 'Objects', 'People', 'Religion', 'Science', 'Signs/Symbols', 'Sports/Recreaction', 'Technology', 'Transportation'"]}'''

PROMPT_TEXT_PNG = '''Analyze main subject only (ignore background), generate JSON:
{"title": ["focused on main subject, minimum 6 words, max 180 chars, unique, dont use special characters"], "description": ["focused on main subject details only, max 180 chars, unique, dont use special characters"], "keywords": ["Give me 60 unique keywords, ensure at least 55 unique; if fewer are obvious, add closely-related synonyms/variations. No multi-word phrases. Array"], "adobe_stock_category": ["pick number and name: 1.Animals, 2.Architecture, 3.Business, 4.Drinks, 5.Environment, 6.Mind, 7.Food, 8.Graphics, 9.Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants, 15.Religion, 16.Science, 17.Social, 18.Sports, 19.Technology, 20.Transport, 21.Travel"], "shutterstock_category": ["pick: 'Abstract', 'Animals/Wildlife', 'Arts', 'Backgrounds/Textures', 'Beauty/Fashion', 'Buildings/Landmarks', 'Business/Finance', 'Education', 'Food and drink', 'Healthcare/Medical', 'Industrial', 'Nature', 'Objects', 'People', 'Religion', 'Science', 'Signs/Symbols', 'Sports/Recreaction', 'Technology', 'Transportation'"]}'''

PROMPT_TEXT_VIDEO = '''
Analyze these video frames comprehensively and generate detailed JSON video metadata:
{"title": ["video title, minimum 6 words, max 180 chars, unique, dont use special characters"], "description": ["video description, max 180 chars, unique, dont use special characters"], "keywords": ["Give me 60 unique keywords, ensure at least 55 unique; if fewer are obvious, add closely-related synonyms/variations. No multi-word phrases. Array"], "adobe_stock_category": ["pick number and name: 1.Animals, 2.Architecture, 3.Business, 4.Drinks, 5.Environment, 6.Mind, 7.Food, 8.Graphics, 9.Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants, 15.Religion, 16.Science, 17.Social, 18.Sports, 19.Technology, 20.Transport, 21.Travel"], "shutterstock_category": ["pick one: 'Animals/Wildlife', 'Arts', 'Backgrounds/Textures', 'Buildings/Landmarks', 'Business/Finance', 'Education', 'Food and drink', 'Healthcare/Medical', 'Holidays', 'Industrial', 'Nature', 'Objects', 'People', 'Religion', 'Science', 'Signs/Symbols', 'Sports/Recreaction', 'Technology', 'Transportation'"]}
'''



PROMPT_TEXT_BALANCED = '''Generate balanced JSON metadata:
{"title": ["focused, minimum 5 words, max 165 chars, unique, dont use special characters"], "description": ["clear info, max 165 chars, unique, dont use special characters"], "keywords": ["Give me 60 unique keywords, ensure at least 55 unique; if fewer are obvious, add closely-related synonyms/variations. No multi-word phrases. Array"], "adobe_stock_category": ["pick number and name: 1.Animals, 2.Architecture, 3.Business, 4.Drinks, 5.Environment, 6.Mind, 7.Food, 8.Graphics, 9.Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants, 15.Religion, 16.Science, 17.Social, 18.Sports, 19.Technology, 20.Transport, 21.Travel"], "shutterstock_category": ["pick: 'Abstract', 'Animals/Wildlife', 'Arts', 'Backgrounds/Textures', 'Beauty/Fashion', 'Buildings/Landmarks', 'Business/Finance', 'Education', 'Food and drink', 'Healthcare/Medical', 'Industrial', 'Nature', 'Objects', 'People', 'Religion', 'Science', 'Signs/Symbols', 'Sports/Recreaction', 'Technology', 'Transportation'"]}'''

PROMPT_TEXT_PNG_BALANCED = '''
Generate balanced JSON metadata:
{"title": ["focused on main subject, minimum 5 words, max 165 chars, unique, dont use special characters"], "description": ["clear info, main subject only, max 165 chars, unique, dont use special characters"], "keywords": ["Give me 60 unique keywords, ensure at least 55 unique; if fewer are obvious, add closely-related synonyms/variations. No multi-word phrases. Array"], "adobe_stock_category": ["pick number and name: 1.Animals, 2.Architecture, 3.Business, 4.Drinks, 5.Environment, 6.Mind, 7.Food, 8.Graphics, 9.Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants, 15.Religion, 16.Science, 17.Social, 18.Sports, 19.Technology, 20.Transport, 21.Travel"], "shutterstock_category": ["pick: 'Abstract', 'Animals/Wildlife', 'Arts', 'Backgrounds/Textures', 'Beauty/Fashion', 'Buildings/Landmarks', 'Business/Finance', 'Education', 'Food and drink', 'Healthcare/Medical', 'Industrial', 'Nature', 'Objects', 'People', 'Religion', 'Science', 'Signs/Symbols', 'Sports/Recreaction', 'Technology', 'Transportation'"]}
'''

PROMPT_TEXT_VIDEO_BALANCED = '''
Generate balanced JSON metadata:
{"title": ["video title, minimum 5 words, max 165 chars, unique, dont use special characters"], "description": ["video description, max 165 chars, unique, dont use special characters"], "keywords": ["Give me 60 unique keywords, ensure at least 55 unique; if fewer are obvious, add closely-related synonyms/variations. No multi-word phrases. Array"], "adobe_stock_category": ["pick number and name: 1.Animals, 2.Architecture, 3.Business, 4.Drinks, 5.Environment, 6.Mind, 7.Food, 8.Graphics, 9.Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants, 15.Religion, 16.Science, 17.Social, 18.Sports, 19.Technology, 20.Transport, 21.Travel"], "shutterstock_category": ["pick one: 'Animals/Wildlife', 'Arts', 'Backgrounds/Textures', 'Buildings/Landmarks', 'Business/Finance', 'Education', 'Food and drink', 'Healthcare/Medical', 'Holidays', 'Industrial', 'Nature', 'Objects', 'People', 'Religion', 'Science', 'Signs/Symbols', 'Sports/Recreaction', 'Technology', 'Transportation'"]}
'''



PROMPT_TEXT_FAST = '''Quick JSON: {"title": ["minimum 4 words, max 150 chars, unique, dont use special characters"], "description":["brief, max 150 chars, unique, dont use special characters"], "keywords":["Give me 60 unique keywords, ensure at least 55 unique; if fewer are obvious, add closely-related synonyms/variations. No multi-word phrases. Array"], "adobe_stock_category": ["pick number and name: 1.Animals, 2.Architecture, 3.Business, 4.Drinks, 5.Environment, 6.Mind, 7.Food, 8.Graphics, 9.Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants, 15.Religion, 16.Science, 17.Social, 18.Sports, 19.Technology, 20.Transport, 21.Travel"], "shutterstock_category": ["pick one: 'Abstract', 'Animals/Wildlife', 'Arts', 'Backgrounds/Textures', 'Beauty/Fashion', 'Buildings/Landmarks', 'Business/Finance', 'Education', 'Food and drink', 'Healthcare/Medical', 'Industrial', 'Nature', 'Objects', 'People', 'Religion', 'Science', 'Signs/Symbols', 'Sports/Recreaction', 'Technology', 'Transportation'"]}'''

PROMPT_TEXT_PNG_FAST = '''Subject JSON: {"title": ["main subject, minimum 4 words, max 150 chars, unique, dont use special characters"], "description":["subject details only, max 150 chars, unique, dont use special characters"], "keywords":["Give me 60 unique keywords, ensure at least 55 unique; if fewer are obvious, add closely-related synonyms/variations. No multi-word phrases. Array"], "adobe_stock_category": ["pick number and name: 1.Animals, 2.Architecture, 3.Business, 4.Drinks, 5.Environment, 6.Mind, 7.Food, 8.Graphics, 9.Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants, 15.Religion, 16.Science, 17.Social, 18.Sports, 19.Technology, 20.Transport, 21.Travel"], "shutterstock_category": ["pick: 'Abstract', 'Animals/Wildlife', 'Arts', 'Backgrounds/Textures', 'Beauty/Fashion', 'Buildings/Landmarks', 'Business/Finance', 'Education', 'Food and drink', 'Healthcare/Medical', 'Industrial', 'Nature', 'Objects', 'People', 'Religion', 'Science', 'Signs/Symbols', 'Sports/Recreaction', 'Technology', 'Transportation'"]}'''

PROMPT_TEXT_VIDEO_FAST = '''Video JSON: {"title": ["video action, minimum 4 words, max 150 chars, unique, dont use special characters"], "description":["video summary, max 150 chars, unique, dont use special characters"], "keywords":["Give me 60 unique keywords, ensure at least 55 unique; if fewer are obvious, add closely-related synonyms/variations. No multi-word phrases. Array"], "adobe_stock_category": ["pick number and name: 1.Animals, 2.Architecture, 3.Business, 4.Drinks, 5.Environment, 6.Mind, 7.Food, 8.Graphics, 9.Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants, 15.Religion, 16.Science, 17.Social, 18.Sports, 19.Technology, 20.Transport, 21.Travel"], "shutterstock_category": ["pick one: 'Animals/Wildlife', 'Arts', 'Backgrounds/Textures', 'Buildings/Landmarks', 'Business/Finance', 'Education', 'Food and drink', 'Healthcare/Medical', 'Holidays', 'Industrial', 'Nature', 'Objects', 'People', 'Religion', 'Science', 'Signs/Symbols', 'Sports/Recreaction', 'Technology', 'Transportation'"]}''' 

_ADOBE_STOCK_CATEGORY_LIST = (
    "1.Animals, 2.Architecture, 3.Business, 4.Drinks, 5.Environment, 6.Mind, 7.Food, 8.Graphics, 9.Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants, 15.Religion, 16.Science, 17.Social, 18.Sports, 19.Technology, 20.Transport, 21.Travel"
)

_SHUTTERSTOCK_CATEGORY_LIST_IMAGE = (
    "'Abstract', 'Animals/Wildlife', 'Arts', 'Backgrounds/Textures', 'Beauty/Fashion', 'Buildings/Landmarks', 'Business/Finance', 'Education', 'Food and drink', 'Healthcare/Medical', 'Industrial', 'Nature', 'Objects', 'People', 'Religion', 'Science', 'Signs/Symbols', 'Sports/Recreaction', 'Technology', 'Transportation'"
)

_SHUTTERSTOCK_CATEGORY_LIST_VIDEO = (
    "'Animals/Wildlife', 'Arts', 'Backgrounds/Textures', 'Buildings/Landmarks', 'Business/Finance', 'Education', 'Food and drink', 'Healthcare/Medical', 'Holidays', 'Industrial', 'Nature', 'Objects', 'People', 'Religion', 'Science', 'Signs/Symbols', 'Sports/Recreaction', 'Technology', 'Transportation'"
)

_OPENAI_JSON_TEMPLATE = '{"title": "", "description": "", "keywords": [], "adobe_stock_category": "", "shutterstock_category": ""}'


def _build_openai_prompt(
    intro: str,
    title_rule: str,
    description_rule: str,
    keyword_rule: str,
    is_video: bool = False,
) -> str:
    shutterstock_list = (
        _SHUTTERSTOCK_CATEGORY_LIST_VIDEO
        if is_video
        else _SHUTTERSTOCK_CATEGORY_LIST_IMAGE
    )
    return (
        "You are a stock photography metadata generator. "
        f"{intro}\n\n"
        "Output requirements:\n"
        f"- Title: {title_rule}.\n"
        f"- Description: {description_rule}.\n"
        f"- Keywords: {keyword_rule}.\n"
        f"- Adobe Stock category: choose the number and name from: {_ADOBE_STOCK_CATEGORY_LIST}.\n"
        f"- Shutterstock category: choose one from: {shutterstock_list}.\n\n"
        "Return ONLY valid JSON matching this schema exactly (no extra text, comments, or markdown):\n"
        f"{_OPENAI_JSON_TEMPLATE}"
    )


OPENAI_PROMPT_TEXT = _build_openai_prompt(
    intro="Analyze the entire image and produce production-ready metadata.",
    title_rule="Minimum 6 words, maximum 180 characters, descriptive, unique, and avoid special characters",
    description_rule="Minimum 6 words, maximum 180 characters, detailed, unique, and avoid special characters",
    keyword_rule="Provide up to 60 unique keywords; ensure at least 55 unique. If fewer are obvious, add closely-related synonyms/variations. No multi-word phrases.",
)

OPENAI_PROMPT_TEXT_PNG = _build_openai_prompt(
    intro="Focus only on the main subject of the image (ignore the background) when generating metadata.",
    title_rule="Minimum 6 words, maximum 180 characters, describe the main subject only, unique, no special characters",
    description_rule="Minimum 6 words, maximum 180 characters, capture only the main subject details, unique, no special characters",
    keyword_rule="Provide up to 60 unique keywords that describe the main subject only; ensure at least 55 unique. If fewer are obvious, add closely-related synonyms/variations. No multi-word phrases.",
)

OPENAI_PROMPT_TEXT_VIDEO = _build_openai_prompt(
    intro="Analyze all video frames comprehensively and generate detailed video metadata.",
    title_rule="Minimum 6 words, maximum 180 characters, describe the video content, unique, no special characters",
    description_rule="Minimum 6 words, maximum 180 characters, summarize the video clearly, unique, no special characters",
    keyword_rule="Provide up to 60 unique keywords covering the entire video content; ensure at least 55 unique. If fewer are obvious, add closely-related synonyms/variations. No multi-word phrases.",
    is_video=True,
)

OPENAI_PROMPT_TEXT_BALANCED = _build_openai_prompt(
    intro="Analyze the full image and create balanced, concise metadata.",
    title_rule="Minimum 5 words, maximum 165 characters, descriptive, unique, no special characters",
    description_rule="Minimum 5 words, maximum 165 characters, clear informative summary, unique, no special characters",
    keyword_rule="Provide up to 60 unique keywords relevant to the image; ensure at least 55 unique. If fewer are obvious, add closely-related synonyms/variations. No multi-word phrases.",
)

OPENAI_PROMPT_TEXT_PNG_BALANCED = _build_openai_prompt(
    intro="Focus strictly on the main subject when generating metadata.",
    title_rule="Minimum 5 words, maximum 165 characters, main subject only, unique, no special characters",
    description_rule="Minimum 5 words, maximum 165 characters, highlight main subject details only, unique, no special characters",
    keyword_rule="Provide up to 60 unique keywords for the main subject; ensure at least 55 unique. If fewer are obvious, add closely-related synonyms/variations. No multi-word phrases.",
)

OPENAI_PROMPT_TEXT_VIDEO_BALANCED = _build_openai_prompt(
    intro="Analyze the video frames to create balanced metadata.",
    title_rule="Minimum 5 words, maximum 165 characters, video-focused, unique, no special characters",
    description_rule="Minimum 5 words, maximum 165 characters, concise video summary, unique, no special characters",
    keyword_rule="Provide up to 60 unique keywords covering the video content; ensure at least 55 unique. If fewer are obvious, add closely-related synonyms/variations. No multi-word phrases.",
    is_video=True,
)

OPENAI_PROMPT_TEXT_FAST = _build_openai_prompt(
    intro="Analyze the image quickly and produce concise metadata.",
    title_rule="Minimum 4 words, maximum 150 characters, descriptive, unique, no special characters",
    description_rule="Minimum 4 words, maximum 150 characters, concise, unique, no special characters",
    keyword_rule="Provide up to 60 unique keywords relevant to the image; ensure at least 55 unique. If fewer are obvious, add closely-related synonyms/variations. No multi-word phrases.",
)

OPENAI_PROMPT_TEXT_PNG_FAST = _build_openai_prompt(
    intro="Focus on the main subject only to produce concise metadata.",
    title_rule="Minimum 4 words, maximum 150 characters, main subject only, unique, no special characters",
    description_rule="Minimum 4 words, maximum 150 characters, concise main subject details, unique, no special characters",
    keyword_rule="Provide up to 60 unique keywords for the main subject; ensure at least 55 unique. If fewer are obvious, add closely-related synonyms/variations. No multi-word phrases.",
)

OPENAI_PROMPT_TEXT_VIDEO_FAST = _build_openai_prompt(
    intro="Analyze the video frames quickly and produce concise metadata.",
    title_rule="Minimum 4 words, maximum 150 characters, video-focused, unique, no special characters",
    description_rule="Minimum 4 words, maximum 150 characters, concise video summary, unique, no special characters",
    keyword_rule="Provide up to 60 unique keywords describing the video content; ensure at least 55 unique. If fewer are obvious, add closely-related synonyms/variations. No multi-word phrases.",
    is_video=True,
)

_OPENAI_PROMPT_PRIORITY_MAP = {
    "Detailed": {
        "default": OPENAI_PROMPT_TEXT,
        "png": OPENAI_PROMPT_TEXT_PNG,
        "video": OPENAI_PROMPT_TEXT_VIDEO,
    },
    "Balanced": {
        "default": OPENAI_PROMPT_TEXT_BALANCED,
        "png": OPENAI_PROMPT_TEXT_PNG_BALANCED,
        "video": OPENAI_PROMPT_TEXT_VIDEO_BALANCED,
    },
    "Less": {
        "default": OPENAI_PROMPT_TEXT_FAST,
        "png": OPENAI_PROMPT_TEXT_PNG_FAST,
        "video": OPENAI_PROMPT_TEXT_VIDEO_FAST,
    },
}

_GEMINI_PROMPT_PRIORITY_MAP = {
    "Detailed": {
        "default": PROMPT_TEXT,
        "png": PROMPT_TEXT_PNG,
        "video": PROMPT_TEXT_VIDEO,
    },
    "Balanced": {
        "default": PROMPT_TEXT_BALANCED,
        "png": PROMPT_TEXT_PNG_BALANCED,
        "video": PROMPT_TEXT_VIDEO_BALANCED,
    },
    "Less": {
        "default": PROMPT_TEXT_FAST,
        "png": PROMPT_TEXT_PNG_FAST,
        "video": PROMPT_TEXT_VIDEO_FAST,
    },
}


def select_prompt(
    priority: str,
    use_png_prompt: bool = False,
    use_video_prompt: bool = False,
    provider: str = "openai",
) -> str:
    provider_key = (provider or "openai").strip().lower()
    if provider_key == "gemini":
        priority_map = _GEMINI_PROMPT_PRIORITY_MAP
    else:
        priority_map = _OPENAI_PROMPT_PRIORITY_MAP

    priority_key = priority if priority in priority_map else "Detailed"
    variants = priority_map[priority_key]

    if use_video_prompt:
        return variants.get("video", variants["default"])
    if use_png_prompt:
        return variants.get("png", variants["default"])
    return variants["default"]
