@echo off
REM ============================================================
REM Actividad 3.1 — script todo en uno (Windows).
REM Equivalente a run_activity_3_1.sh.
REM
REM Uso:
REM   run_activity_3_1.cmd                 (arranca todo)
REM   run_activity_3_1.cmd --retrain       (fuerza re-entrenamiento)
REM   run_activity_3_1.cmd --no-webots     (solo entrena + copia modelo)
REM   run_activity_3_1.cmd --record        (graba video sincronizado)
REM   run_activity_3_1.cmd --world recording
REM ============================================================
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

set "RETRAIN=0"
set "LAUNCH_WEBOTS=1"
set "RECORD=0"
set "WORLD_KIND=activity"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--retrain"    ( set "RETRAIN=1" & shift & goto parse_args )
if /I "%~1"=="--no-webots"  ( set "LAUNCH_WEBOTS=0" & shift & goto parse_args )
if /I "%~1"=="--record"     ( set "RECORD=1" & set "WORLD_KIND=recording" & shift & goto parse_args )
if /I "%~1"=="--world"      ( set "WORLD_KIND=%~2" & shift & shift & goto parse_args )
echo Argumento desconocido: %~1
exit /b 2
:args_done

REM --- Webots ---
if "%WEBOTS_HOME%"=="" (
  if exist "C:\Program Files\Webots" set "WEBOTS_HOME=C:\Program Files\Webots"
  if exist "C:\Program Files (x86)\Webots" set "WEBOTS_HOME=C:\Program Files (x86)\Webots"
)

if "%LAUNCH_WEBOTS%"=="1" (
  if "%WEBOTS_HOME%"=="" (
    echo No se pudo detectar WEBOTS_HOME. Define WEBOTS_HOME antes de ejecutar este script.
    exit /b 1
  )
)

REM --- Entorno virtual ---
set "VENV_DIR=%SCRIPT_DIR%.venv-webots"
if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo [setup] Creando entorno virtual en %VENV_DIR%
  py -3 -m venv "%VENV_DIR%"
  "%VENV_DIR%\Scripts\python.exe" -m pip install --quiet --upgrade pip
  "%VENV_DIR%\Scripts\python.exe" -m pip install --quiet -r "%SCRIPT_DIR%requirements_webots.txt"
)
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

REM --- Entrenamiento (si hace falta) ---
set "TRAIN_DIR=%SCRIPT_DIR%SDC_webots\training"
set "MODEL_TRAIN=%TRAIN_DIR%\svm_pedestrian_model.pkl"
set "MODEL_CTRL=%SCRIPT_DIR%SDC_webots\controllers\vehicle_controller\svm_pedestrian_model.pkl"
if "%PENNFUDAN_DIR%"=="" set "PENNFUDAN_DIR=%SCRIPT_DIR%SDC_webots\PennFudanPed"

if "%RETRAIN%"=="1" goto do_train
if not exist "%MODEL_CTRL%" goto do_train
goto skip_train
:do_train
  if not exist "%PENNFUDAN_DIR%" (
    echo [train] No se encuentra el dataset en %PENNFUDAN_DIR%
    if not exist "%MODEL_CTRL%" exit /b 1
  ) else (
    echo [train] Entrenando SVM con dataset en %PENNFUDAN_DIR%
    pushd "%TRAIN_DIR%"
    "%VENV_PY%" train_svm.py
    popd
    copy /Y "%MODEL_TRAIN%" "%MODEL_CTRL%" >nul
    echo [train] Modelo copiado a %MODEL_CTRL%
  )
:skip_train

REM --- Mundo ---
if /I "%WORLD_KIND%"=="activity"  set "WORLD=%SCRIPT_DIR%SDC_webots\worlds\city_2025a_activity_3_1.wbt"
if /I "%WORLD_KIND%"=="recording" set "WORLD=%SCRIPT_DIR%SDC_webots\worlds\city_2025a_activity_3_1_recording.wbt"
if not defined WORLD (
  echo Mundo desconocido: %WORLD_KIND%
  exit /b 2
)

if "%LAUNCH_WEBOTS%"=="0" (
  echo [done] Modelo listo. Webots no se lanza por --no-webots.
  popd
  exit /b 0
)

REM --- Webots + controlador externo ---
set "PYTHONPATH=%WEBOTS_HOME%\lib\controller\python"
set "PATH=%VENV_DIR%\Scripts;%WEBOTS_HOME%\msys64\mingw64\bin;%WEBOTS_HOME%\lib\controller;%PATH%"
set "WEBOTS_PYTHON_EXECUTABLE=%VENV_PY%"

if exist "%WEBOTS_HOME%\msys64\mingw64\bin\webots.exe" (
  set "WEBOTS_EXE=%WEBOTS_HOME%\msys64\mingw64\bin\webots.exe"
) else (
  set "WEBOTS_EXE=%WEBOTS_HOME%\webots.exe"
)

if "%RECORD%"=="1" (
  if not exist "%SCRIPT_DIR%media" mkdir "%SCRIPT_DIR%media"
  if "%WEBOTS_RECORD_MAX_SECONDS%"=="" set "WEBOTS_RECORD_MAX_SECONDS=30"
  if "%WEBOTS_RECORD_MAIN_QUALITY%"=="" set "WEBOTS_RECORD_MAIN_QUALITY=50"
  set "WEBOTS_RECORD_MAIN_PATH=%SCRIPT_DIR%media\Actividad_3_1_synchronized_main.mp4"
  set "WEBOTS_RECORD_CAMERA_PATH=%SCRIPT_DIR%media\Actividad_3_1_synchronized_camera.mp4"
  echo [record] Webots grabara durante %WEBOTS_RECORD_MAX_SECONDS%s en %SCRIPT_DIR%media
)

REM Elige un puerto libre para esta instancia y ata el controlador
REM externo a el via WEBOTS_CONTROLLER_URL.
if "%WEBOTS_PORT%"=="" (
  for /f %%P in ('"%VENV_PY%" -c "import socket;s=socket.socket();s.bind((''127.0.0.1'',0));print(s.getsockname()[1]);s.close()"') do set "WEBOTS_PORT=%%P"
)
echo [run] Usando puerto Webots: %WEBOTS_PORT%

echo [run] Webots -^> %WORLD%
if "%RECORD%"=="1" (
  REM El mundo de grabacion usa el vehicle_controller INTERNO de Webots.
  REM No se lanza controlador externo; Webots se cierra solo al terminar.
  "%WEBOTS_EXE%" --port=%WEBOTS_PORT% --mode=realtime --stdout --stderr "%WORLD%"
) else (
  start "" "%WEBOTS_EXE%" --port=%WEBOTS_PORT% --mode=realtime --stdout --stderr "%WORLD%"
  timeout /t 4 /nobreak >nul
  set "WEBOTS_CONTROLLER_URL=tcp://localhost:%WEBOTS_PORT%/"
  echo [run] Controlador externo -^> SDC_webots\controllers\vehicle_controller\vehicle_controller.py
  pushd "%SCRIPT_DIR%SDC_webots\controllers\vehicle_controller"
  "%VENV_PY%" vehicle_controller.py
  popd
)

if "%RECORD%"=="1" (
  echo [record] Componiendo overlay sincronizado...
  where ffmpeg >nul 2>nul && where ffprobe >nul 2>nul
  if not errorlevel 1 (
    "%VENV_PY%" "%SCRIPT_DIR%compose_synchronized_overlay.py"
  ) else (
    echo [record] ffmpeg/ffprobe no encontrados. Instalalos para componer el overlay.
  )
)

popd
endlocal
