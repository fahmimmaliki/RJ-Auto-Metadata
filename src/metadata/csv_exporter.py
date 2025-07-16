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

# src/metadata/csv_exporter.py
import os
import re
from src.utils.logging import log_message
from src.utils.file_utils import sanitize_csv_field, write_to_csv
from src.metadata.categories.for_adobestock import map_to_adobe_stock_category
from src.metadata.categories.for_shutterstock import map_to_shutterstock_category, map_to_shutterstock_category_video

def smart_truncate_description(description, max_length=200):
    if not description:
        return ""
    
    description = str(description).strip()
    if len(description) <= max_length:
        return description
    
    truncated = description[:max_length]
    
    last_period_pos = truncated.rfind('.')
    
    if last_period_pos > 0 and last_period_pos < max_length - 1:
        result = description[:last_period_pos + 1]
        log_message(f"Smart truncate: Cut to last period ({len(result)} chars)")
        return result
    
    result = description[:max_length - 1] + '.'
    log_message(f"Smart truncate: Hard cut + period ({len(result)} chars)")
    return result

def smart_truncate_title(title, max_length=200):
    if not title:
        return ""
    
    title = str(title).strip()
    
    if len(title) <= max_length:
        return title
    
    truncated = title[:max_length]
    
    last_period_pos = truncated.rfind('.')
    
    if last_period_pos > 0 and last_period_pos < max_length - 1:
        result = title[:last_period_pos + 1]
        log_message(f"Smart truncate title: Cut to last period ({len(result)} chars)")
        return result
    
    result = title[:max_length - 1] + '.'
    log_message(f"Smart truncate title: Hard cut + period ({len(result)} chars)")
    return result

def sanitize_adobe_stock_title(title):
    if not title:
        return ""
    sanitized = re.sub(r'[\r\n\t]+', ' ', str(title))
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    sanitized = re.sub(r'[^\w\s\-:]', '', sanitized)
    sanitized = smart_truncate_title(sanitized, max_length=200)
    
    if sanitized and not sanitized.endswith('.'):
        if len(sanitized) < 200:sanitized += '.'
        else:
            sanitized = sanitized[:-1] + '.'
    
    return sanitized

def sanitize_adobe_stock_keywords(keywords):
    if isinstance(keywords, list):
        sanitized_list = []
        for keyword in keywords:
            if keyword:
                clean_kw = re.sub(r'[\r\n\t]+', ' ', str(keyword))
                clean_kw = re.sub(r'\s+', ' ', clean_kw).strip()
                clean_kw = re.sub(r'[^\w\s\-]', '', clean_kw)
                if clean_kw:
                    sanitized_list.append(clean_kw)
        return ', '.join(sanitized_list)
    else:
        clean_kw = re.sub(r'[\r\n\t]+', ' ', str(keywords))
        clean_kw = re.sub(r'\s+', ' ', clean_kw).strip()
        clean_kw = re.sub(r'[^\w\s\-,]', '', clean_kw)
        return clean_kw

def sanitize_vecteezy_title(title):
    if not title:
        return ""
    
    sanitized = re.sub(r'[\r\n\t]+', ' ', str(title))
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    sanitized = sanitized.replace(':', ' -')
    sanitized = re.sub(r'[^\w\s\-]', '', sanitized)
    sanitized = smart_truncate_title(sanitized, max_length=200)
    
    if sanitized and not sanitized.endswith('.'):
        if len(sanitized) < 200:sanitized += '.'
        else:
            sanitized = sanitized[:-1] + '.'
    
    return sanitized

def sanitize_vecteezy_keywords(keywords):
    if isinstance(keywords, list):
        sanitized_list = []
        for keyword in keywords:
            if keyword:
                clean_kw = re.sub(r'[\r\n\t]+', ' ', str(keyword))
                clean_kw = re.sub(r'\s+', ' ', clean_kw).strip().lower()
                clean_kw = re.sub(r'[^\w\s]', '', clean_kw)
                clean_kw = re.sub(r'\bvector\b', '', clean_kw, flags=re.IGNORECASE)
                clean_kw = re.sub(r'vector', '', clean_kw, flags=re.IGNORECASE)
                clean_kw = re.sub(r'\s+', ' ', clean_kw).strip()
                if clean_kw:
                    sanitized_list.append(clean_kw)
        return ', '.join(sanitized_list)
    else:
        clean_kw = re.sub(r'[\r\n\t]+', ' ', str(keywords))
        clean_kw = re.sub(r'\s+', ' ', clean_kw).strip()
        clean_kw = re.sub(r'[^\w\s,]', '', clean_kw)
        clean_kw = re.sub(r'\bvector\b', '', clean_kw, flags=re.IGNORECASE)
        clean_kw = re.sub(r'vector', '', clean_kw, flags=re.IGNORECASE)
        clean_kw = re.sub(r'\s+', ' ', clean_kw).strip()
        return clean_kw

def write_123rf_csv(csv_path, filename, description, keywords):
    csv_dir = os.path.dirname(csv_path)
    if not os.path.exists(csv_dir):
        try:
            os.makedirs(csv_dir)
        except Exception as e:
            log_message(f"Error: Failed to create CSV directory for 123RF: {e}")
            return False
    
    file_exists = os.path.isfile(csv_path)
    try:
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            if not file_exists or os.path.getsize(csv_path) == 0:
                csvfile.write('oldfilename,"123rf_filename","description","keywords","country"\n')
            truncated_description = smart_truncate_description(description, max_length=200)
            safe_filename = filename.replace('"', '""')
            safe_description = truncated_description.replace('"', '""')
            safe_keywords = keywords.replace('"', '""')
            csvfile.write(f'{safe_filename},"","{safe_description}","{safe_keywords}","ID"\n')
        return True
    except Exception as e:
        log_message(f"Error writing to CSV 123RF: {e}")
        return False

def write_vecteezy_csv(csv_path, filename, title, description, keywords):
    csv_dir = os.path.dirname(csv_path)
    if not os.path.exists(csv_dir):
        try:
            os.makedirs(csv_dir)
        except Exception as e:
            log_message(f"Error: Failed to create CSV directory for Vecteezy: {e}")
            return False
    
    file_exists = os.path.isfile(csv_path)
    try:
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            if not file_exists or os.path.getsize(csv_path) == 0:
                csvfile.write('Filename,Title,Description,Keywords,License,Id\n')
            
            truncated_title = smart_truncate_title(title, max_length=200)
            truncated_description = smart_truncate_description(description, max_length=200)
            
            safe_filename = filename.replace('"', '""')
            safe_title = truncated_title.replace('"', '""')
            safe_description = truncated_description.replace('"', '""')
            safe_keywords = keywords.replace('"', '""')
            
            csvfile.write(f'{safe_filename},{safe_title},"{safe_description}","{safe_keywords}",pro,\n')
        return True
    except Exception as e:
        log_message(f"Error writing to CSV Vecteezy: {e}")
        return False

def write_miri_canvas_csv(csv_path, filename, title, keywords):
    import re
    csv_dir = os.path.dirname(csv_path)
    if not os.path.exists(csv_dir):
        try:
            os.makedirs(csv_dir)
        except Exception as e:
            log_message(f"Error: Failed to create CSV directory for Miri Canvas: {e}")
            return False

    file_exists = os.path.isfile(csv_path)
    try:
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            if not file_exists or os.path.getsize(csv_path) == 0:
                csvfile.write('fileName,"uniqueId","elementName","keywords","tier","contentType"\n')

            base_filename = os.path.splitext(filename)[0]
            from src.metadata.csv_exporter import smart_truncate_title
            safe_title = smart_truncate_title(str(title), max_length=100)
            safe_title = re.sub(r'[^\w\s-]', '', safe_title)
            if isinstance(keywords, list):
                safe_keywords = ','.join(keywords[:25])
            else:
                safe_keywords = ','.join(str(keywords).split(',')[:25])
            tier = 'Premium'
            content_type = ''
            unique_id = ''
            csvfile.write(f'{base_filename},"{unique_id}","{safe_title}","{safe_keywords}","{tier}","{content_type}"\n')
        return True
    except Exception as e:
        log_message(f"Error writing to CSV Miri Canvas: {e}")
        return False

def validate_metadata_completeness(metadata, filename="unknown"):

    issues = []
    validated_metadata = {}
    
    if not metadata:
        issues.append("Metadata empty or None")
        return False, {}, issues
    
    if isinstance(metadata, dict):
        title = metadata.get("title", "")
        description = metadata.get("description", "")
        tags = metadata.get("tags", [])
        
        if not title or not str(title).strip():
            issues.append("Title empty or None")
            base_filename = filename.replace(".jpg", "").replace(".jpeg", "").replace(".png", "").replace(".mp4", "").replace(".eps", "").replace(".ai", "").replace(".svg", "")
            validated_metadata["title"] = base_filename or "Untitled"
            log_message(f"Warning: Title empty for {filename}, using filename as fallback", "warning")
        else:
            validated_metadata["title"] = str(title).strip()
        
        if not description or not str(description).strip():
            issues.append("Description empty or None") 
            validated_metadata["description"] = validated_metadata["title"]
            log_message(f"Warning: Description empty for {filename}, using title as fallback", "warning")
        else:
            validated_metadata["description"] = str(description).strip()
        
        if not tags or (isinstance(tags, list) and len(tags) == 0):
            issues.append("Tags/keywords empty or None")
            title_words = validated_metadata["title"].lower().replace("-", " ").replace("_", " ").split()
            filtered_words = [word for word in title_words if len(word) > 2 and word not in ["the", "and", "for", "with", "from"]]
            validated_metadata["tags"] = filtered_words[:5] if filtered_words else ["image", "stock", "photo"]
            log_message(f"Warning: Keywords empty for {filename}, generated from title as fallback", "warning")
        elif isinstance(tags, list):
            cleaned_tags = [str(tag).strip() for tag in tags if tag and str(tag).strip()]
            if not cleaned_tags:
                issues.append("All tags empty after cleaning")
                validated_metadata["tags"] = ["image", "stock", "photo"]  # Ultimate fallback
                log_message(f"Warning: All keywords empty after cleaning for {filename}", "warning")
            else:
                validated_metadata["tags"] = cleaned_tags
        else:
            tag_string = str(tags).strip()
            if not tag_string:
                validated_metadata["tags"] = ["image", "stock", "photo"]
                issues.append("Tag string empty")
            else:
                tag_list = [tag.strip() for tag in tag_string.replace(";", ",").split(",") if tag.strip()]
                validated_metadata["tags"] = tag_list if tag_list else ["image", "stock", "photo"]
        
        validated_metadata["as_category"] = metadata.get("as_category", "")
        validated_metadata["ss_category"] = metadata.get("ss_category", "")
        validated_metadata["keyword_count"] = metadata.get("keyword_count", "49")
        
    else:
        issues.append(f"Metadata is not a dictionary: {type(metadata)}")
        return False, {}, issues
    
    essential_fields = ["title", "description", "tags"]
    missing_fields = [field for field in essential_fields if not validated_metadata.get(field)]
    
    if missing_fields:
        issues.append(f"Essential field still empty after validation: {missing_fields}")
        return False, validated_metadata, issues
    
    if issues:
        log_message(f"Metadata validation: {len(issues)} issue(s) fixed for {filename}")
    
    return True, validated_metadata, issues

def write_to_platform_csvs_safe(csv_dir, filename, title, description, keywords, auto_kategori_enabled=True, is_vector=False, max_keywords=49, is_video=False):

    try:
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir, exist_ok=True)
        
        if isinstance(title, dict):
            is_valid, validated_metadata, issues = validate_metadata_completeness(title, filename)
            if not is_valid:
                log_message(f"ERROR CSV: Metadata not valid for {filename}: {issues}", "error")
                return False, ["All platforms - Invalid metadata"]
            
            safe_title = validated_metadata["title"]
            safe_description = validated_metadata["description"] 
            keywords = validated_metadata["tags"]
        else:
            if not title or not str(title).strip():
                log_message(f"ERROR CSV: Title empty for {filename}", "error")
                base_filename = filename.replace(".jpg", "").replace(".jpeg", "").replace(".png", "").replace(".mp4", "").replace(".eps", "").replace(".ai", "").replace(".svg", "")
                safe_title = base_filename or "Untitled"
            else:
                safe_title = str(title).strip()
            
            if not description or not str(description).strip():
                log_message(f"ERROR CSV: Description empty for {filename}", "error") 
                safe_description = safe_title
            else:
                safe_description = str(description).strip()
                
            if not keywords or (isinstance(keywords, list) and len(keywords) == 0):
                log_message(f"ERROR CSV: Keywords empty for {filename}", "error")
                keywords = ["image", "stock", "photo"]
        
        safe_filename = sanitize_csv_field(filename)
        
        safe_title = smart_truncate_title(sanitize_csv_field(safe_title), max_length=200)
        safe_description = smart_truncate_description(sanitize_csv_field(safe_description), max_length=200)
        
        if isinstance(keywords, list):
            keywords = list(dict.fromkeys([k for k in keywords if k and str(k).strip()]))
            keywords = keywords[:max_keywords]
            ss_keywords = ', '.join([sanitize_csv_field(k) for k in keywords if k])
            as_keywords = ', '.join([sanitize_csv_field(k) for k in keywords if k])
        else:
            ss_keywords = sanitize_csv_field(str(keywords))
            as_keywords = sanitize_csv_field(str(keywords))
        
        if not safe_filename or not safe_title or not safe_description or not (ss_keywords or as_keywords):
            log_message(f"ERROR CSV: Final data not valid after sanitization for {filename}", "error")
            return False, ["All platforms - Data validation failed"]
        
        as_category = ""
        ss_category = ""
        if auto_kategori_enabled:
            as_category = map_to_adobe_stock_category(safe_title, safe_description, keywords if isinstance(keywords, list) else [])
            if is_video:
                ss_category = map_to_shutterstock_category_video(safe_title, safe_description, keywords if isinstance(keywords, list) else [])
            else:
                ss_category = map_to_shutterstock_category(safe_title, safe_description, keywords if isinstance(keywords, list) else [])
            log_message(f"Auto Category: Active (AS: {as_category}, SS: {ss_category})")
        else:
            log_message(f"Auto Category: Inactive")
        
        success_count = 0
        failed_platforms = []
        
        # Adobe Stock
        try:
            as_csv_path = os.path.join(csv_dir, "adobe_stock_export.csv")
            as_header = ["Filename", "Title", "Keywords", "Category", "Releases"]
            as_title_clean = sanitize_adobe_stock_title(safe_title)
            as_keywords_clean = sanitize_adobe_stock_keywords(keywords if isinstance(keywords, list) else as_keywords)
            as_data_row = [safe_filename, as_title_clean, as_keywords_clean, as_category, ""]
            
            if write_to_csv(as_csv_path, as_header, as_data_row):
                success_count += 1
            else:
                failed_platforms.append("Adobe Stock")
        except Exception as e:
            log_message(f"ERROR CSV Adobe Stock: {e}", "error")
            failed_platforms.append("Adobe Stock")
        
        # ShutterStock  
        try:
            ss_csv_path = os.path.join(csv_dir, "shutterstock_export.csv")
            ss_header = ["Filename", "Description", "Keywords", "Categories", "Editorial", "Mature content", "illustration"]
            illustration_value = "yes" if is_vector else ""
            ss_data_row = [safe_filename, safe_description, ss_keywords, ss_category, "no", "", illustration_value]
            
            if write_to_csv(ss_csv_path, ss_header, ss_data_row):
                success_count += 1
            else:
                failed_platforms.append("Shutterstock")
        except Exception as e:
            log_message(f"ERROR CSV Shutterstock: {e}", "error")
            failed_platforms.append("Shutterstock")
        
        # 123RF
        try:
            rf_csv_path = os.path.join(csv_dir, "123rf_export.csv")
            if write_123rf_csv(rf_csv_path, safe_filename, safe_description, as_keywords):
                success_count += 1
            else:
                failed_platforms.append("123RF")
        except Exception as e:
            log_message(f"ERROR CSV 123RF: {e}", "error")
            failed_platforms.append("123RF")
        
        # Vecteezy
        try:
            vz_csv_path = os.path.join(csv_dir, "vecteezy_export.csv")
            vz_title_clean = sanitize_vecteezy_title(safe_title)
            vz_keywords_clean = sanitize_vecteezy_keywords(keywords if isinstance(keywords, list) else as_keywords)
            if write_vecteezy_csv(vz_csv_path, safe_filename, vz_title_clean, safe_description, vz_keywords_clean):
                success_count += 1
            else:
                failed_platforms.append("Vecteezy")
        except Exception as e:
            log_message(f"ERROR CSV Vecteezy: {e}", "error")
            failed_platforms.append("Vecteezy")
        
        # Depositphotos
        try:
            dp_csv_path = os.path.join(csv_dir, "depositphotos_export.csv")
            dp_header = ["Filename", "description", "Keywords", "Nudity", "Editorial"]
            dp_data_row = [safe_filename, safe_description, as_keywords, "no", "no"]
            
            if write_to_csv(dp_csv_path, dp_header, dp_data_row):
                success_count += 1
            else:
                failed_platforms.append("Depositphotos")
        except Exception as e:
            log_message(f"ERROR CSV Depositphotos: {e}", "error")
            failed_platforms.append("Depositphotos")
        
        # Miri Canvas
        try:
            mc_csv_path = os.path.join(csv_dir, "miri_canvas_export.csv")
            mc_title_clean = sanitize_vecteezy_title(safe_title) # Use vecteezy sanitizer for Miri Canvas title
            mc_keywords_clean = sanitize_vecteezy_keywords(keywords if isinstance(keywords, list) else as_keywords) # Use vecteezy sanitizer for Miri Canvas keywords
            if write_miri_canvas_csv(mc_csv_path, safe_filename, mc_title_clean, mc_keywords_clean):
                success_count += 1
            else:
                failed_platforms.append("Miri Canvas")
        except Exception as e:
            log_message(f"ERROR CSV Miri Canvas: {e}", "error")
            failed_platforms.append("Miri Canvas")
        
        backup_dir = os.path.join(csv_dir, "backup")
        try:
            backup_success_count, backup_failed = write_platform_specific_txt_backups(
                backup_dir, safe_filename, safe_title, safe_description, keywords, 
                as_keywords, ss_keywords, as_category, ss_category, is_vector
            )
            
            if backup_success_count >= 3:
                log_message(f"TXT Backup: {backup_success_count}/6 platform backups successful")
            else:
                log_message(f"TXT Backup: WARNING - Only {backup_success_count}/6 backups successful", "warning")
                
            if backup_failed:
                log_message(f"TXT Backup failures: {', '.join(backup_failed)}", "warning")
                
        except Exception as e:
            log_message(f"TXT Backup: ERROR - {e}", "error")
        
        total_platforms = 6
        success_threshold = 4
        
        if success_count >= success_threshold:
            if failed_platforms:
                log_message(f"CSV Export: {success_count}/{total_platforms} successful. Failed: {', '.join(failed_platforms)}", "warning")
            else:
                log_message(f"CSV Export: Success for all {total_platforms} platforms")
            return True, failed_platforms
        else:
            log_message(f"CSV Export: CRITICAL - Only {success_count}/{total_platforms} successful. Threshold: {success_threshold}", "error")
            return False, failed_platforms
            
    except Exception as e:
        log_message(f"CRITICAL ERROR CSV: {e}", "error")
        import traceback
        log_message(f"Traceback: {traceback.format_exc()}", "error")
        return False, ["All platforms - Critical error"]

def write_to_platform_csvs(csv_dir, filename, title, description, keywords, auto_kategori_enabled=True, is_vector=False, max_keywords=49, is_video=False):

    try:
        success, failed_platforms = write_to_platform_csvs_safe(
            csv_dir, filename, title, description, keywords, 
            auto_kategori_enabled, is_vector, max_keywords, is_video
        )
        
        if failed_platforms and success:
            log_message(f"Note: Some platforms failed but still within threshold: {', '.join(failed_platforms)}", "info")
        elif failed_platforms and not success:
            log_message(f"Critical: Too many platforms failed: {', '.join(failed_platforms)}", "error")
        
        return success
        
    except Exception as e:
        log_message(f"Wrapper Error: {e}", "error")
        return False

def write_txt_backup(backup_dir, platform_name, header, data_rows):

    try:
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = os.path.join(backup_dir, f"{platform_name}_backup.txt")
        
        with open(backup_file, 'w', newline='', encoding='utf-8') as txtfile:
            if isinstance(header, list):
                header_line = ','.join([f'"{col}"' if ',' in col or '"' in col else col for col in header])
                txtfile.write(header_line + '\n')
            
            for row in data_rows:
                if isinstance(row, list):
                    formatted_row = []
                    for field in row:
                        field_str = str(field) if field is not None else ""
                        if '"' in field_str:
                            field_str = field_str.replace('"', '""')
                        if ',' in field_str or '"' in field_str or '\n' in field_str:
                            field_str = f'"{field_str}"'
                        formatted_row.append(field_str)
                    txtfile.write(','.join(formatted_row) + '\n')
        
        return True
        
    except Exception as e:
        log_message(f"Error writing TXT backup {platform_name}: {e}", "error")
        return False

def write_platform_specific_txt_backups(backup_dir, filename, safe_title, safe_description, keywords, as_keywords, ss_keywords, as_category, ss_category, is_vector=False):
    success_count = 0
    failed_platforms = []
    
    platform_data = {
        'adobe_stock': {
            'header': ["Filename", "Title", "Keywords", "Category", "Releases"],
            'data': [filename, sanitize_adobe_stock_title(safe_title), sanitize_adobe_stock_keywords(keywords if isinstance(keywords, list) else as_keywords), as_category, ""]
        },
        'shutterstock': {
            'header': ["Filename", "Description", "Keywords", "Categories", "Editorial", "Mature content", "illustration"],
            'data': [filename, safe_description, ','.join(ss_keywords.split(',')[:49]) if isinstance(ss_keywords, str) else ','.join(ss_keywords[:49]), ss_category, "no", "", "yes" if is_vector else ""]
        },
        '123rf': {
            'header': ['oldfilename', '"123rf_filename"', '"description"', '"keywords"', '"country"'],
            'data': [filename, "", safe_description, as_keywords, "ID"]  # RAW data, quotes will be handled by formatting
        },
        'vecteezy': {
            'header': ["Filename", "Title", "Description", "Keywords", "License", "Id"],
            'data': [filename, sanitize_vecteezy_title(safe_title), safe_description, sanitize_vecteezy_keywords(keywords if isinstance(keywords, list) else as_keywords), "pro", ""]  # RAW data
        },
        'depositphotos': {
            'header': ["Filename", "description", "Keywords", "Nudity", "Editorial"],
            'data': [filename, safe_description, as_keywords, "no", "no"]
        },
        'miri_canvas': {
            'header': ['fileName', '"uniqueId"', '"elementName"', '"keywords"', '"tier"', '"contentType"'],
            'data': [os.path.splitext(filename)[0], "", safe_title,','.join(as_keywords.split(',')[:25]) if isinstance(as_keywords, str) else ','.join(as_keywords[:25]), "Premium", ""]
        }
    }
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
    
    existing_data = {}
    for platform_name in platform_data.keys():
        backup_file = os.path.join(backup_dir, f"{platform_name}_backup.txt")
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        existing_data[platform_name] = [line.strip() for line in lines[1:]]
                    else:
                        existing_data[platform_name] = []
            except Exception as e:
                log_message(f"Warning: Failed to read existing backup {platform_name}: {e}", "warning")
                existing_data[platform_name] = []
        else:
            existing_data[platform_name] = []
    
    for platform_name, data in platform_data.items():
        try:
            new_row = data['data']
            formatted_new_row = []
            
            for i, field in enumerate(new_row):
                field_str = str(field) if field is not None else ""
                
                if platform_name == '123rf':
                    if i == 1:
                        formatted_new_row.append('""')
                    elif i in [2, 3, 4]:
                        escaped_field = field_str.replace('"', '""')
                        formatted_new_row.append(f'"{escaped_field}"')
                    else:
                        formatted_new_row.append(field_str)
                
                elif platform_name == 'miri_canvas':
                    if i == 1:
                        formatted_new_row.append('""')
                    elif i in [2, 3, 4, 6]:
                        escaped_field = field_str.replace('"', '""')
                        formatted_new_row.append(f'"{escaped_field}"')
                    else:
                        formatted_new_row.append(field_str)
                        
                elif platform_name == 'vecteezy':
                    if i in [2, 3]:
                        escaped_field = field_str.replace('"', '""')
                        if ',' in field_str or '"' in field_str or '\n' in field_str:
                            formatted_new_row.append(f'"{escaped_field}"')
                        else:
                            formatted_new_row.append(escaped_field)
                    else:
                        if ',' in field_str or '"' in field_str or '\n' in field_str:
                            escaped_field = field_str.replace('"', '""')
                            formatted_new_row.append(f'"{escaped_field}"')
                        else:
                            formatted_new_row.append(field_str)
                
                else:
                    if '"' in field_str:
                        field_str = field_str.replace('"', '""')
                    if ',' in field_str or '"' in field_str or '\n' in field_str:
                        field_str = f'"{field_str}"'
                    formatted_new_row.append(field_str)
            
            new_row_str = ','.join(formatted_new_row)
            
            existing_rows = existing_data.get(platform_name, [])
            
            valid_existing_rows = []
            for row in existing_rows:
                row = row.strip()
                if row and row != '':
                    expected_commas = len(data['header']) - 1
                    if row.count(',') >= expected_commas:
                        valid_existing_rows.append(row)
                    else:
                        log_message(f"Warning: Skipping malformed backup row in {platform_name}: {row[:50]}...", "warning")
            
            all_data_rows = valid_existing_rows + [new_row_str]
            
            backup_file = os.path.join(backup_dir, f"{platform_name}_backup.txt")
            with open(backup_file, 'w', newline='', encoding='utf-8') as txtfile:
                header = data['header']
                if platform_name == '123rf':
                    txtfile.write(','.join(header) + '\n')
                elif platform_name == 'miri_canvas':
                    txtfile.write(','.join(header) + '\n')
                else:
                    header_line = ','.join([f'"{col}"' if ',' in col or '"' in col else col for col in header])
                    txtfile.write(header_line + '\n')
                
                for row_str in all_data_rows:
                    if row_str.strip():
                        txtfile.write(row_str + '\n')
            
            success_count += 1
            
        except Exception as e:
            log_message(f"Error backup TXT {platform_name}: {e}", "error")
            failed_platforms.append(platform_name)
    
    return success_count, failed_platforms
