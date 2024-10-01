cd C:\Users\User\Documents\GitHub\test4

REM Run PyInstaller with the specified options
pyinstaller --onefile ^
    --add-data "C:\Users\User\Documents\GitHub\test4\src;src" ^
    --hidden-import numpy ^
    --hidden-import pyrr ^
    --hidden-import glfw ^
    --hidden-import pyopengl ^
    --hidden-import pyglm ^
    --hidden-import pillow ^
    --hidden-import multiprocess ^
    --add-binary "C:\Python310\Lib\site-packages\glfw\glfw3.dll;." ^
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