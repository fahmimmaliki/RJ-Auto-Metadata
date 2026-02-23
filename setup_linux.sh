#!/bin/bash
# =============================================================================
# RJ Auto Metadata — One-Command Linux Setup Script
# Supports: Ubuntu/Debian, Fedora/RHEL/CentOS, Arch Linux, openSUSE
#
# Usage (from project directory):
#   chmod +x setup_linux.sh && ./setup_linux.sh
#
# Or one-liner (downloads and runs):
#   curl -fsSL https://raw.githubusercontent.com/fahmimmaliki/RJ-Auto-Metadata/main/setup_linux.sh | bash
# =============================================================================

set -e

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

ok()   { echo -e "  ${GREEN}✅ $*${NC}"; }
warn() { echo -e "  ${YELLOW}⚠️  $*${NC}"; }
err()  { echo -e "  ${RED}❌ $*${NC}"; }
info() { echo -e "  ${CYAN}ℹ️  $*${NC}"; }
step() { echo -e "\n${BOLD}${BLUE}▶ $*${NC}"; }

# ── Header ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       RJ Auto Metadata — Linux One-Command Setup         ║"
echo "║              v3.12.0 | © Riiicil 2025                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── OS Detection ─────────────────────────────────────────────────────────────
step "Detecting Linux distribution..."

DISTRO=""
PKG_MANAGER=""
INSTALL_CMD=""
UPDATE_CMD=""

if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_ID="${ID:-unknown}"
    DISTRO_LIKE="${ID_LIKE:-}"
    DISTRO_NAME="${PRETTY_NAME:-Linux}"
else
    DISTRO_ID="unknown"
    DISTRO_NAME="Unknown Linux"
fi

# Detect package manager
if command -v apt-get &>/dev/null; then
    PKG_MANAGER="apt"
    UPDATE_CMD="sudo apt-get update -qq"
    INSTALL_CMD="sudo apt-get install -y"
elif command -v dnf &>/dev/null; then
    PKG_MANAGER="dnf"
    UPDATE_CMD="sudo dnf check-update -q || true"
    INSTALL_CMD="sudo dnf install -y"
elif command -v yum &>/dev/null; then
    PKG_MANAGER="yum"
    UPDATE_CMD="sudo yum check-update -q || true"
    INSTALL_CMD="sudo yum install -y"
elif command -v pacman &>/dev/null; then
    PKG_MANAGER="pacman"
    UPDATE_CMD="sudo pacman -Sy --noconfirm"
    INSTALL_CMD="sudo pacman -S --noconfirm --needed"
elif command -v zypper &>/dev/null; then
    PKG_MANAGER="zypper"
    UPDATE_CMD="sudo zypper refresh -q"
    INSTALL_CMD="sudo zypper install -y"
else
    err "No supported package manager found (apt/dnf/yum/pacman/zypper)"
    err "Please install dependencies manually. See README.md §5.3"
    exit 1
fi

info "Distribution: $DISTRO_NAME"
info "Package manager: $PKG_MANAGER"
info "Architecture: $(uname -m)"
info "Kernel: $(uname -r)"

# ── Helper: check if command exists ──────────────────────────────────────────
command_exists() { command -v "$1" &>/dev/null; }

# ── Helper: install packages with the detected manager ───────────────────────
pkg_install() {
    local packages=("$@")
    echo "  Installing: ${packages[*]}"
    $INSTALL_CMD "${packages[@]}" 2>&1 | tail -3 || warn "Some packages may have failed"
}

# ── Step 1: Update package index ─────────────────────────────────────────────
step "Updating package index..."
$UPDATE_CMD || warn "Package index update failed, continuing..."
ok "Package index updated"

# ── Step 2: Install system dependencies ──────────────────────────────────────
step "Installing system dependencies..."

case "$PKG_MANAGER" in
    apt)
        pkg_install \
            python3 python3-pip python3-venv python3-tk python3-dev \
            ghostscript ffmpeg libimage-exiftool-perl \
            libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev \
            librsvg2-dev libffi-dev libssl-dev \
            build-essential pkg-config git curl wget \
            libjpeg-turbo8-dev libpng-dev \
            ocl-icd-opencl-dev opencl-headers
        # Try to install ROCm OpenCL for AMD GPUs (optional, non-fatal)
        if lspci 2>/dev/null | grep -qi "AMD\|ATI\|Radeon"; then
            info "AMD GPU detected — attempting to install ROCm OpenCL runtime..."
            pkg_install rocm-opencl-runtime 2>/dev/null || \
            pkg_install mesa-opencl-icd 2>/dev/null || \
            warn "ROCm/Mesa OpenCL not installed — GPU acceleration will be unavailable"
        fi
        ;;
    dnf|yum)
        pkg_install \
            python3 python3-pip python3-tkinter python3-devel \
            ghostscript ffmpeg perl-Image-ExifTool \
            cairo-devel pango-devel gdk-pixbuf2-devel \
            librsvg2-devel libffi-devel openssl-devel \
            gcc gcc-c++ make pkgconfig git curl wget \
            libjpeg-turbo-devel libpng-devel \
            ocl-icd-devel opencl-headers
        if lspci 2>/dev/null | grep -qi "AMD\|ATI\|Radeon"; then
            info "AMD GPU detected — attempting to install Mesa OpenCL..."
            pkg_install mesa-libOpenCL 2>/dev/null || \
            warn "Mesa OpenCL not installed — GPU acceleration will be unavailable"
        fi
        ;;
    pacman)
        pkg_install \
            python python-pip tk \
            ghostscript ffmpeg perl-image-exiftool \
            cairo pango gdk-pixbuf2 \
            librsvg libffi openssl \
            base-devel pkgconf git curl wget \
            libjpeg-turbo libpng \
            ocl-icd opencl-headers
        if lspci 2>/dev/null | grep -qi "AMD\|ATI\|Radeon"; then
            info "AMD GPU detected — attempting to install ROCm OpenCL..."
            pkg_install rocm-opencl-runtime 2>/dev/null || \
            pkg_install opencl-mesa 2>/dev/null || \
            warn "ROCm/Mesa OpenCL not installed — GPU acceleration will be unavailable"
        fi
        ;;
    zypper)
        pkg_install \
            python3 python3-pip python3-tk python3-devel \
            ghostscript ffmpeg exiftool \
            cairo-devel pango-devel gdk-pixbuf-devel \
            librsvg-devel libffi-devel libopenssl-devel \
            gcc gcc-c++ make pkg-config git curl wget \
            libjpeg8-devel libpng16-devel \
            ocl-icd-devel opencl-headers
        ;;
esac

ok "System dependencies installed"

# ── Step 3: Verify Python ─────────────────────────────────────────────────────
step "Checking Python version..."

PYTHON_CMD=""
for cmd in python3.12 python3.11 python3.10 python3.9 python3; do
    if command_exists "$cmd"; then
        ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -eq 3 ] && [ "$minor" -ge 9 ]; then
            PYTHON_CMD="$cmd"
            ok "Python $ver found at $(command -v $cmd)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    err "Python 3.9+ not found. Please install Python 3.9 or newer."
    case "$PKG_MANAGER" in
        apt)   info "Try: sudo apt-get install python3.12" ;;
        dnf)   info "Try: sudo dnf install python3.12" ;;
        pacman) info "Try: sudo pacman -S python" ;;
        zypper) info "Try: sudo zypper install python312" ;;
    esac
    exit 1
fi

# ── Step 4: Get project source ────────────────────────────────────────────────
step "Locating project source..."

if [ -f "main.py" ] && [ -f "requirements.txt" ]; then
    ok "Already in RJ Auto Metadata project directory: $(pwd)"
    PROJECT_DIR="$(pwd)"
else
    info "Downloading RJ Auto Metadata source code..."
    REPO_URL="https://github.com/fahmimmaliki/RJ-Auto-Metadata.git"
    if command_exists git; then
        git clone "$REPO_URL" RJ-Auto-Metadata
        PROJECT_DIR="$(pwd)/RJ-Auto-Metadata"
    else
        warn "git not found, downloading ZIP..."
        curl -L -o rj-auto-metadata.zip \
            "https://github.com/fahmimmaliki/RJ-Auto-Metadata/archive/main.zip"
        unzip -q rj-auto-metadata.zip
        mv RJ-Auto-Metadata-main RJ-Auto-Metadata
        PROJECT_DIR="$(pwd)/RJ-Auto-Metadata"
        rm rj-auto-metadata.zip
    fi
    cd "$PROJECT_DIR"
    ok "Source code downloaded to: $PROJECT_DIR"
fi

# ── Step 5: Create virtual environment ───────────────────────────────────────
step "Setting up Python virtual environment..."

VENV_DIR="$PROJECT_DIR/venv"

if [ -d "$VENV_DIR" ]; then
    ok "Virtual environment already exists at $VENV_DIR"
else
    $PYTHON_CMD -m venv "$VENV_DIR"
    ok "Virtual environment created at $VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python3"
VENV_PIP="$VENV_DIR/bin/pip"

# ── Step 6: Install Python dependencies ──────────────────────────────────────
step "Installing Python dependencies..."

"$VENV_PIP" install --upgrade pip setuptools wheel -q
ok "pip/setuptools/wheel upgraded"

if "$VENV_PIP" install -r "$PROJECT_DIR/requirements.txt"; then
    ok "All requirements installed successfully"
else
    warn "Some requirements failed. Trying individual installation..."
    for pkg in cairocffi cairosvg svglib reportlab; do
        "$VENV_PIP" install --no-cache-dir "$pkg" 2>/dev/null || warn "$pkg failed (SVG support may be limited)"
    done
    "$VENV_PIP" install -r "$PROJECT_DIR/requirements.txt" || warn "Some packages may still be missing"
fi

# ── Step 7: Verify external tools ────────────────────────────────────────────
step "Verifying external tools..."

TOOLS_OK=true

if command_exists gs; then
    gs_ver=$(gs --version 2>/dev/null | head -1)
    ok "Ghostscript: $gs_ver"
else
    err "Ghostscript not found — .eps and .ai files will NOT work"
    TOOLS_OK=false
fi

if command_exists ffmpeg; then
    ff_ver=$(ffmpeg -version 2>/dev/null | head -1 | awk '{print $3}')
    ok "FFmpeg: $ff_ver"
else
    err "FFmpeg not found — video files will NOT work"
    TOOLS_OK=false
fi

if command_exists exiftool; then
    et_ver=$(exiftool -ver 2>/dev/null)
    ok "ExifTool: $et_ver"
else
    err "ExifTool not found — metadata embedding will NOT work"
    TOOLS_OK=false
fi

# ── Step 8: Verify Python packages ───────────────────────────────────────────
step "Verifying Python packages..."

"$VENV_PYTHON" -c "
import sys
results = []

packages = {
    'customtkinter': 'GUI',
    'PIL': 'Image processing (Pillow)',
    'cv2': 'Video processing (OpenCV)',
    'requests': 'HTTP client',
    'portalocker': 'File locking',
}

for pkg, desc in packages.items():
    try:
        __import__(pkg)
        print(f'  ✅ {desc}')
    except ImportError:
        print(f'  ❌ {desc} — MISSING')

# Check libjpeg-turbo
try:
    from PIL import features
    turbo = features.check_feature('libjpeg_turbo')
    print(f'  {\"✅\" if turbo else \"⚠️ \"} libjpeg-turbo SIMD: {\"enabled\" if turbo else \"not available\"}')
except Exception:
    pass

# Check OpenCL
try:
    import cv2
    has_ocl = cv2.ocl.haveOpenCL()
    if has_ocl:
        cv2.ocl.setUseOpenCL(True)
        dev = cv2.ocl.Device.getDefault().name()
        print(f'  ✅ OpenCL GPU acceleration: {dev}')
    else:
        print('  ⚠️  OpenCL not available — CPU-only image processing')
except Exception as e:
    print(f'  ⚠️  OpenCL check failed: {e}')
" 2>/dev/null || warn "Package verification had issues"

# ── Step 9: Create run script ─────────────────────────────────────────────────
step "Creating run script..."

RUN_SCRIPT="$PROJECT_DIR/run_linux.sh"
cat > "$RUN_SCRIPT" << RUNEOF
#!/bin/bash
# RJ Auto Metadata — Linux Run Script
# Generated by setup_linux.sh

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="\$SCRIPT_DIR/venv/bin/python3"

if [ ! -f "\$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found. Please run setup_linux.sh first."
    exit 1
fi

echo "🚀 Starting RJ Auto Metadata..."
cd "\$SCRIPT_DIR"
"\$VENV_PYTHON" main.py "\$@"
RUNEOF

chmod +x "$RUN_SCRIPT"
ok "Run script created: $RUN_SCRIPT"

# ── Step 10: Create desktop shortcut (optional) ───────────────────────────────
step "Creating desktop shortcut (optional)..."

DESKTOP_DIR="$HOME/Desktop"
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"

ICON_PATH="$PROJECT_DIR/assets/icon1.ico"
DESKTOP_FILE="$APPS_DIR/rj-auto-metadata.desktop"

cat > "$DESKTOP_FILE" << DESKEOF
[Desktop Entry]
Version=1.0
Type=Application
Name=RJ Auto Metadata
Comment=AI-powered metadata generator for stock media
Exec=$RUN_SCRIPT
Icon=$ICON_PATH
Terminal=false
Categories=Graphics;Photography;
StartupNotify=true
DESKEOF

chmod +x "$DESKTOP_FILE"
ok "Application shortcut created: $DESKTOP_FILE"

# Copy to Desktop if it exists
if [ -d "$DESKTOP_DIR" ]; then
    cp "$DESKTOP_FILE" "$DESKTOP_DIR/rj-auto-metadata.desktop" 2>/dev/null && \
    chmod +x "$DESKTOP_DIR/rj-auto-metadata.desktop" && \
    ok "Desktop shortcut created: $DESKTOP_DIR/rj-auto-metadata.desktop" || \
    warn "Could not create desktop shortcut"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════╗"
echo "║                  Setup Complete! 🎉                      ║"
echo -e "╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}To run RJ Auto Metadata:${NC}"
echo ""
echo -e "  ${CYAN}Option 1 (recommended):${NC}"
echo "    $RUN_SCRIPT"
echo ""
echo -e "  ${CYAN}Option 2 (manual):${NC}"
echo "    cd $PROJECT_DIR"
echo "    venv/bin/python3 main.py"
echo ""

if [ "$TOOLS_OK" = false ]; then
    echo -e "${YELLOW}⚠️  Some external tools are missing. Affected features:${NC}"
    command_exists gs    || echo "    • Ghostscript missing → .eps/.ai files will fail"
    command_exists ffmpeg || echo "    • FFmpeg missing → video files will fail"
    command_exists exiftool || echo "    • ExifTool missing → metadata embedding will fail"
    echo ""
    echo "  Install missing tools and re-run this script."
    echo ""
fi

echo -e "${CYAN}Hardware acceleration status:${NC}"
"$VENV_PYTHON" -c "
import cv2
if cv2.ocl.haveOpenCL():
    cv2.ocl.setUseOpenCL(True)
    print('  ✅ OpenCL GPU: ' + cv2.ocl.Device.getDefault().name())
else:
    print('  ℹ️  OpenCL: not available (CPU-only)')
from PIL import features
turbo = features.check_feature('libjpeg_turbo')
print('  ' + ('✅' if turbo else '⚠️ ') + ' libjpeg-turbo SIMD: ' + ('enabled' if turbo else 'not available'))
import os
cpu = os.cpu_count()
rec = min(int(cpu * 1.5), 100)
print(f'  ✅ CPU threads: {cpu} → recommended workers: {rec}')
" 2>/dev/null || true

echo ""
echo -e "${GREEN}Enjoy using RJ Auto Metadata! 🚀${NC}"
echo ""
