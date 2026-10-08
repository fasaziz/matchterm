@echo off
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install.ps1"
if errorlevel 1 (
  echo.
  echo Setup or launch failed. Copy the error text above for help.
  pause
)
