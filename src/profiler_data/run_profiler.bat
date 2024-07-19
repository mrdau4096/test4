@echo off
cd C:\Users\User\Documents\GitHub\test4

rem Run the main.py script with memory_profiler.
mprof run main.py

rem Find the latest produced data file.
set LATEST_FILE=
for /f "tokens=*" %%f in ('dir /b /o-d "mprofile_*.dat"') do (
    set LATEST_FILE=%%f
    goto :found
)
:found

rem Move produced data file to the right sub-folder.
if defined LATEST_FILE (
    MOVE /Y "%LATEST_FILE%" "profiler_data\data\%LATEST_FILE%"
)

rem Visualise the collected data.
python C:\Users\User\Documents\GitHub\test4\src\profiler_data\profile_visualise.py "profiler_data\data\%LATEST_FILE%%"
