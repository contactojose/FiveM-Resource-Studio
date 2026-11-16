@echo off
cd /d "%~dp0"
if exist "dist\FiveM_Resource_Studio.exe" (
  start "" "dist\FiveM_Resource_Studio.exe"
  exit /b 0
)
where py >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python.
  echo Para generar el EXE en Windows, ejecuta Build_Windows_EXE.bat en un equipo con Python 3.11.
  pause
  exit /b 1
)
py -3.11 FiveM_Resource_Studio.py
if errorlevel 1 pause
