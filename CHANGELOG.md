# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
-

### Changed
-

### Fixed
-

## [3.7.0] - 2025-07-15

### Added
- **Gemini 2.5 Thinking Models Support:** Full integration with Google's latest Gemini 2.5 models featuring advanced reasoning capabilities:
  - **Gemini 2.5 Pro:** Dynamic thinking mode (-1)
  - **Gemini 2.5 Flash:** Dynamic thinking mode (-1)
  - **Gemini 2.5 Flash Lite:** Standard mode (0) no thinking
- **Google Generative AI SDK Integration:** Migrated from REST API to official `google-genai` Python SDK (v1.25.0) for:
  - Native thinking budget configuration support
  - Improved response handling and error management
  - Better API structure with `GenerateContentConfig` for advanced model features
- **Enhanced Token Management:** Significantly increased token limits to prevent MAX_TOKENS errors:
  - Removed dependency on quality priority for token allocation
  - High token limits optimized for thinking model overhead
  - Proper token allocation for both thinking and response generation
- **Miri Canvas CSV Export:** Added support for Miri Canvas CSV export:
  - `fileName`, `uniqueId`, `elementName`, `keywords`, `tier`, `contentType`
  - Custom header quoting, tier set to "Premium"
  - Specific quote placement for platform compatibility

### Changed
- **API Architecture Migration:** Complete transition from REST API requests to Google Generative AI SDK:
  - Maintained backward compatibility with REST API fallback for non-2.5 models
  - Improved error handling with proper SDK exception management
  - Enhanced response parsing for both SDK and REST API responses
- **User Interface Language:** Converted all UI elements and log messages from Indonesian to English for:
  - Better international accessibility and user experience
  - Improved consistency across the application
  - Enhanced compatibility with global user base
- **Model Configuration:** Updated model selection and configuration system:
  - Streamlined model-specific settings for thinking capabilities
  - Optimized configuration constants for easy maintenance
  - Improved model detection and feature support logic

### Fixed
- **Thinking Model Response Parsing:** Resolved "invalid response structure" errors for Gemini 2.5 models:
  - Fixed response structure handling for thinking vs non-thinking models
  - Proper parsing of SDK response format vs REST API format
  - Eliminated MAX_TOKENS errors through appropriate token allocation
- **API Response Validation:** Enhanced response validation for different model types:
  - Improved error detection and handling for thinking model responses
  - Better fallback mechanisms for response parsing failures
  - Robust handling of various response structures from different API endpoints

### Technical Details
- **SDK Integration:** Implemented proper `google-genai` library integration with `GenerateContentConfig` for advanced model configuration
- **Thinking Configuration:** Added configurable thinking budget constants for easy model behavior adjustment
- **Response Handling:** Dual-path response processing supporting both SDK and REST API response formats
- **Token Optimization:** Optimized token allocation strategy specifically for thinking model requirements
- **Error Recovery:** Enhanced error handling with proper SDK exception catching and fallback mechanisms

---
## [3.6.0] - 2025-06-20

### Added
- **TXT Backup System:** Implemented comprehensive backup functionality that creates TXT files with identical formatting to CSV exports:
  - Auto-creates `backup/` subfolder in `metadata_csv/` directory
  - Generates platform-specific backup files: `adobe_stock_backup.txt`, `shutterstock_backup.txt`, `123rf_backup.txt`, `vecteezy_backup.txt`, `depositphotos_backup.txt`
  - Cumulative backup system that appends new data while preserving historical entries
  - Perfect format matching with corresponding CSV files for seamless data recovery
- **Smart Description Truncation:** Added intelligent text truncation system to prevent upload failures:
  - `smart_truncate_description()`: Handles descriptions >200 characters by cutting at last period within limit, or hard-cutting to 199 chars + period
  - `smart_truncate_title()`: Similar logic for titles with smart period handling
  - Integrated into all platform sanitization functions to ensure compliance with character limits
- **Enhanced Error Handling & Validation:** Implemented comprehensive metadata validation and fallback system:
  - `validate_metadata_completeness()`: Auto-detects and fixes incomplete metadata (empty titles, descriptions, keywords)
  - Intelligent fallbacks: filename→title, title→description, auto-generated keywords from title
  - `write_to_platform_csvs_safe()`: Per-platform error handling with success threshold (minimum 3/5 platforms must succeed)
  - Graceful degradation that prevents total failure from individual platform issues

### Changed
- **Improved system reliability & backup system:**
  - Enhance and fix prompt to better suit priorities
  - Better API response validation before CSV writing
  - Removal of race conditions in multi-threaded processing
  - Individual platform error isolation
  - Self-healing metadata system with automatic fallbacks
- **Platform-Specific CSV Writing:** Refined CSV export logic with better error handling:
  - Individual try/catch blocks for each platform to prevent cascade failures
  - Detailed logging for troubleshooting platform-specific issues
  - Success/failure tracking with comprehensive reporting

### Fixed
- **Quote Escaping Issues:** Resolved double-escaping problems in TXT backup files for 123RF and Vecteezy platforms:
  - Fixed over-escaping that caused `"""description"""` instead of `"description"`
  - Implemented platform-specific formatting logic for proper CSV compliance
  - Raw data approach prevents multiple escaping passes
- **Missing Row Data:** Fixed incomplete CSV exports caused by:
  - Weak API response validation allowing partial metadata through
  - Race conditions in concurrent CSV writing operations
  - Process interruptions during stop/resume operations
  - Silent failures in metadata processing pipeline
- **Data Integrity:** Enhanced backup system validation to filter corrupted or malformed data entries

### Technical Details
- **Backup Architecture:** TXT backup system runs independently of CSV success/failure, ensuring data preservation even during partial failures
- **Smart Formatting:** Platform-specific quote handling (123RF requires quoted fields, Vecteezy conditionally quotes based on content)
- **Validation Pipeline:** Multi-stage validation ensures data completeness before writing to any output format
- **Fallback Hierarchy:** Structured fallback system with ultimate safety net of generic keywords ["image", "stock", "photo"]
---
## [3.5.1] - 2025-06-18

### Fixed
- **UnboundLocalError:** Fixed `UnboundLocalError: cannot access local variable 'is_vector_conversion' before assignment` that occurred during API requests for vector files. Resolved by adding proper parameter passing in the `_attempt_gemini_request` function.
- **Prompt Token Optimization:** Optimized all prompt formats (KUALITAS, SEIMBANG, CEPAT for Standard, PNG, and VIDEO variants) by removing bullet-point formatting and condensing text structure. This reduces token usage by approximately 60-70% while maintaining content quality, preventing false rate limit issues for vector and video files.

### Changed
- **Prompt Structure:** Streamlined all prompts to use inline formatting instead of bullet points, significantly reducing token consumption without affecting metadata quality or detail level.
---

## [3.5.0] - 2025-06-13

### Added
- **Multi-Platform CSV Export:** Added support for 3 additional stock photography platforms:
  - **123RF:** Custom CSV format with specific header quoting requirements
  - **Vecteezy:** Specialized format without filename quotes, vector keyword filtering
  - **Depositphotos:** Standard format with platform-specific fields
- **Platform-Specific Metadata Sanitization:** Implemented custom sanitization rules per platform:
  - **Adobe Stock:** Automatic period addition to titles, colon and hyphen preservation in titles/keywords
  - **Vecteezy:** Colon-to-hyphen replacement in titles, complete special character removal from keywords, automatic "vector" word filtering
  - **Other Platforms:** Maintain existing minimal sanitization for compatibility

### Changed
- **Enhanced Video Processing:** Video analysis now processes and sends 3 frames to the API instead of 1, providing more comprehensive content analysis and improved metadata accuracy
- **Improved Video Prompts:** Updated video processing prompts to handle multi-frame analysis, resulting in better title, description, and keyword generation for video content
- **Log Output Optimization:** Reduced unnecessary log messages to provide cleaner, more focused output during processing

### Technical Details
- **CSV Export Architecture:** Extended `csv_exporter.py` with specialized functions for each platform's unique requirements
- **Sanitization Functions:** Added `sanitize_adobe_stock_title()`, `sanitize_adobe_stock_keywords()`, `sanitize_vecteezy_title()`, and `sanitize_vecteezy_keywords()` for platform-specific data cleaning
- **Video Frame Processing:** Modified video processing pipeline to extract and analyze multiple frames for enhanced content understanding
---
## [3.4.0] - 2025-05-25

### Fixed
- **API Key Distribution:** Resolved an issue where API requests were not properly distributed across all available free API keys, often causing requests to concentrate on a single key (typically the first one in the list). The system now correctly rotates through all provided API keys based on their last used time, ensuring more balanced utilization and reducing premature rate limit errors on individual keys.
- **Premature Rate Limiting:** Addressed an issue where the internal rate limiter could incorrectly flag API keys or models as rate-limited sooner than the actual limits imposed by the Gemini API.

### Changed
- **Rate Limiting Strategy:** The internal token bucket-based rate limiting mechanism has been significantly revised. The program now primarily relies on the actual rate limits enforced by the Gemini API, with internal selection logic for keys and models now prioritizing the least recently used ones. Active cooldowns and token-based selection/penalties from the local rate limiter have been disabled to prevent premature limiting and to better align with Gemini's own quota management.
- **"Auto Rotasi" Model Selection:** Simplified the model selection logic when "Auto Rotasi" is active. It now solely relies on selecting the model least recently used from the `GEMINI_MODELS` list, removing dependency on internal token counts.
- **Fallback Strategy Overhaul:** The fallback mechanism, triggered when a primary model encounters a rate limit (HTTP 429) after all retries, has been enhanced:
    - It now iteratively attempts each model from the predefined `FALLBACK_MODELS` list sequentially if the prior fallback attempt also fails.
    - The primary model that initially failed due to the rate limit is automatically excluded from these fallback attempts.
    - This replaces the previous logic of selecting and trying only a single 'best' fallback model, increasing the chances of finding an available model.
---
## [3.3.2] - 2025-05-20

### Changed
- **Keyword Handling Optimized:** All keyword outputs are now always deduplicated and strictly limited to the user-specified maximum. This ensures no more over-limit or duplicate keywords, regardless of API response or file type.

### Fixed
- **Keyword Limit Bug:** Fixed an issue where the number of keywords could exceed the user-set limit (sometimes over 100) or contain duplicates, especially for vector and video files. Now, the keyword count is always enforced as intended.
---
## [3.3.1] - 2025-05-19

### Added
- **Enhanced Metadata Extraction:** Updated `_extract_metadata_from_text` function in `gemini_api.py` to include AdobeStockCategory and ShutterstockCategory in the output.

### Changed
- **Improved Keyword Handling:** Modified keyword extraction logic to exclude categories during the extraction process.
- **Enhanced CSV Export:** Improved `write_to_platform_csvs` function to better support metadata from AI results, including proper category extraction.

### Fixed
- **EXIF Writing Stability:** Fixed issues in `exif_writer.py` to enhance stability when writing metadata to different file formats.
---
## [3.3.0] - 2025-05-15 Feature Release

### Added
- **API Key Paid Option:** New checkbox in the API Key section of the UI. If enabled, users with a paid Gemini API key can use more workers than the number of API keys (removes the usual worker limit for free users). The state of this option is saved in the configuration file (`config.json`). **Note: Even with this option enabled, the maximum allowed workers is 100 for stability.**

### Changed
- **Worker Validation Logic:** When the 'API key paid?' option is enabled, the application no longer limits the number of workers to the number of API keys. This allows paid users to fully utilize their API quota and hardware, up to a maximum of 100 workers.
- **Configuration:** The state of the 'API key paid?' option is now saved and loaded automatically from `config.json` like other settings.
---
## [3.2.1] - 2025-05-13 Optimize Feature Release

### Fixed
- **API Key Checker Button:** Disable the 'Check API' button when processing starts, and reset it to enable it when the process stops or completes.
- **Log Messages:** Adjusted log messages in batch processing to reflect the current batch count accurately.
- **Log Messages:** Modified regex patterns for log message validation to align with recent changes.

---
## [3.2.0] - 2025-05-13 Optimize & Feature Release

### Added
- **API Key Checker Button:** New 'Cek API' button in the GUI to check all entered API keys at once. Results are shown in the log area, with clear OK/error summary per key.

### Changed
- **Log Filtering:** Log output from the API key checker is now visible in the GUI log (regex filter updated).

### Fixed
- **False API Limit Errors:** Removed internal rate limiter (TokenBucket) logic that was causing premature/fake API limit errors. Now, the app relies solely on Google-side quota enforcement.

### Removed
- **Internal Rate Limiter:** All TokenBucket and related cooldown logic have been removed from the codebase.

---
## [3.1.0] - 2025-05-08 Feature & BugFix Release

### Added
- **Smart API Key Selection:** Implemented logic to select the "most ready" API key based on its token bucket wait time and last usage time, replacing the previous random selection. This involves new helper functions `get_potential_wait_time` in `TokenBucket` and `select_smart_api_key` in `gemini_api.py`.
- **Fallback Model Mechanism:** If the user-selected or auto-selected API model fails due to rate limits (429) after all main retries, the system attempts one additional call using the "most ready" model from a predefined fallback list (`FALLBACK_MODELS`). This does not apply when "Auto Rotasi" mode is active. Logic handled by `select_best_fallback_model` and integrated into `_attempt_gemini_request` and `get_gemini_metadata` in `gemini_api.py`.
- **Adaptive Inter-Batch Cooldown:** The delay between processing batches now dynamically adjusts. If a high percentage (e.g., >90%) of API calls failed in the preceding batch, the next inter-batch delay is automatically set to 60 seconds to allow API RPM to recover. Otherwise, the user-defined delay is used. The delay reverts to the user-defined value if the subsequent batch (after a 60s cooldown) is successful (failure rate <90%). (`batch_processing.py`)

### Changed
- **Metadata Extraction Refactor:** The logic for extracting Title, Description, and Keywords from the API's text response has been centralized into a new helper function `_extract_metadata_from_text` within `get_gemini_metadata` (`gemini_api.py`). This eliminates code duplication for handling both primary and fallback API call results, leading to cleaner and more maintainable code.
- **API Call Logic Refactor:** The core logic for making a single attempt to the Gemini API, including error handling for specific HTTP status codes (429, 500, 503), has been refactored into the `_attempt_gemini_request` function in `gemini_api.py`.
- **`get_gemini_metadata` Overhaul:** This main function in `gemini_api.py` has been significantly reworked to utilize `_attempt_gemini_request`, manage the primary retry loop, and implement the new fallback model logic after the main loop fails due to a 429 error (only if not in "Auto Rotasi" mode).
- **API Key Handling in Processing:** `process_single_file` in `batch_processing.py` was updated to call `select_smart_api_key`. All specific file processing functions (for JPG, PNG, Video, Vector) were modified to accept a single pre-selected API key instead of a list of keys.

### Fixed
- Fixed a logical error in `wait_for_model_cooldown` (`rate_limiter.py`) where `time.time()` was incorrectly used in a `time.sleep()` context, ensuring cooldowns are applied correctly.

### Removed
- Deleted unused functions `get_gemini_metadata_with_key_rotation` and `_call_gemini_api_once` from `gemini_api.py` as their functionalities are now covered by the refactored API calling logic.

---
## [3.0.0] - 2025-05-05 Major Refactor & Feature Release

### Added
- **Model Selection:** Dropdown UI to select specific Gemini API models (e.g., `gemini-1.5-flash`, `gemini-1.5-pro`) or use "Auto Rotasi". (`src/ui/app.py`, `src/api/gemini_api.py`)
- **Keyword Count Input:** UI entry field to specify the maximum number of keywords (tags) to request from the API (min 8, max 49). (`src/ui/app.py`, `src/api/gemini_api.py`)
- **Prompt Priority:** Dropdown UI to select processing priority ("Kualitas", "Seimbang", "Cepat"). (`src/ui/app.py`)
- **Dynamic Prompts:** Implemented distinct API prompts for each priority level (Kualitas, Seimbang, Cepat) and file type (Standard, PNG/Vector, Video). (`src/api/gemini_prompts.py`, `src/api/gemini_api.py`)
- **Centralized Prompts:** Created `src/api/gemini_prompts.py` to store all prompt variations, improving maintainability.
- **Priority Logging:** Added log message to indicate which prompt priority is being used for each API request. (`src/api/gemini_api.py`)
- **UI Spacing:** Added empty labels to ensure correct visual row spacing in center/right columns. (`src/ui/app.py`)

### Changed
- **Major UI Refactor:** Removed status bar, progress bar, and associated status labels. Reorganized settings/options into a cleaner 3-column layout (Inputs Left, Dropdowns Middle, Toggles Right). (`src/ui/app.py`)
- **Prompt Management Refactor:** Moved all prompt definitions from `gemini_api.py` to the new `gemini_prompts.py` and updated imports/logic. (`src/api/gemini_api.py`, `src/api/gemini_prompts.py`)
- **Log Output:** Moved batch progress count `(x/x)` directly into the batch log message in the GUI. (`src/processing/batch_processing.py`, `src/ui/app.py`)
- **Keyword Validation:** Changed minimum allowed keyword input from 1 to 8. (`src/ui/app.py`)
- **UI Element Disabling:** Ensured new UI controls (Theme, Model, Priority dropdowns; Keyword input) are correctly disabled/enabled during processing. (`src/ui/app.py`)

### Fixed
- `NameError: name 'settings_header_tooltip' is not defined` after UI refactoring. (`src/ui/app.py`)
- UI layout not visually shifting down rows as intended (fixed by adding empty labels). (`src/ui/app.py`)

### Removed
- Status bar, progress bar, and associated UI variables (`progress_text_var`, etc.) from the main application UI. (`src/ui/app.py`)
- Redundant "Menggunakan prompt: ..." log messages for "Kualitas" priority to reduce log noise. (`src/api/gemini_api.py`)
- Old prompt definitions directly within `gemini_api.py`.

---
## [2.1.0] - 2025-05-02 Feature & BugFix Release

### Added
- **ShutterStock CSV:** Automatically set "illustration" column to "yes" for vector files (EPS, AI, SVG). (`src/metadata/csv_exporter.py`, `src/processing/batch_processing.py`)

### Changed
- **EXIF Failure Logging:** Changed log message for EXIF write failures from error (✗) to warning (⚠) and added clarification that processing continues. (`src/processing/batch_processing.py`)

### Fixed
- **EXIF Failure Handling:** Ensured processing (CSV writing, file moving) continues even if writing EXIF metadata directly to the file fails. (`src/metadata/exif_writer.py`, `src/processing/image_processing/format_jpg_jpeg_processing.py`, `src/processing/video_processing.py`)
- **Input File Deletion:** Ensured original input file is deleted after successful processing even if EXIF writing failed (consistent with normal processing). (`src/processing/batch_processing.py`)

---
## [2.0.1] - 2025-05-01 Bug Fix Release

### Fixed
- **Cropped EPS/AI Conversion:** Fixed an issue where EPS/AI files converted to JPG were getting cropped. This was resolved by adding the `-dEPSCrop` parameter to the Ghostscript command in `src/processing/vector_processing/format_eps_ai_processing.py`, ensuring Ghostscript uses the source file's BoundingBox.
- **Oversized EPS/AI Conversion Dimensions:** Fixed an issue where EPS/AI files converted to JPG resulted in pixel dimensions significantly larger than the original artboard size. This was addressed by removing the `-r300` parameter (which enforced a high DPI) from the Ghostscript command, allowing it to use the default resolution based on the BoundingBox.
- **Application Version:** Updated `APP_VERSION` constant and watermark text in `src/ui/app.py` to `2.0.1`.

---
## [2.0.0] - 2025-04-13 Major Refactor & Feature Release

This version represents a significant overhaul and feature expansion from v1.

### Added
- **Project Structure:** Reorganized into a modular `src/` directory (api, config, metadata, processing, ui, utils) for better maintainability.
- **GUI Implementation:** Introduced a user-friendly graphical interface using CustomTkinter (`src/ui/app.py`).
    - Includes folder selection, API key management (load/save/delete/hide), options (workers, delay, rename, etc.), status display, logging area, theme selection, tooltips, and completion dialog.
- **Enhanced API Integration (`src/api/`):**
    - Integrated `google-generativeai` client.
    - Implemented multi-API key rotation and multi-model rotation (e.g., `gemini-1.5-flash`, `gemini-1.5-pro`).
    - Added `TokenBucket` rate limiting for keys and models.
    - Improved API call retry logic.
- **Expanded File Processing (`src/processing/`):**
    - Added support for vectors (AI, EPS, SVG) via Ghostscript.
    - Added support for videos (MP4, MKV, AVI, MOV, MPEG, etc) via OpenCV/FFmpeg frame extraction.
- **Platform-Specific CSV Export (`src/metadata/`):**
    - Implemented category mapping for Adobe Stock & Shutterstock.
    - Generates separate, formatted CSV files.
- **Startup Dependency Checks:** Verifies ExifTool, Ghostscript, FFmpeg, GTK/cairocffi on launch with GUI logging/warnings.
- **Utility Modules (`src/utils/`):** Created helpers for system checks, analytics, file operations, etc.
- **Documentation:** Added `README.md`, `quick_guide.txt`, and this `CHANGELOG.md`.
- **Configuration:** Persistent settings saved to `config.json`.
- **Licensing Info:** Added main `LICENSE` (AGPLv3) and dependency licenses in `licenses/`.
- **Console Toggle (Windows Only):** Added UI switch and functionality to show/hide the console window.
- **Basic `.gitignore`**.

### Changed
- **Code Organization:** Major refactoring separating UI, API, processing logic.
- **Main Entry Point:** Shifted to `main.py` launching `MetadataApp`.
- **Logging:** Integrated with GUI text area.
- **Stop Handling:** Refined process interruption logic.
- **UI Switches:** Removed text labels from API Key/Console switches, added tooltips.
- **`.gitignore`:** Updated (later simplified).

### Fixed
- **Ghostscript Path Resolution:** Corrected issue where AI/EPS conversion failed in packaged builds due to worker threads not accessing the correct Ghostscript path. Implemented parameter passing for the path.
- **Logging:** Cleaned up verbose stdout debug logging from the initial Ghostscript check.

### Removed
- Removed hardcoded application expiry date check from v1.
- Removed initial mandatory Terms & Conditions dialog from v1.
- Removed standalone execution capability from `core_logic.py`.

---
## [1.0.0] - 2025-04-05 (Approximate Date) Initial Version

### Added
- First functional version combining UI (`RJ_Auto_Metadata.py`) and logic (`core_logic.py`).
- Basic image processing (JPG/PNG) with Gemini API.
- ExifTool integration for metadata writing.
- Simple UI for core functions (folders, keys, basic options).
- Basic `config.json` saving.
- Bundled ExifTool.


