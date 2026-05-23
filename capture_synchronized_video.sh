#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -z "${WEBOTS_HOME:-}" ]]; then
  if [[ -d "/Applications/Webots.app" ]]; then
    export WEBOTS_HOME="/Applications/Webots.app"
  else
    CASK_WEBOTS="$(ls -d /opt/homebrew/Caskroom/webots/*/Webots.app 2>/dev/null | tail -n 1 || true)"
    if [[ -n "$CASK_WEBOTS" ]]; then
      export WEBOTS_HOME="$CASK_WEBOTS"
    fi
  fi
fi

if [[ -z "${WEBOTS_HOME:-}" || ! -x "$WEBOTS_HOME/Contents/MacOS/webots" ]]; then
  echo "No se pudo detectar Webots. Define WEBOTS_HOME, por ejemplo: /Applications/Webots.app"
  exit 1
fi

mkdir -p "$SCRIPT_DIR/media"

export PATH="$SCRIPT_DIR/.venv-webots/bin:$PATH"
export WEBOTS_RECORD_MAX_SECONDS="${WEBOTS_RECORD_MAX_SECONDS:-18}"
export WEBOTS_RECORD_MAIN_PATH="$SCRIPT_DIR/media/Actividad_3_1_synchronized_main.mp4"
export WEBOTS_RECORD_CAMERA_PATH="$SCRIPT_DIR/media/Actividad_3_1_synchronized_camera.mp4"

"$WEBOTS_HOME/Contents/MacOS/webots" \
  --mode=realtime \
  --stdout \
  --stderr \
  "$SCRIPT_DIR/SDC_webots/worlds/city_2025a_activity_3_1_recording.wbt"
