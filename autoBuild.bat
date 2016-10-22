@echo off

REM This script just sets python as a system variable for this particular session
REM So that the python scripts can run if you get errors check the file paths

C:\Python27\python %~f0\..\autoBuild.py

echo Press the any key to exit
pause > nul
cls
exit