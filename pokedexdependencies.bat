@echo off
title Pokémon Codex Scout
color 0A

echo ====================================================
echo    DETECTING PYTHON ENVIRONMENT
echo ====================================================
echo.

:: 1. Check for 'python' command
python --version >nul 2>&1
if %errorlevel% == 0 (
    set PY_CMD=python
    goto :found
)

:: 2. Check for 'py' launcher (standard on Windows)
py --version >nul 2>&1
if %errorlevel% == 0 (
    set PY_CMD=py
    goto :found
)

:: 3. Not found - Help the user
echo [!] Python was NOT detected on this system.
echo [!] Opening the official Python download page for you...
echo.
timeout /t 3
start https://www.python.org/downloads/
echo.
echo ----------------------------------------------------
echo Once installed, make sure to check "Add Python to PATH"
echo Then, run this batch file again!
echo ----------------------------------------------------
pause
exit

:found
echo [OK] Python detected using command: %PY_CMD%
%PY_CMD% --version
echo.

echo ====================================================
echo    INSTALLING POKEMON CODEX LIBRARIES
echo ====================================================
echo.

echo [1/3] Upgrading pip...
%PY_CMD% -m pip install --upgrade pip --user

echo.
echo [2/3] Installing essential tools (Requests, Pillow)...
%PY_CMD% -m pip install requests Pillow

echo.
echo [3/3] Installing the Audio Engine (Pygame-CE)...
%PY_CMD% -m pip install pygame-ce

echo.
echo ====================================================
echo    SUCCESS: Environment is ready to go!
echo ====================================================
pause