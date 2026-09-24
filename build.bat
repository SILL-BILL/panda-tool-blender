@echo off
setlocal

set "REPOSITORY_ROOT=%~dp0"

if defined BLENDER_EXE goto check_blender
set "BLENDER_EXE=blender"

:check_blender
if exist "%BLENDER_EXE%" goto blender_found
where "%BLENDER_EXE%" >nul 2>&1
if not errorlevel 1 goto blender_found

for %%V in (5.1 5.0 4.5 4.4 4.3 4.2) do (
    if exist "%ProgramFiles%\Blender Foundation\Blender %%V\blender.exe" (
        set "BLENDER_EXE=%ProgramFiles%\Blender Foundation\Blender %%V\blender.exe"
        goto blender_found
    )
)

echo ERROR: Blender 4.2 or later was not found.
echo Add Blender to PATH or set BLENDER_EXE to the full blender.exe path.
pause
exit /b 1

:blender_found
if not exist "%REPOSITORY_ROOT%dist" mkdir "%REPOSITORY_ROOT%dist"

echo Building Panda Tool Extension with:
echo %BLENDER_EXE%
"%BLENDER_EXE%" --factory-startup --command extension build --source-dir "%REPOSITORY_ROOT%panda_tool" --output-dir "%REPOSITORY_ROOT%dist"
if errorlevel 1 (
    echo ERROR: Extension build failed.
    pause
    exit /b 1
)

echo Build complete: "%REPOSITORY_ROOT%dist\panda_tool-0.5.0.zip"
exit /b 0
