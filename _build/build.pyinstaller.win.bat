@echo off

REM ......................setup variables......................

if [%1]==[] (
    SET ARCH=64
) else (
    SET ARCH=%1
)

if ["%ARCH%"]==["64"] ( SET BINARCH=x64 )
if ["%ARCH%"]==["32"] ( SET BINARCH=x86 )

REM ......................get latest version number......................

for /f "delims=" %%a in ('python version.py') do @set VERSION=%%a

REM ......................cleanup previous build scraps......................

rd /s /q build
rd /s /q dist

REM ......................run pyinstaller......................

pyinstaller --clean tvlinker.win%ARCH%.spec

REM ......................add metadata to built Windows binary......................

verpatch dist\tvlinker.exe /va %VERSION%.0 /pv %VERSION%.0 /s desc "TVLinker" /s name "TVLinker" /s copyright "(c) 2017 Pete Alexandrou" /s product "TVLinker %BINARCH%" /s company "ozmartians.com"

REM ......................call Inno Setup installer build script......................

cd InnoSetup
"C:\Program Files (x86)\Inno Setup 5\iscc.exe" installer_%BINARCH%.iss
cd ..
