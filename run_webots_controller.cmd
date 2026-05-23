@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "CONTROLLER_DIR=%SCRIPT_DIR%SDC_webots\controllers\vehicle_controller"

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

set "PYTHONPATH=%WEBOTS_HOME%\lib\controller\python"
set "PATH=%WEBOTS_HOME%\msys64\mingw64\bin;%WEBOTS_HOME%\lib\controller;%PATH%"

if "%WEBOTS_PYTHON_EXECUTABLE%"=="" (
  if exist "%SCRIPT_DIR%.venv-webots\Scripts\python.exe" (
    set "WEBOTS_PYTHON_EXECUTABLE=%SCRIPT_DIR%.venv-webots\Scripts\python.exe"
  ) else (
    set "WEBOTS_PYTHON_EXECUTABLE=python"
  )
)

cd /d "%CONTROLLER_DIR%"
"%WEBOTS_PYTHON_EXECUTABLE%" vehicle_controller.py
endlocal
