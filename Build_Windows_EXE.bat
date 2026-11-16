@echo off
setlocal
cd /d "%~dp0"
py -3.11 -m venv .venv
if errorlevel 1 goto :error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --name FiveM_Resource_Studio FiveM_Resource_Studio.py
if errorlevel 1 goto :error
echo.
echo EXE listo: dist\FiveM_Resource_Studio.exe
pause
exit /b 0
:error
echo Error al construir. Revisa el mensaje anterior.
pause
exit /b 1
