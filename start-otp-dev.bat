@echo off

color c

REM this is taking the contents of PPYTHON_PATH.txt and putting it in an Environment varaible.
set /P PPYTHON_PATH=<PPYTHON_PATH.txt

title OpenOTP
:goto
if exist %PPYTHON_PATH% (
%PPYTHON_PATH% __main__.py
) else (
echo You seem to be missing %PPYTHON_PATH%, which is required to run OpenOTP.
echo Please install Panda3D-1.8.1 or edit PPYTHON_PATH.txt to where your ppython is.
)
pause
goto :goto
