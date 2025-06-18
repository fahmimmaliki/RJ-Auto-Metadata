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

# Semua konstanta prompt Gemini API

# --- KUALITAS (detail, versi optimized) ---
PROMPT_TEXT = '''
Analyze the image thoroughly and generate high-quality metadata in English:

1. Title: Create a unique, highly descriptive title (minimal 6 words, with max 180 character). Focus on distinctive visual features, composition, lighting, mood, or unique elements. Include specific details that make this image stand out from similar ones. Consider artistic aspects, technical quality, and emotional impact.
2. Description: Write a detailed, engaging description (minimal 6 words, with max 180 character). Describe Who/What/Where/When/Why with rich detail. Include context, setting, actions, emotions, or story elements. Mention technical aspects like lighting, composition, or perspective when relevant. Make it descriptive enough to paint a mental picture.
3. Keywords: Generate 60-65 carefully selected single-word keywords, comma-separated. Include specific, descriptive terms related to all aspects of the image. Cover subjects, actions, emotions, colors, styles, techniques, and concepts. Use varied vocabulary including technical, artistic, and conceptual terms.
4. Adobe Stock Category: Choose one (number and name): 1.Animals, 2.Buildings and Architecture, 3.Business, 4.Drinks, 5.The Environment, 6.States of Mind, 7.Food, 8.Graphic Resources, 9.Hobbies and Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants and Flowers, 15.Culture and Religion, 16.Science, 17.Social Issues, 18.Sports, 19.Technology, 20.Transport, 21.Travel
5. Shutterstock Category: Abstract, Animals/Wildlife, Arts, Backgrounds/Textures, Beauty/Fashion, Buildings/Landmarks, Business/Finance, Celebrities, Education, Food and drink, Healthcare/Medical, Holidays, Industrial, Interiors, Miscellaneous, Nature, Objects, Parks/Outdoor, People, Religion, Science, Signs/Symbols, Sports/Recreation, Technology, Transportation, Vintage

Format:
Title: [title]
Description: [description]
Keywords: [keywords]
AdobeStockCategory: [number. name]
ShutterstockCategory: [name]
'''

PROMPT_TEXT_PNG = '''
Analyze the image thoroughly and generate high-quality metadata in English, focusing on the main object or subject:

1. Title: Create a precise, descriptive title for the main object or subject (minimal 6 words, with max 180 character). Focus on visible object or subject. Include specific details about the object or subject's appearance, pose, condition, or style. Mention distinctive features, colors, textures, or unique characteristics.
2. Description: Write a detailed description of the main object or subject only (minimal 6 words, with max 180 character). Focus on visible elements. Include object or subject's appearance, condition, orientation, style, or context. Mention materials, textures, colors, or distinctive features. Describe any actions, poses, or expressions if applicable.
3. Keywords: Generate 60-65 single-word keywords exclusively for the main object or subject, comma-separated. Focus on object or subject's characteristics, materials, colors, style, function, or category. Include specific descriptive terms and broader conceptual keywords.
4. Adobe Stock Category: Choose one (number and name): 1.Animals, 2.Buildings and Architecture, 3.Business, 4.Drinks, 5.The Environment, 6.States of Mind, 7.Food, 8.Graphic Resources, 9.Hobbies and Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants and Flowers, 15.Culture and Religion, 16.Science, 17.Social Issues, 18.Sports, 19.Technology, 20.Transport, 21.Travel
5. Shutterstock Category: Abstract, Animals/Wildlife, Arts, Backgrounds/Textures, Beauty/Fashion, Buildings/Landmarks, Business/Finance, Celebrities, Education, Food and drink, Healthcare/Medical, Holidays, Industrial, Interiors, Miscellaneous, Nature, Objects, Parks/Outdoor, People, Religion, Science, Signs/Symbols, Sports/Recreation, Technology, Transportation, Vintage

Format:
Title: [title]
Description: [description]
Keywords: [keywords]
AdobeStockCategory: [number. name]
ShutterstockCategory: [name]
'''

PROMPT_TEXT_VIDEO = '''
Analyze these video frames comprehensively and generate detailed video metadata:

1. Title: Create a dynamic, descriptive video title (minimal 6 words, with max 180 character). Analyze ALL frames to understand the complete video narrative. Consider motion, action sequences, scene transitions, or story progression. Include specific details about subjects, actions, setting, and visual style. Emphasize the dynamic nature and key visual elements across frames.
2. Description: Write a comprehensive video description (minimal 6 words, with max 180 character). Describe main subjects, their actions, and scene progression across all frames. Include context, setting, mood, and any narrative elements. Mention camera movement, visual style, or technical aspects when relevant. Consider the temporal aspects and changes between frames.
3. Keywords: Generate 60-65 single-word keywords covering all video aspects, comma-separated. Include both static elements (subjects, objects, settings) and dynamic aspects (actions, movements, emotions). Cover visual style, technical aspects, narrative elements, and conceptual themes. Use specific terms for video content, production style, and intended use.
4. Adobe Stock Category: Choose one (number and name): 1.Animals, 2.Buildings and Architecture, 3.Business, 4.Drinks, 5.The Environment, 6.States of Mind, 7.Food, 8.Graphic Resources, 9.Hobbies and Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants and Flowers, 15.Culture and Religion, 16.Science, 17.Social Issues, 18.Sports, 19.Technology, 20.Transport, 21.Travel
5. Shutterstock Category: Abstract, Animals/Wildlife, Arts, Backgrounds/Textures, Beauty/Fashion, Buildings/Landmarks, Business/Finance, Celebrities, Education, Food and drink, Healthcare/Medical, Holidays, Industrial, Interiors, Miscellaneous, Nature, Objects, Parks/Outdoor, People, Religion, Science, Signs/Symbols, Sports/Recreation, Technology, Transportation, Vintage

Format:
Title: [title]
Description: [description]
Keywords: [keywords]
AdobeStockCategory: [number. name]
ShutterstockCategory: [name]
'''


# --- SEIMBANG (medium detail) ---
PROMPT_TEXT_BALANCED = '''
Analyze the image and generate balanced metadata in English:

1. Title: Create a descriptive title (minimal 5 words, with max 180 character) with specific details from the image. Include key visual elements and distinguishing features. Mention main subjects, setting, or notable characteristics.
2. Description: Write a clear description (minimal 5 words, with max 180 character) covering key image elements. Describe main subjects, setting, and important visual details. Include relevant context or actions when present.
3. Keywords: Generate 60-65 single-word keywords, comma-separated. Include relevant terms for the image. Cover main subjects, visual elements, colors, and concepts. Balance specific and general terms for good discoverability.
4. Adobe Stock Category: Choose one (number and name): 1.Animals, 2.Buildings and Architecture, 3.Business, 4.Drinks, 5.The Environment, 6.States of Mind, 7.Food, 8.Graphic Resources, 9.Hobbies and Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants and Flowers, 15.Culture and Religion, 16.Science, 17.Social Issues, 18.Sports, 19.Technology, 20.Transport, 21.Travel
5. Shutterstock Category: Abstract, Animals/Wildlife, Arts, Backgrounds/Textures, Beauty/Fashion, Buildings/Landmarks, Business/Finance, Celebrities, Education, Food and drink, Healthcare/Medical, Holidays, Industrial, Interiors, Miscellaneous, Nature, Objects, Parks/Outdoor, People, Religion, Science, Signs/Symbols, Sports/Recreation, Technology, Transportation, Vintage

Format:
Title: [title]
Description: [description]
Keywords: [keywords]
AdobeStockCategory: [number. name]
ShutterstockCategory: [name]
'''

PROMPT_TEXT_PNG_BALANCED = '''
Analyze this image and generate balanced metadata in English, focus on main object or subject:

1. Title: Create a descriptive title for main object or subject (minimal 5 words, with max 180 character) with specific details. Focus on the visible object or subject. Include key characteristics or distinguishing features.
2. Description: Write a clear description of main object or subject (minimal 5 words, with max 180 character). Describe the object or subject's appearance and key details. Include materials, colors, or notable features when relevant.
3. Keywords: Generate 60-65 single-word keywords for main object or subject, comma-separated. Focus on the object or subject. Include descriptive terms covering appearance, function, and category.
4. Adobe Stock Category: Choose one (number and name): 1.Animals, 2.Buildings and Architecture, 3.Business, 4.Drinks, 5.The Environment, 6.States of Mind, 7.Food, 8.Graphic Resources, 9.Hobbies and Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants and Flowers, 15.Culture and Religion, 16.Science, 17.Social Issues, 18.Sports, 19.Technology, 20.Transport, 21.Travel
5. Shutterstock Category: Abstract, Animals/Wildlife, Arts, Backgrounds/Textures, Beauty/Fashion, Buildings/Landmarks, Business/Finance, Celebrities, Education, Food and drink, Healthcare/Medical, Holidays, Industrial, Interiors, Miscellaneous, Nature, Objects, Parks/Outdoor, People, Religion, Science, Signs/Symbols, Sports/Recreation, Technology, Transportation, Vintage

Format:
Title: [title]
Description: [description]
Keywords: [keywords]
AdobeStockCategory: [number. name]
ShutterstockCategory: [name]
'''

PROMPT_TEXT_VIDEO_BALANCED = '''
Analyze these video frames and generate balanced metadata:

1. Title: Create a video title (minimal 5 words, with max 180 character) describing content across all frames. Consider the video narrative and main visual elements. Include key subjects and actions shown in the frames.
2. Description: Write a video description (minimal 5 words, with max 180 character) covering key elements and actions. Describe main subjects and their activities across frames. Include setting and important visual details.
3. Keywords: Generate 60-65 single-word keywords, comma-separated. Include video-related terms. Cover subjects, actions, settings, and visual elements. Include both static and dynamic aspects of the video content.
4. Adobe Stock Category: Choose one (number and name): 1.Animals, 2.Buildings and Architecture, 3.Business, 4.Drinks, 5.The Environment, 6.States of Mind, 7.Food, 8.Graphic Resources, 9.Hobbies and Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants and Flowers, 15.Culture and Religion, 16.Science, 17.Social Issues, 18.Sports, 19.Technology, 20.Transport, 21.Travel
5. Shutterstock Category: Abstract, Animals/Wildlife, Arts, Backgrounds/Textures, Beauty/Fashion, Buildings/Landmarks, Business/Finance, Celebrities, Education, Food and drink, Healthcare/Medical, Holidays, Industrial, Interiors, Miscellaneous, Nature, Objects, Parks/Outdoor, People, Religion, Science, Signs/Symbols, Sports/Recreation, Technology, Transportation, Vintage

Format:
Title: [title]
Description: [description]
Keywords: [keywords]
AdobeStockCategory: [number. name]
ShutterstockCategory: [name]
'''

# --- CEPAT (minimal, optimized) ---
PROMPT_TEXT_FAST = '''
Generate metadata quickly in English:

1. Title: Descriptive title (minimal 4 words, with max 180 character).
2. Description: Clear description (minimal 4 words, with max 180 character).
3. Keywords: 50-60 single-word keywords, comma-separated.
4. Adobe Stock Category: Choose one (number and name): 1.Animals, 2.Buildings and Architecture, 3.Business, 4.Drinks, 5.The Environment, 6.States of Mind, 7.Food, 8.Graphic Resources, 9.Hobbies and Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants and Flowers, 15.Culture and Religion, 16.Science, 17.Social Issues, 18.Sports, 19.Technology, 20.Transport, 21.Travel
5. Shutterstock Category: Abstract, Animals/Wildlife, Arts, Backgrounds/Textures, Beauty/Fashion, Buildings/Landmarks, Business/Finance, Celebrities, Education, Food and drink, Healthcare/Medical, Holidays, Industrial, Interiors, Miscellaneous, Nature, Objects, Parks/Outdoor, People, Religion, Science, Signs/Symbols, Sports/Recreation, Technology, Transportation, Vintage

Format:
Title: [title]
Description: [description]
Keywords: [keywords]
AdobeStockCategory: [number. name]
ShutterstockCategory: [name]
'''

PROMPT_TEXT_PNG_FAST = '''
Generate metadata for this image quickly in English, focus on main object or subject:

1. Title: Object or subject title (minimal 4 words, with max 180 character).
2. Description: Object or subject description (minimal 4 words, with max 180 character).
3. Keywords: 50-60 single-word keywords for main object or subject, comma-separated.
4. Adobe Stock Category: Choose one (number and name): 1.Animals, 2.Buildings and Architecture, 3.Business, 4.Drinks, 5.The Environment, 6.States of Mind, 7.Food, 8.Graphic Resources, 9.Hobbies and Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants and Flowers, 15.Culture and Religion, 16.Science, 17.Social Issues, 18.Sports, 19.Technology, 20.Transport, 21.Travel
5. Shutterstock Category: Abstract, Animals/Wildlife, Arts, Backgrounds/Textures, Beauty/Fashion, Buildings/Landmarks, Business/Finance, Celebrities, Education, Food and drink, Healthcare/Medical, Holidays, Industrial, Interiors, Miscellaneous, Nature, Objects, Parks/Outdoor, People, Religion, Science, Signs/Symbols, Sports/Recreation, Technology, Transportation, Vintage

Format:
Title: [title]
Description: [description]
Keywords: [keywords]
AdobeStockCategory: [number. name]
ShutterstockCategory: [name]
'''

PROMPT_TEXT_VIDEO_FAST = '''
Generate metadata for video frames:

1. Title: Video title (minimal 4 words, with max 180 character) from all frames.
2. Description: Video description (minimal 4 words, with max 180 character).
3. Keywords: 50-60 single-word keywords, comma-separated.
4. Adobe Stock Category: Choose one (number and name): 1.Animals, 2.Buildings and Architecture, 3.Business, 4.Drinks, 5.The Environment, 6.States of Mind, 7.Food, 8.Graphic Resources, 9.Hobbies and Leisure, 10.Industry, 11.Landscapes, 12.Lifestyle, 13.People, 14.Plants and Flowers, 15.Culture and Religion, 16.Science, 17.Social Issues, 18.Sports, 19.Technology, 20.Transport, 21.Travel
5. Shutterstock Category: Abstract, Animals/Wildlife, Arts, Backgrounds/Textures, Beauty/Fashion, Buildings/Landmarks, Business/Finance, Celebrities, Education, Food and drink, Healthcare/Medical, Holidays, Industrial, Interiors, Miscellaneous, Nature, Objects, Parks/Outdoor, People, Religion, Science, Signs/Symbols, Sports/Recreation, Technology, Transportation, Vintage

Format:
Title: [title]
Description: [description]
Keywords: [keywords]
AdobeStockCategory: [number. name]
ShutterstockCategory: [name]
''' 