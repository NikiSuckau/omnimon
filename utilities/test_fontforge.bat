@echo off
echo Testing FontForge execution...
cd /d "e:\Omnimon\utilities"

echo.
echo Running FontForge with basic script...
"C:\Program Files (x86)\FontForgeBuilds\run_fontforge.exe" -script Forge_basic.pe

echo.
echo Exit code: %ERRORLEVEL%

echo.
echo Checking for output file...
if exist "ProggySmall-merged.ttf" (
    echo SUCCESS: Font file created!
    dir "ProggySmall-merged.ttf"
) else (
    echo ERROR: Font file not created.
)

echo.
echo Testing if FontForge can open files individually...
echo Open("ProggySmall.ttf") > test_open.pe
echo Print("Font opened successfully") >> test_open.pe
echo Quit() >> test_open.pe

"C:\Program Files (x86)\FontForgeBuilds\run_fontforge.exe" -script test_open.pe
echo Simple open test exit code: %ERRORLEVEL%

pause