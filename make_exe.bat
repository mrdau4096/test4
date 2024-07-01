cd C:\Users\User\Documents\code\.py\pygame\test4.2.3b

REM Run PyInstaller with the specified options
pyinstaller --onefile ^
    --add-data "C:\Users\User\Documents\code\.py\pygame\test4.2.3b\src;src" ^
    --add-data "C:\Users\User\Documents\code\.py\pygame\test4.2.3b\src\modules.zip;modules.zip" ^
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
