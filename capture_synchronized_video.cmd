@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

if "%WEBOTS_HOME%"=="" (
  if exist "C:\Program Files\Webots" (
    set "WEBOTS_HOME=C:\Program Files\Webots"
  ) else if exist "C:\Program Files (x86)\Webots" (
    set "WEBOTS_HOME=C:\Program Files (x86)\Webots"
  )
)

if "%WEBOTS_HOME%"=="" (
  echo No se pudo detectar WEBOTS_HOME. Define WEBOTS_HOME antes de ejecutar este script.
  exit /b 1
)

if exist "%WEBOTS_HOME%\msys64\mingw64\bin\webots.exe" (
  set "WEBOTS_EXE=%WEBOTS_HOME%\msys64\mingw64\bin\webots.exe"
) else if exist "%WEBOTS_HOME%\webots.exe" (
  set "WEBOTS_EXE=%WEBOTS_HOME%\webots.exe"
) else (
  echo No se encontro webots.exe dentro de WEBOTS_HOME.
  exit /b 1
)

if not exist "%SCRIPT_DIR%media" mkdir "%SCRIPT_DIR%media"

if "%WEBOTS_RECORD_MAX_SECONDS%"=="" set "WEBOTS_RECORD_MAX_SECONDS=18"
set "WEBOTS_RECORD_MAIN_PATH=%SCRIPT_DIR%media\Actividad_3_1_synchronized_main.mp4"
set "WEBOTS_RECORD_CAMERA_PATH=%SCRIPT_DIR%media\Actividad_3_1_synchronized_camera.mp4"
set "PATH=%SCRIPT_DIR%.venv-webots\Scripts;%WEBOTS_HOME%\msys64\mingw64\bin;%WEBOTS_HOME%\lib\controller;%PATH%"

"%WEBOTS_EXE%" --mode=realtime --stdout --stderr "%SCRIPT_DIR%SDC_webots\worlds\city_2025a_activity_3_1_recording.wbt"
endlocal
