cd C:\Users\User\Documents\GitHub\test4

REM Run PyInstaller with the specified options
pyinstaller --onefile ^
    --add-data "C:\Users\User\Documents\GitHub\test4\src;src" ^
    --add-data "C:\Users\User\Documents\GitHub\test4\src\modules;modules" ^
    --hidden-import numpy ^
    --hidden-import pyrr ^
    main.py

REM Check if the build was successful
IF NOT EXIST "dist\main.exe" (
    ECHO Build failed!
    EXIT /B 1
)

REM Move the executable
MOVE /Y "dist\main.exe" "main.exe"

REM Remove the build directories and spec file
RMDIR /S /Q "dist"
RMDIR /S /Q "build"
DEL /Q "main.spec"
