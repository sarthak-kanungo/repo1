@echo off
rem Double-click to install and start OmniRoute on Windows.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0omniroute_windows.ps1" %*
pause
