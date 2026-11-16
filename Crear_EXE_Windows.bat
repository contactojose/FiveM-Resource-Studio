@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo   FIVE M RESOURCE STUDIO - BUILD EXE
echo ==========================================
where py >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python Launcher.
  echo Instala Python 3 desde https://www.python.org/downloads/
  echo Marca "Add Python to PATH".
  pause
  exit /b 1
)
py -m pip install --upgrade pip
if errorlevel 1 goto :error
py -m pip install pyinstaller
if errorlevel 1 goto :error
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "FiveM_Resource_Studio" FiveM_Resource_Studio.py
if errorlevel 1 goto :error
echo.
echo EXE CREADO EN:
echo %CD%\dist\FiveM_Resource_Studio.exe
echo.
pause
exit /b 0
:error
echo.
echo No se pudo crear el EXE. Revisa el error mostrado arriba.
pause
exit /b 1
