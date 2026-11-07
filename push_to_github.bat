@echo off
setlocal
echo ====================================================================
echo  FIPP — Facility Issue Prediction & Prioritization
echo  Pushing code to GitHub...
echo ====================================================================
echo.

set "PATH=C:\Users\pothu\MinGit\cmd;%PATH%"

git branch -M main
git push -u origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo --------------------------------------------------------------------
    echo [NOTICE] If the push failed, please ensure:
    echo   1. The empty repository has been created at:
    echo      https://github.com/new
    echo      Repository Name: Smart-Campus-Facility-Issue-Prediction-Prioritization-System
    echo      (Do not initialize with README, .gitignore, or license)
    echo.
    echo   2. Authenticate when prompted by GitHub in the browser / terminal.
    echo --------------------------------------------------------------------
    echo.
) else (
    echo.
    echo ====================================================================
    echo [SUCCESS] Code pushed to GitHub successfully!
    echo View repository at:
    echo https://github.com/dheerajpothula/Smart-Campus-Facility-Issue-Prediction-Prioritization-System
    echo ====================================================================
    echo.
)

pause
