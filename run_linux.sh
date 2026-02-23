#!/bin/bash
# Quick run script for RJ Auto Metadata on Linux
# Usage: ./run_linux.sh

echo "🐧 Starting RJ Auto Metadata on Linux..."

# Detect package manager for hints
if command -v apt-get &>/dev/null; then
    PKG_MANAGER="apt"
elif command -v dnf &>/dev/null; then
    PKG_MANAGER="dnf"
elif command -v yum &>/dev/null; then
    PKG_MANAGER="yum"
elif command -v pacman &>/dev/null; then
    PKG_MANAGER="pacman"
else
    PKG_MANAGER="unknown"
fi

if [[ ! -f "main.py" ]]; then
    echo "❌ Error: main.py not found!"
    echo "   Please run this script from the RJ Auto Metadata directory."
    echo "   Current directory: $(pwd)"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 not found!"
    echo "   Please install Python 3.9+ or run the setup script:"
    echo "   ./setup_linux.sh"
    exit 1
fi

if ! python3 -c "import customtkinter" &>/dev/null; then
    echo "⚠️ Dependencies not installed or incomplete."
    echo "🔄 Installing dependencies..."
    pip3 install -r requirements.txt || {
        echo "❌ Failed to install dependencies."
        echo "   Please run the full setup script: ./setup_linux.sh"
        exit 1
    }
fi

if [[ -d "venv" ]]; then
    echo "📦 Virtual environment detected, activating..."
    source venv/bin/activate
fi

echo "🔍 Quick system check..."
tools_ok=0
total_tools=3

if command -v gs >/dev/null 2>&1; then
    echo "  ✅ Ghostscript available"
    ((tools_ok++))
else
    echo "  ❌ Ghostscript not found (vector files may not work)"
fi

if command -v ffmpeg >/dev/null 2>&1; then
    echo "  ✅ FFmpeg available"
    ((tools_ok++))
else
    echo "  ❌ FFmpeg not found (video files may not work)"
fi

if command -v exiftool >/dev/null 2>&1; then
    echo "  ✅ ExifTool available"
    ((tools_ok++))
else
    echo "  ❌ ExifTool not found (metadata writing may not work)"
fi

if [[ $tools_ok -eq $total_tools ]]; then
    echo "🟢 All external tools ready! ($tools_ok/$total_tools)"
elif [[ $tools_ok -gt 0 ]]; then
    echo "🟡 Some tools missing ($tools_ok/$total_tools) - basic functionality available"
else
    echo "🔴 No external tools found! Only basic image processing will work."
    echo "   Run setup script to install tools: ./setup_linux.sh"
fi

# Check for display (GUI apps need X11 or Wayland)
if [[ -z "$DISPLAY" && -z "$WAYLAND_DISPLAY" ]]; then
    echo ""
    echo "⚠️ Warning: No display detected!"
    echo "   Make sure X11 or Wayland is running for the GUI to work."
    echo ""
fi

echo ""
echo "🚀 Launching RJ Auto Metadata..."
echo "   Close this terminal to stop the application"
echo ""

python3 main.py

echo ""
echo "👋 Application closed. Thanks for using RJ Auto Metadata!"
