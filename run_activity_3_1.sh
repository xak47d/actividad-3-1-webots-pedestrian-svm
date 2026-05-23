#!/bin/zsh
# ============================================================
# Actividad 3.1 — script todo en uno (macOS / Linux).
#
# Prepara el entorno, (opcionalmente) re-entrena el SVM y lanza
# Webots con el mundo de la actividad junto al controlador externo
# del vehículo. Es el equivalente a `run_webots_controller.sh` +
# `capture_synchronized_video.sh` pero unificado.
#
# Uso:
#   ./run_activity_3_1.sh                  # arranca todo
#   ./run_activity_3_1.sh --retrain        # fuerza re-entrenamiento del SVM
#   ./run_activity_3_1.sh --no-webots      # solo entrena + copia modelo
#   ./run_activity_3_1.sh --record         # graba video sincronizado
#   ./run_activity_3_1.sh --world recording  # abre el mundo de grabación
#
# Variables de entorno opcionales:
#   WEBOTS_HOME            Ruta a Webots.app
#   PENNFUDAN_DIR          Ruta al dataset PennFudanPed (default: ./SDC_webots/PennFudanPed)
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ------------------------------------------------------------
# Argumentos.
# ------------------------------------------------------------
RETRAIN=0
LAUNCH_WEBOTS=1
RECORD=0
WORLD_KIND="activity"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --retrain)    RETRAIN=1 ;;
    --no-webots)  LAUNCH_WEBOTS=0 ;;
    --record)     RECORD=1; WORLD_KIND="recording" ;;
    --world)      shift; WORLD_KIND="$1" ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *) echo "Argumento desconocido: $1"; exit 2 ;;
  esac
  shift
done

# ------------------------------------------------------------
# 1. Detección de Webots.
# ------------------------------------------------------------
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

if [[ $LAUNCH_WEBOTS -eq 1 && ( -z "${WEBOTS_HOME:-}" || ! -d "$WEBOTS_HOME" ) ]]; then
  echo "No se pudo detectar WEBOTS_HOME. Define WEBOTS_HOME antes de ejecutar este script."
  exit 1
fi

# ------------------------------------------------------------
# 2. Entorno virtual de Python.
# ------------------------------------------------------------
VENV_DIR="$SCRIPT_DIR/.venv-webots"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "[setup] Creando entorno virtual en $VENV_DIR"
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
  "$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements_webots.txt"
fi

VENV_PY="$VENV_DIR/bin/python"

# ------------------------------------------------------------
# 3. Entrenamiento del SVM (si hace falta o se forzó).
# ------------------------------------------------------------
TRAIN_DIR="$SCRIPT_DIR/SDC_webots/training"
MODEL_TRAIN="$TRAIN_DIR/svm_pedestrian_model.pkl"
MODEL_CTRL="$SCRIPT_DIR/SDC_webots/controllers/vehicle_controller/svm_pedestrian_model.pkl"

PENNFUDAN_DIR="${PENNFUDAN_DIR:-$SCRIPT_DIR/SDC_webots/PennFudanPed}"

if [[ $RETRAIN -eq 1 || ! -f "$MODEL_CTRL" ]]; then
  if [[ ! -d "$PENNFUDAN_DIR" ]]; then
    echo "[train] No se encuentra el dataset PennFudanPed en $PENNFUDAN_DIR"
    echo "       Define PENNFUDAN_DIR o copia el dataset, o salta este paso con un modelo pre-existente."
    if [[ ! -f "$MODEL_CTRL" ]]; then
      exit 1
    fi
  else
    echo "[train] Entrenando SVM con dataset en $PENNFUDAN_DIR"
    # El script train_svm.py espera el dataset un nivel arriba del directorio training/.
    # Hacemos un enlace simbólico temporal si fuese necesario.
    if [[ ! -d "$TRAIN_DIR/../PennFudanPed" ]]; then
      ln -sfn "$PENNFUDAN_DIR" "$TRAIN_DIR/../PennFudanPed"
    fi
    (cd "$TRAIN_DIR" && "$VENV_PY" train_svm.py)
    cp "$MODEL_TRAIN" "$MODEL_CTRL"
    echo "[train] Modelo copiado a $MODEL_CTRL"
  fi
fi

# ------------------------------------------------------------
# 4. Selección de mundo.
# ------------------------------------------------------------
case "$WORLD_KIND" in
  activity)   WORLD="$SCRIPT_DIR/SDC_webots/worlds/city_2025a_activity_3_1.wbt" ;;
  recording)  WORLD="$SCRIPT_DIR/SDC_webots/worlds/city_2025a_activity_3_1_recording.wbt" ;;
  *) echo "Mundo desconocido: $WORLD_KIND"; exit 2 ;;
esac

if [[ $LAUNCH_WEBOTS -eq 0 ]]; then
  echo "[done] Modelo listo. Webots no se lanza por --no-webots."
  exit 0
fi

# ------------------------------------------------------------
# 5. Lanzamiento de Webots + controlador externo.
# ------------------------------------------------------------
export PYTHONPATH="$WEBOTS_HOME/Contents/lib/controller/python"
export WEBOTS_PYTHON_EXECUTABLE="$VENV_PY"

# Elige un puerto libre para esta instancia de Webots. Si ya hay otra
# instancia en 1234 (el puerto por omisión), la nuestra usaría 1235
# pero el controlador externo seguiría conectándose a 1234 (puerto por
# defecto), controlando la instancia equivocada. Para evitarlo,
# elegimos un puerto libre y atamos tanto Webots como el controlador
# externo a ese puerto vía WEBOTS_CONTROLLER_URL.
pick_free_port() {
  python3 - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
}

WEBOTS_PORT="${WEBOTS_PORT:-$(pick_free_port)}"
echo "[run] Usando puerto Webots: $WEBOTS_PORT"

if [[ $RECORD -eq 1 ]]; then
  mkdir -p "$SCRIPT_DIR/media"
  export WEBOTS_RECORD_MAX_SECONDS="${WEBOTS_RECORD_MAX_SECONDS:-30}"
  export WEBOTS_RECORD_MAIN_PATH="$SCRIPT_DIR/media/Actividad_3_1_synchronized_main.mp4"
  export WEBOTS_RECORD_CAMERA_PATH="$SCRIPT_DIR/media/Actividad_3_1_synchronized_camera.mp4"
  # Calidad baja para evitar 'Error: 2pass curve failed to converge' del
  # codificador libx264 con contenido casi estático.
  export WEBOTS_RECORD_MAIN_QUALITY="${WEBOTS_RECORD_MAIN_QUALITY:-50}"
  echo "[record] Webots grabará durante ${WEBOTS_RECORD_MAX_SECONDS}s en $SCRIPT_DIR/media"
fi

echo "[run] Webots → $WORLD"
"$WEBOTS_HOME/Contents/MacOS/webots" \
  --port="$WEBOTS_PORT" \
  --mode=realtime --stdout --stderr "$WORLD" &
WEBOTS_PID=$!

cleanup() {
  if kill -0 "$WEBOTS_PID" 2>/dev/null; then
    kill "$WEBOTS_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if [[ $RECORD -eq 1 ]]; then
  # El mundo de grabación tiene el vehicle_controller declarado como
  # controlador INTERNO de Webots (para mantener cámara y vista 3D en
  # sincronía). No se debe lanzar un controlador externo adicional.
  echo "[record] Esperando a que Webots termine de grabar..."
  wait "$WEBOTS_PID" 2>/dev/null || true
else
  # Webots tarda unos segundos en abrir el mundo y aceptar conexiones externas.
  sleep 4

  CONTROLLER_DIR="$SCRIPT_DIR/SDC_webots/controllers/vehicle_controller"
  echo "[run] Controlador externo → $CONTROLLER_DIR/vehicle_controller.py"

  # El controlador externo se ata a la instancia de Webots correcta vía
  # WEBOTS_CONTROLLER_URL (formato tcp://host:puerto/nombre_del_robot).
  export WEBOTS_CONTROLLER_URL="tcp://localhost:${WEBOTS_PORT}/"

  cd "$CONTROLLER_DIR"
  "$VENV_PY" vehicle_controller.py

  wait "$WEBOTS_PID" 2>/dev/null || true
fi

if [[ $RECORD -eq 1 ]]; then
  echo "[record] Componiendo overlay sincronizado..."
  if command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null; then
    "$VENV_PY" "$SCRIPT_DIR/compose_synchronized_overlay.py"
  else
    echo "[record] ffmpeg/ffprobe no encontrados. Instálalos para componer el overlay."
  fi
fi
