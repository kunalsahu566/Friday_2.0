#!/bin/zsh
# Installs Friday as a login item. It starts hidden, waits for the wake phrase,
# and restarts if the process exits unexpectedly.

set -eu
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LABEL="com.friday2.assistant"
AGENT_DIR="$HOME/Library/LaunchAgents"
PLIST="$AGENT_DIR/$LABEL.plist"
APP="$PROJECT_ROOT/dist/Friday.app"
UID_VALUE="$(id -u)"
CONFIG_DIR="$HOME/Library/Application Support/Friday2"

mkdir -p "$AGENT_DIR"
mkdir -p "$CONFIG_DIR"
# Preserve an existing packaged-app configuration. On first install, migrate
# the project's optional settings so weather and voice preferences still work.
if [[ -f "$PROJECT_ROOT/.env" && ! -f "$CONFIG_DIR/.env" ]]; then
  umask 077
  cp "$PROJECT_ROOT/.env" "$CONFIG_DIR/.env"
fi
launchctl bootout "gui/$UID_VALUE" "$PLIST" 2>/dev/null || true

if [[ -d "$APP" ]]; then
  # Launch the bundle executable directly. `open` returns immediately, which
  # makes a KeepAlive LaunchAgent relaunch it in a loop.
  PROGRAM="$APP/Contents/MacOS/Friday"
  ARGUMENTS=""
else
  PROGRAM="/bin/zsh"
  ARGUMENTS="<string>$PROJECT_ROOT/macos/run_friday.sh</string>"
fi

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>$PROGRAM</string>$ARGUMENTS</array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>WorkingDirectory</key><string>$PROJECT_ROOT</string>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/friday2.out.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/friday2.err.log</string>
</dict></plist>
EOF

launchctl bootstrap "gui/$UID_VALUE" "$PLIST"
launchctl kickstart -k "gui/$UID_VALUE/$LABEL"
echo "Friday starts automatically at login. To stop it: launchctl bootout gui/$UID_VALUE $PLIST"
