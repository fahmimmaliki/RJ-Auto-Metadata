# RJ Auto Metadata

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://example.com/build-status) <!-- Placeholder -->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) <!-- Placeholder -->

**© Riiicil 2025**

>**New to RJ Auto Metadata?** Check out our [**Quick Start Guide**](QUICK_START_GUIDE.md) for platform-specific setup instructions!

## 1. Introduction

RJ Auto Metadata is a powerful desktop application built with Python and CustomTkinter, designed to streamline the process of adding descriptive metadata (titles, descriptions, keywords) to various media files. It now supports multiple AI providers (Google Gemini, OpenAI Responses, OpenRouter, and Groq) to analyze file content and suggest relevant metadata, which is then embedded directly into the files using the industry-standard ExifTool utility. This tool is particularly useful for photographers, videographers, graphic designers, and stock media contributors who need to manage and enrich large collections of digital assets efficiently.

**Platform Support:**
- 🟢 **Windows**: Full installer + source code support
- 🔵 **macOS**: Source code installation (with automated setup scripts)
- 🟠 **Linux**: Source code installation (manual dependency setup)

## 2. Core Features Detailed

*   **AI-Powered Metadata Generation:**
    *   Utilizes Google Gemini, OpenAI Responses, OpenRouter, or Groq for content analysis and metadata suggestion.
    *   Extracts meaningful titles, detailed descriptions, and relevant keywords based on visual or content analysis.
    *   Handles API communication, including request formatting and response parsing (`src/api/gemini_api.py`, `src/api/openai_api.py`, `src/api/openrouter_api.py`, `src/api/groq_api.py`).
*   **Multi-Provider Routing:**
    *   Provider manager allows switching between Gemini, OpenAI, OpenRouter, and Groq from the UI.
    *   Per-provider model catalogs mirror the latest public offerings, including Gemini 2.5/2.0, GPT-5/4.1, Claude 4.5/3.7, Grok 4, and Llama 4 Maverick/Scout.
    *   API key storage, validation, and request scheduling respect the active provider (`src/api/provider_manager.py`).
*   **Efficient Batch Processing:**
    *   Processes entire folders of files automatically.
    *   Uses a configurable number of parallel worker threads (`concurrent.futures.ThreadPoolExecutor`) for faster throughput (`src/processing/batch_processing.py`).
    *   **Sliding Window Submission:** Workers are never idle — as soon as one finishes, the next file is submitted immediately (replaces old batch-wait pattern).
    *   **Adaptive Worker Count:** Default worker count is automatically calculated as `N_logical_cpus × 1.5` (e.g., 24 workers on an 8-core/16-thread CPU). Can be overridden in the UI.
    *   **Thread-Safe Operations:** Supports high-concurrency processing (100+ workers, 1000+ files) with race condition prevention.
    *   **Auto Retry System:** Intelligent failure recovery that automatically retries failed files with configurable attempts per failure type (API errors: 5 attempts, file operations: 3 attempts). Includes real-time counter updates and smart retry timing.
*   **Broad File Format Compatibility:**
    *   **Images:** Processes standard formats like `.jpg`, `.jpeg`, `.png` directly (`src/processing/image_processing/`).
    *   **Vectors:** Handles `.ai`, `.eps`, and `.svg` files. Requires external tools (Ghostscript, GTK3 Runtime) for rendering/conversion before analysis (`src/processing/vector_processing/`).
    *   **Videos:** Supports `.mp4`, `.mkv`, `avi`, `mov`, `mpeg`, etc. Extracts representative frames using OpenCV and FFmpeg for analysis (`src/processing/video_processing.py`).
*   **Direct Metadata Embedding:**
    *   Integrates with the external **ExifTool** command-line utility (`tools/exiftool/`) to write standardized metadata fields into output files (`src/metadata/exif_writer.py`).
    *   **XMP-First Strategy:** Prioritizes XMP metadata for better preservation and cross-platform compatibility.
    *   **Format-Specific Support:**
        *   **JPEG (.jpg, .jpeg):** Full support (title, description, keywords) via XMP + IPTC dual embedding
        *   **Adobe Illustrator (.ai):** Partial support (title, keywords) via XMP-only strategy  
        *   **EPS (.eps):** Partial support (description, keywords) via simplified generic approach
        *   **PNG (.png):** Not supported (ExifTool limitations)
        *   **SVG (.svg):** Not supported (ExifTool limitations)
    *   **Thread-Safe CSV Export:** High-concurrency processing support with atomic operations to prevent data corruption.
*   **Extensive Customization & Configuration:**
    *   **Folder Selection:** Dedicated input and output folder paths. Ensures input/output are distinct.
    *   **API Key Management:** Text area for multiple API keys per provider (Gemini/OpenAI/OpenRouter/Groq) with automatic persistence and last-five-character masking. Supports loading/saving keys to/from `.txt` files. Option to show/hide keys in the UI.
    *   **API Key Paid Option:** New checkbox in the API Key section. If you have a paid Gemini API key, enable this option to allow the use of more workers than the number of API keys (removes the usual worker limit for free users). For free users, leave this unchecked to avoid hitting rate limits. **Note: Even with this option enabled, the maximum allowed workers is 100 for stability.**
    *   **Provider & Model Selection:** Choose Gemini, OpenAI, OpenRouter, or Groq in the dropdown, then pick a specific model (e.g., `gemini-2.5-pro`, `openai/gpt-5`, `Llama 4 Scout`). Gemini still supports automatic rotation (`Auto Rotation`).
    *   **Prompt Quality:** Select the desired trade-off between result detail and speed (`Detailed`, `Balanced`, `Less`) via a dropdown, using different underlying prompts.
        *   _Note:_ Prompt length affects API token usage. Longer prompts (`Detailed`) consume more input tokens per request, potentially hitting token limits (TPM/TPD) faster. Shorter prompts (`Less`) are more token-efficient.
    *   **Keyword Count:** Specify the maximum number of keywords to request from the API (min 8, max 49).
    *   **Performance Tuning:** Adjust the number of `Workers` and `Delay (s)` between API calls.
    *   **File Handling Options:**
        *   `Rename File?`: Automatically renames output files using the generated title.
        *   `Auto Category?`: (Experimental) Attempts to assign categories based on API results (`src/metadata/categories/`).
        *   `Auto Foldering?`: Automatically organizes output files into subdirectories (`Images`, `Vectors`, `Videos`) based on their type.
        *   `Auto Retry?`: Enables intelligent failure recovery that automatically retries failed files with smart retry logic.
        *   `Embedding`: Controls metadata embedding into files (`Enable`/`Disable`). When disabled, skips EXIF/XMP writing while still generating CSV exports.
    *   **Appearance:** Choose between `Light`, `Dark`, or `System` themes, powered by CustomTkinter.
*   **Intuitive User Interface (`src/ui/app.py`):**
    *   Built with CustomTkinter for a modern look and feel.
    *   Clear sections for folder selection, API keys, and a refined 3-column layout for options (Inputs Left, Dropdowns Middle, Toggles Right).
    *   Real-time detailed logging area showing processing steps, successes, failures, warnings, and batch progress `(x/x)`.
    *   Removed visual status bar; all progress feedback is now in the log.
    *   Tooltips (?) provide help for various settings and buttons.
    *   Completion dialog summarizes the results after processing.
*   **Persistent Settings:**
    *   Automatically saves user configuration (folders, keys, options, theme) to `config.json` upon closing or successful processing. Typically located in `Documents/RJAutoMetadata` on Windows (`src/config/config.py`).
    *   Maintains a `processed_cache.json` to potentially track processed files (current usage might be limited).
*   **Robust Error Handling & Logging:**
    *   Provides informative messages in the log for various events, including API errors, file processing issues, and missing dependencies.
    *   Graceful handling of process interruption (`Stop` button).
    *   Logs messages with timestamps and severity tags (Info, Warning, Error, Success).

*   **Optional Usage Analytics:**
      Can send anonymous data (like OS version, event counts, success rates) using Google Analytics Measurement Protocol to help the developer improve the application (`src/utils/analytics.py`). Associated with a unique, anonymous `installation_id`. Can be implicitly disabled by not having Measurement ID/API Secret configured at build time (or potentially via a future setting).
*   **Console Visibility Toggle (Windows Only):**
      Provides a switch in the UI to **minimize/restore** the underlying console window (`RJ Auto Metadata.exe`). This is useful for temporarily hiding the console while keeping detailed logs accessible. Visibility state is saved in the configuration.
   *   **Alternative No-Console Executable:** For users who prefer **no console window at all**, a second executable (`RJ Auto Metadata No Console.exe`) is included in the installation directory (e.g., `C:\Program Files (x86)\RJ Auto Metadata`). Running this file directly will launch the application without an initial console window.
## 3. Workflow Overview

The application follows these general steps during processing:

1.  **Initialization:** User launches the application (`main.py`), initializing the UI (`src/ui/app.py`). Settings load from `config.json`.
2.  **Configuration:** User selects Input/Output folders, chooses an AI provider, supplies the corresponding API keys, and adjusts processing options.
3.  **Start Process:** User clicks "Mulai Proses".
4.  **Validation:** Application validates inputs (folders, keys, settings).
5.  **File Discovery:** Scans the Input Folder for supported file types (`src/utils/file_utils.py`).
6.  **Batch Processing (`src/processing/batch_processing.py`):**
    *   Creates a thread pool (`Workers`).
    *   Distributes files to worker threads.
    *   Each worker:
        *   **Preprocessing:** Converts/extracts data (video frames, vector rendering). Handles compression (`src/utils/compression.py`).
        *   **API Call:** Selects the smartest API key, sends data to Gemini API (respecting base `Delay` and adaptive cooldowns, utilizing fallback models if necessary) (`src/api/gemini_api.py`, `src/api/rate_limiter.py`).
        *   **Metadata Extraction:** Parses Gemini response.
        *   **File Copying:** Copies original to Output Folder (optional subfolders).
        *   **Metadata Writing:** Calls ExifTool to embed metadata (`src/metadata/exif_writer.py`).
        *   **Renaming (Optional):** Renames output file.
        *   **Categorization (Optional):** Applies category logic (`src/metadata/categories/`).
        *   **Logging & Progress:** Reports status to UI.
7.  **Completion:** Summary message displayed, UI re-enabled. Settings/cache saved.


## 4. System Requirements

### 4.1. Python Environment

*   **Python 3.x:** (Recommended: 3.9 or newer)
*   **pip:** For installing dependencies.
*   **Required Python Packages:** Install via `pip install -r requirements.txt`. Key packages:
    *   `customtkinter>=5.2.2` (GUI)
    *   `Pillow>=11.1.0` (Images)
    *   `google-genai>=1.25.0` (Gemini API with thinking models support)
    *   `requests>=2.32.3` (HTTP)
    *   `opencv-python>=4.11.0.86` (Video Frames - needs FFmpeg)
    *   `svglib>=1.5.1`, `reportlab>=4.3.1`, `CairoSVG>=2.7.1` (SVG - needs GTK3)
    *   `portalocker>=3.1.1` (Optional File Locking)
    *   *Plus other dependencies.*

### 4.2. External Tools & Libraries Dependencies

The application relies on several external command-line tools for full functionality:

1.  **ExifTool:** Reads/writes metadata (EXIF, IPTC, XMP). **(Bundled)**
2.  **Ghostscript:** Needed for `.eps` and `.ai` file analysis/conversion. **(Bundled)**
3.  **FFmpeg:** Needed by OpenCV for `.mp4`, `.mkv`, `avi`, `mov`, `mpeg`, `etc` frame reading. **(Bundled)**
4.  **GTK3 Runtime (Windows Only):** Needed by CairoSVG for SVG rendering. **(Handled by Installer)**

*   **For users of the provided `.exe` installer:**
    *   ExifTool, Ghostscript, and FFmpeg are **included** within the `tools/` directory of the installation and should work automatically.
    *   The installer will attempt to run the **GTK3 Runtime installer** separately during setup. You need to accept its installation for SVG support.
*   **For users running from source code:**
    *   You **must install ExifTool, Ghostscript, FFmpeg, and GTK3 Runtime manually** and ensure they are accessible in your system's PATH.
    *   Download links:
        *   ExifTool: [https://exiftool.org/](https://exiftool.org/)
        *   Ghostscript: [https://www.ghostscript.com/releases/gsdnld.html](https://www.ghostscript.com/releases/gsdnld.html)
        *   FFmpeg: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
        *   GTK3 (Win): [GTK for Windows Runtime Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)

**Failure of these tools WILL cause errors for vector/video files!**

### 4.3. Hardware Acceleration (Optional but Recommended)

RJ Auto Metadata automatically detects and uses available hardware acceleration:

*   **GPU via OpenCL (AMD/Intel/NVIDIA):**
    *   Image resize during compression is offloaded to the GPU using OpenCV's `cv2.UMat` (transparent OpenCL).
    *   Confirmed working on AMD Radeon RX 6600 (gfx1032) and AMD Radeon Vega integrated graphics.
    *   No extra installation needed — OpenCV includes OpenCL support by default.
    *   Falls back to CPU (Pillow LANCZOS) automatically if OpenCL is unavailable.
*   **libjpeg-turbo (SIMD-accelerated JPEG):**
    *   Pillow uses libjpeg-turbo for hardware-accelerated JPEG encode/decode when available.
    *   Verify with: `python3 -c "from PIL import features; print(features.check_feature('libjpeg_turbo'))"`
*   **Adaptive Worker Count:**
    *   The default number of workers is automatically set to `N_logical_cpus × 1.5` (e.g., 24 on a 16-thread CPU).
    *   This follows the Python recommendation for I/O-bound thread pools.
    *   You can override this in the Workers field in the UI.

## 5. Installation Guide

There are two main ways to install and run RJ Auto Metadata: using the provided installer or running directly from the source code.

### 5.1. Using the Installer (.exe) (Recommended for most users)

This is the easiest way to get started on Windows.

1.  **Download Installer:** Go to the [Releases page](https://github.com/riiicil/RJ-Auto-Metadata/releases) on GitHub. Download the `v3.x.x.zip` file from the latest release assets.
2.  **Extract and run Installer:** Double-click the downloaded `setup.exe`.
3.  **Follow Prompts:** Follow the on-screen instructions provided by the installer. It will guide you through the process, including installing necessary components like the GTK3 Runtime (required for SVG files). Accept the prompts to install these components when asked.
4.  **Launch:** Once installation is complete, you can launch RJ Auto Metadata from the Start Menu shortcut or the optional desktop icon.

### 5.2. Running from Source Code (For developers or advanced users)
Follow these steps if you want to run the application directly using Python:

1.  **Clone Repository (Optional):**
    ```bash
    git clone https://github.com/riiicil/RJ-Auto-Metadata.git
    cd RJ-Auto-Metadata
    ```
    (Or download & extract the source code ZIP from the repository page).
2.  **Setup Python Environment (Recommended):** Create and activate a virtual environment.
    ```bash
    python -m venv venv
    # Windows: .\venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```
3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Install ALL External Tools Manually:** You **must** install ExifTool, Ghostscript, FFmpeg, and (on Windows) GTK3 Runtime yourself and ensure they are correctly added to your system's PATH. Refer to the download links in section [4.2. External Tools & Libraries Dependencies](#42-external-tools--libraries-dependencies). Verify each tool is working via your terminal (e.g., `exiftool -ver`, `gswin64c -version`, `ffmpeg -version`).
5.  **Run the Application:**
    ```bash
    python main.py
    ```

### 5.3. Linux (Ubuntu) Installation

For Ubuntu and Ubuntu-based distributions, follow these steps:

1.  **Install System Dependencies:**
    ```bash
    sudo apt update
    sudo apt install python3 python3-pip python3-venv python3-tk ghostscript ffmpeg exiftool libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev librsvg2-dev
    ```

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/riiicil/RJ-Auto-Metadata.git
    cd RJ-Auto-Metadata
    ```

3.  **Create Virtual Environment and Install Dependencies:**
    ```bash
    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements.txt
    ```

4.  **Run the Application:**
    ```bash
    . venv/bin/activate
    python main.py
    ```

**Note:** The virtual environment must be activated each time you run the application. You can also create a desktop shortcut or alias for convenience.

## 6. Configuration Details

### 6.1. `config.json`

Stores settings automatically (usually in `Documents/RJ Auto Metadata` on Windows).
*   `input_dir`, `output_dir`: Folder paths.
*   `delay`, `workers`: Performance settings.
*   `rename`, `auto_kategori`, `auto_foldering`: File handling toggles (booleans).
*   `api_keys`: Stored per provider (Gemini, OpenAI, OpenRouter, Groq) as entered via the UI.
*   `provider`: Last used provider (e.g., "Gemini", "OpenAI", "OpenRouter", "Groq").
*   `model`: Selected API model for the active provider (e.g., "gemini-2.5-pro", "openai/gpt-5").
*   `priority`: Selected prompt priority ("Detailed", "Balanced", "Less").
*   `keyword_count`: Maximum keywords requested (string, e.g., "49").
*   `theme`: "light", "dark", or "system".
*   `installation_id`: Anonymous analytics ID.
*   `analytics_enabled`: Analytics toggle state.

### 6.2. UI Settings

*   **Input/Output Folders:** Must be valid, different directories.
*   **API Keys:** One key per line. Load/Save/Delete/Show-Hide options available.
*   **Keywords:** Max keywords from API (8-49).
*   **Workers:** Threads (1-10+). More workers = faster, but more API usage. (Paid users can use more workers by enabling the checkbox above, up to a maximum of 100.)
*   **Delay (s):** Pause between API calls per worker (avoids rate limits).
*   **Theme:** Visual style selection.
*   **Models:** Select specific models for request.
*   **Quality:** Choose prompt detail level (Detailed/Balanced/Less).
*   **Rename File?:** Renames output file to `Generated Title.ext`.
*   **Auto Category?:** Applies experimental categories.
*   **Auto Foldering?:** Sorts output into `Images/`, `Vectors/`, `Videos/`.
*   **Auto Retry?:** Enables automatic retry of failed files with intelligent failure recovery.
*   **Embedding:** Controls metadata embedding (`Enable`/`Disable`). Skips EXIF writing when disabled.

### 6.3. Analytics

*   Uses Google Analytics (Measurement Protocol) for anonymous usage stats if configured at build time (`src/config/config.py`).
*   Helps improve the app. Sends OS info, event counts, success rates. **No personal data or file content is sent.**

## 7. Usage Guide

1.  **Launch:**
    *   Run `python main.py` (if running from source).
    *   Use the desktop/start menu shortcut, which points to `RJ Auto Metadata.exe` (includes a console window that can be minimized/restored via the UI toggle).
    *   *Optional:* If you prefer no console window, navigate to the installation directory and run `RJ Auto Metadata No Console.exe` directly.
2.  **Set Folders:** Use "Browse" for **Input** & **Output** directories (must be different!).
3.  **Enter API Keys:** Paste keys (one per line) or use "Load". 
4.  **Adjust Settings (Optional):** Tune `Keywords`, `Workers`, `Delay`, `Theme`, `Models`, `Quality`, Toggles (`Rename?`, etc.).
5.  **Initiate Processing:** Click **"Start Processing"**. Buttons will update state.
6.  **Monitor:** Watch the **"Logs"** area for detailed steps, batch progress `(x/x)`, success/failure messages.
7.  **Interrupt (Optional):** Click **"Stop"** to stop gracefully (may take a moment).
8.  **Review Results:** Check summary dialog & Output Folder for processed files.
9.  **Clear Log (Optional):** Click **"Clear Log"** for a clean slate.
10. **Exit:** Close window (settings save automatically).

## 8. Provider Rate Limits

Each provider enforces its own request and token quotas. Always size your worker count, delay, and key pool with these limits in mind to avoid repeated HTTP 429 responses.

### 8.1. Google Gemini

When using the Google Gemini API, usage is subject to several rate limits that apply per Google Cloud project. Exceeding any dimension will block further requests until the budget recovers.

**Rate limits are measured across four main dimensions:**

- **Requests per minute (RPM):** Maximum number of API requests allowed per minute.
- **Requests per day (RPD):** Maximum number of API requests allowed per day.
- **Tokens per minute (TPM):** Maximum number of tokens processed per minute.
- **Tokens per day (TPD):** Maximum number of tokens processed per day.

Each dimension is evaluated independently. If you exceed one (for example, RPM), further requests will be blocked even if the other limits are still available.

**Limits vary by model and may change over time.** Example (free tier) values:

| Model                              | RPM | TPM      | RPD  |
|------------------------------------|-----|----------|------|
| Gemini 2.5 Flash                   | 10  | 250,000  | 500  |
| Gemini 2.5 Flash-Lite              | 15  | 250,000  | 500  |
| Gemini 2.5 Pro                     | 5   | 250,000  | 25   |
| Gemini 2.0 Flash                   | 15  | 1,000,000| 1,500|
| Gemini 2.0 Flash-Lite              | 30  | 1,000,000| 1,500|

> **Note:** Rate limits are stricter for experimental or preview models. Consult the [official Gemini API documentation](https://ai.google.dev/gemini-api/docs/rate-limits) for current quotas. RJ Auto Metadata includes Smart API Key Selection, Adaptive Inter-Batch Cooldown, and a fallback model system to help balance throughput, but configuring sensible worker counts and delays remains essential.

### 8.2. OpenAI Responses

OpenAI applies per-minute and per-day quotas that depend on your account tier and the specific model family (GPT-5 vs GPT-4.1 vs GPT-4o). Track your usage in the [OpenAI usage dashboard](https://platform.openai.com/usage) and review the [rate limit guide](https://platform.openai.com/docs/guides/rate-limits) for the latest allowances. RJ Auto Metadata respects the same retry/backoff logic used for Gemini but cannot override account-level caps.

### 8.3. OpenRouter

OpenRouter proxies multiple upstream providers. Your effective limits depend on both OpenRouter's own quotas and the limits imposed by the selected routed model (e.g., Anthropic, Google, xAI). Monitor usage through the [OpenRouter dashboard](https://openrouter.ai/dashboard) and consult the [OpenRouter rate limits article](https://openrouter.ai/docs/rate-limits). When possible, rotate multiple API keys or select models with more generous quotas to maintain throughput.

### 8.4. Groq

Groq offers high-speed inference with generous free-tier limits for supported models.

- **Developer/Free Plan Limits (Typical):**
  - **Llama 4 Vision Models (Scout/Maverick):** ~30 RPM, 1,000 RPD, ~6,000-30,000 TPM.
  - **Text-Only Models:** Higher limits (e.g., 30 RPM, 14.4K RPD for Llama 3.1 8B).
- **Rate Limit Handling:** The application handles `429 Too Many Requests` errors with automatic backoff.
- **Vision Support:** Groq's Llama 4 preview models support direct image input for metadata generation.


## 9. Supported File Formats

*   **Images:** `.jpg`, `.jpeg`, `.png`
*   **Vectors:** `.ai`, `.eps` (Need Ghostscript), `.svg` (Need Ghostscript & GTK3)
*   **Videos:** `.mp4`, `.mov`, `etc` (Need FFmpeg)

*Processing vectors/videos WILL FAIL without the required external tools!*

## 10. Multi-Platform CSV Export

RJ Auto Metadata automatically generates CSV files optimized for **5 major stock photography platforms**, making it easy to upload your processed media with proper metadata formatting:

### 10.1. Supported Platforms

*   **Adobe Stock** (`adobe_stock_export.csv`)
    *   Format: Filename, Title, Keywords, Category, Releases
    *   Features: Automatic period addition to titles, colon and hyphen preservation
    *   Category mapping: Numeric IDs (1-21) based on content analysis

*   **Shutterstock** (`shutterstock_export.csv`)
    *   Format: Filename, Description, Keywords, Categories, Editorial, Mature content, Illustration
    *   Features: Automatic "illustration" flag for vector files (EPS, AI, SVG)
    *   Category mapping: Text-based categories (e.g., "Abstract", "Animals/Wildlife")

*   **123RF** (`123rf_export.csv`)
    *   Format: oldfilename, "123rf_filename", "description", "keywords", "country"
    *   Features: Custom header quoting, country field set to "ID"
    *   Special formatting: Specific quote placement for platform compatibility

*   **Vecteezy** (`vecteezy_export.csv`)
    *   Format: Filename, Title, Description, Keywords, License, Id
    *   Features: Filename without quotes, automatic "vector" keyword filtering
    *   Sanitization: Colon-to-hyphen replacement, special character removal
    *   License: Automatically set to "pro"

*   **Depositphotos** (`depositphotos_export.csv`)
    *   Format: Filename, Title, Description, Keywords, Category, Nudity, Editorial
    *   Features: Standard formatting with platform-specific fields
    *   Default values: Nudity and Editorial set to "no"

*   **Miri Canvas** (`miri_canvas_export.csv`)
    *   Format: fileName, uniqueId, elementName, keywords, tier, contentType
    *   Features: Custom header quoting, tier set to "Premium"
    *   Special formatting: Specific quote placement for platform compatibility

### 10.2. Platform-Specific Features

**Smart Sanitization:** Each platform has custom data cleaning rules:
*   **Adobe Stock:** Preserves colons and hyphens in titles/keywords
*   **Vecteezy:** Removes "vector" words from keywords, replaces colons with hyphens
*   **Others:** Minimal sanitization for maximum compatibility

**Automatic Categorization:** When "Auto Category?" is enabled, the AI analyzes content and assigns appropriate categories for Adobe Stock and Shutterstock.

**Vector Detection:** Automatically detects vector files and applies appropriate flags (e.g., Shutterstock's "illustration" field).

### 10.3. CSV Output Location

All CSV files are generated in your specified **Output Folder** and updated in real-time as files are processed. Each platform gets its own dedicated CSV file for easy bulk uploading.

## 11. Troubleshooting Common Issues

*   **"Exiftool not found" / Errors on `.ai`/`.eps` / Errors on `.mp4`/`.mov`:**
    *   **Using Installer:** These tools should be bundled. Ensure the installation completed without errors and the `tools/` subfolder exists with content. Check the application log for specific errors during execution.
    *   **Running from Source:** The respective tool (ExifTool, Ghostscript, FFmpeg) is likely not installed correctly or its location is not included in the system's PATH environment variable. Reinstall the tool or add it to your PATH.
*   **Errors on `.svg` (Windows):**
    *   **Using Installer:** The GTK3 Runtime installation might have failed or been skipped during setup. Try running the GTK3 installer found within the application's temporary setup files (if available) or download and install it manually.
    *   **Running from Source:** GTK3 Runtime is missing or misconfigured. Install GTK3 Runtime.
*   **Permission Errors:** Cannot write to Output Folder or config location? Choose different folder, check permissions.
*   **Freezes/Crashes:** Review the GUI log carefully for any error messages. Since the terminal output is suppressed, the GUI log is the primary source of information. Ensure all dependencies (Python and external) are correctly installed. If the log provides no clues, consider system resource issues or try reducing the number of `Workers`.

## 12. Project Structure Deep Dive

*   `main.py`: Entry point.
*   `src/`: Core logic.
    *   `api/`: API interactions.
    *   `config/`: Settings load/save.
    *   `metadata/`: ExifTool writing, categories.
    *   `processing/`: Batch logic, format handlers.
    *   `ui/`: CustomTkinter GUI.
    *   `utils/`: Helpers.
*   `tools/`: Bundled tools.
*   `assets/`: Icons, etc.
*   `licenses/`: Dependency licenses.
*   `sample_files/`: Test files.

## 13. License Information

Licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. See `LICENSE` file.

*   **Freedom:** Use, modify, distribute.
*   **Share Alike:** Modified source code must also be AGPLv3.
*   **Network Use:** If run modified on a server, users interacting remotely must get source code access.

Dependencies have their own licenses (MIT, Apache, LGPL, etc.). See `licenses/` folder. Comply with all, especially for external tools (ExifTool, Ghostscript, FFmpeg, GTK3).

## 14. Contributing

This is currently a solo project and my first one! As such, I'm focusing on learning and building. While I'm not set up for formal contributions right now, I'm always open to hearing feedback or suggestions. You can reach out via the contact details below (if provided).

## 15. Contact & Support

You can find me and discuss this project (or others) at: https://s.id/riiicil

## 16. Support the Project

If you find this application helpful and would like to support its continued development, you can do so via the QR code below. Thanks!

![Support QR Code](assets/qr.jpg)

---
