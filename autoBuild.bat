@echo off

REM This script just sets python as a system variable for this particular session
REM So that the python scripts can run if you get errors check the file paths

"C:\Python27\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke9.0v1\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke9.0v2\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke9.0v3\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke9.0v4\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke9.0v5\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke9.0v6\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke9.0v7\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke9.0v8\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke9.0v9\python" %~f0\..\autoBuild.py

"C:\Program Files\Nuke10.0v1\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke10.0v2\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke10.0v3\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke10.0v4\python" %~f0\..\autoBuild.py
"C:\Program Files\Nuke10.0v5\python" %~f0\..\autoBuild.py

echo Press the any key to exit
pause > nul
cls
exit