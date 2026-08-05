@echo off
title NSE Swing Trading Bot - Daily Automated Job
cd /d "%~dp0"
echo ===================================================
echo   RUNNING NSE SWING TRADING AUTOMATED DAILY JOB
echo ===================================================
call .\venv\Scripts\activate.bat
python scripts/automated_daily_job.py
echo.
echo Job completed. Press any key to exit...
pause > nul
