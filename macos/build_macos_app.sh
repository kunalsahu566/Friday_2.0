#!/bin/zsh
# Builds dist/Friday.app. Run after installing requirements-macos.txt.

set -eu
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="$PROJECT_ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3)"
fi

cd "$PROJECT_ROOT"
# Keep PyInstaller's signing-analysis cache inside the project. This makes
# repeatable builds work in restricted macOS environments as well.
export PYINSTALLER_CONFIG_DIR="$PROJECT_ROOT/.pyinstaller"
"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name Friday \
  --osx-bundle-identifier com.friday2.assistant \
  --add-data "Website/Assests/Image/friday-core-3d.png:Website/Assests/Image" \
  mac_app.py

INFO_PLIST="$PROJECT_ROOT/dist/Friday.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "$INFO_PLIST" 2>/dev/null || \
  /usr/libexec/PlistBuddy -c "Set :LSUIElement true" "$INFO_PLIST"
/usr/libexec/PlistBuddy -c "Add :NSMicrophoneUsageDescription string Friday listens for the Hello Friday wake phrase and your voice commands." "$INFO_PLIST" 2>/dev/null || \
  /usr/libexec/PlistBuddy -c "Set :NSMicrophoneUsageDescription Friday listens for the Hello Friday wake phrase and your voice commands." "$INFO_PLIST"
# PlistBuddy changes the generated bundle, so refresh its ad-hoc signature.
codesign --force --deep --sign - "$PROJECT_ROOT/dist/Friday.app"

echo "Built: $PROJECT_ROOT/dist/Friday.app"
