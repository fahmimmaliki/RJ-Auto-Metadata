
# RJ Auto Metadata - Quick Start Guide

**Choose Your Platform:**

🟢 WINDOWS - Easy Installation (Recommended) 

🟠 WINDOWS - Source Code Installation  

🔵 macOS - Source Code Installation Only

🟣 Linux (Ubuntu) - Source Code Installation Only

## Linux (Ubuntu) - SOURCE CODE INSTALLATION ONLY
**Compatibility:** Ubuntu 20.04+ and derivatives
**Requirements:** Python 3.9+, tkinter

**QUICK SETUP:**

1. **Install system dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv python3-tk ghostscript ffmpeg exiftool libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev librsvg2-dev
   ```

2. **Clone/download source code:**
   ```bash
   git clone https://github.com/riiicil/RJ-Auto-Metadata.git
   cd RJ-Auto-Metadata
   ```

3. **Create virtual environment and install dependencies:**
   ```bash
   python3 -m venv venv
   . venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Run the app:**
   ```bash
   . venv/bin/activate
   python main.py
   ```

**Note:** The virtual environment must be activated each time you run the app.

## WINDOWS - EASY INSTALLATION
**Requirements:** Windows 10/11

1. Download latest release: https://github.com/riiicil/RJ-Auto-Metadata/releases
2. Extract the ZIP file
3. Double-click setup.exe
4. Follow installation wizard (click Next → Next → Install)
5. Launch from Start Menu: "RJ Auto Metadata"

✅ All tools (ExifTool, Ghostscript, FFmpeg) are included!
    
✅ No additional setup required!

## WINDOWS - SOURCE CODE INSTALLATION
**Requirements:** Windows 10/11, Python 3.9+

**Method 1: Quick Setup (Recommended)**
1. Download source code: https://github.com/riiicil/RJ-Auto-Metadata/archive/main.zip
2. Extract to a folder
3. Download and install external tools
4. Download and install depedencies
5. Open Command Prompt in that folder
6. Run: `python main.py`

**Method 2: Manual Setup**
1. Clone/download source code
2. Open Command Prompt in project folder
3. Run: `pip install -r requirements.txt`
4. Run: `python main.py`

**External Tools:** Install manually if not bundled:
- ExifTool: https://exiftool.org/
- Ghostscript: https://www.ghostscript.com/download/
- FFmpeg: https://ffmpeg.org/download.html

## macOS - SOURCE CODE INSTALLATION ONLY
**Compatibility:** macOS 10.14+ (Mojave and newer)
**Requirements:** Command Line Tools, Python 3.9+

**ONE-COMMAND SETUP (For most users):**

Open Terminal and run this single command:
```bash
curl -fsSL https://raw.githubusercontent.com/riiicil/RJ-Auto-Metadata/main/setup_macos.sh | bash
```

This will automatically:
- Install Homebrew (if needed)
- Install Python 3 (if needed)  
- Install external tools (Ghostscript, FFmpeg, ExifTool, Cairo)
- Install Python dependencies
- Test everything
- Ready to run!

**Then run the app:**
```bash
cd RJ_Auto_metadata
python3 main.py
```

**MANUAL SETUP (Advanced users):**

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install external tools:**
   ```bash
   brew install python@3.11 ghostscript ffmpeg exiftool cairo pango gdk-pixbuf librsvg pkg-config
   ```

3. **Get source code:**
   ```bash
   git clone https://github.com/riiicil/RJ-Auto-Metadata.git
   cd RJ_Auto_metadata
   ```

4. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

5. **Run the app:**
   ```bash
   python3 main.py
   ```

**SVG Issues Fix:** If SVG files don't work, run:
```bash
chmod +x fix_svg_macos.sh
./fix_svg_macos.sh
```

**Homebrew Compatibility:**
- macOS 10.14+ (Mojave): ✅ Full support
- macOS 10.12-10.13: ⚠️ Limited support (try MacPorts instead)
- macOS 10.11 and older: ❌ Use MacPorts or manual installation

**Alternative for older macOS:** Use MacPorts instead of Homebrew:
```bash
# Install MacPorts first from: https://www.macports.org/install.php
sudo port install ghostscript ffmpeg exiftool cairo pango
```

## GETTING GEMINI API KEY
1. Go to: https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key (starts with "AIza...")
5. Paste into the app's API Key field


## HOW TO USE
1. **Launch the app** (method depends on installation above)
2. **Select Input Folder** - Where your files are located
3. **Select Output Folder** - Where processed files will be saved (must be different)
4. **Add API Key(s)** - Paste your Gemini API key(s), one per line
5. **Adjust Settings** (optional):
   - Workers: 1-10 (more = faster, but uses more API quota)
   - Delay: 10s+ (prevents rate limiting)
   - Quality: Detailed/Balanced/Fast
   - Keywords: Max number to generate (8-49)
6. **Click "Start Processing"**
7. **Monitor progress** in the log area

## SUPPORTED FILE FORMATS
- **Images:** .jpg, .jpeg, .png
- **Videos:** .mp4, .mov, .avi, .mkv, .mpeg
- **Vectors:** .ai, .eps, .svg

**Note:** Vector and video files require external tools!


## TROUBLESHOOTING
**"External tool not found" errors:**
- Windows (installer): Should not happen
- Windows (source): Install tools manually
- macOS: Run setup script or install via Homebrew

**API errors (429, rate limit):**
- Increase delay between requests
- Reduce number of workers  
- Check API key validity
- Wait a few minutes and try again

**App won't start:**
- Check Python version: `python --version` (need 3.9+)
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- macOS: Run compatibility test: `python3 test_cross_platform.py`

**SVG files not processing (macOS):**
- Run SVG fix script: `./fix_svg_macos.sh`
- Install Cairo dependencies: `brew install cairo pango gdk-pixbuf librsvg`


## SUPPORT & MORE INFO
- **Full Documentation:** README.md 
- **Report Issues:** https://github.com/riiicil/RJ-Auto-Metadata/issues
- **Community:** https://s.id/rj_auto_metadata

**System Requirements:**
- Windows: 10/11, Python 3.9+
- macOS: 10.14+, Python 3.9+, Command Line Tools
- RAM: 4GB+ recommended
- Storage: 2GB+ free space


---

***© Riiicil 2025 | AGPL-3.0 License***

