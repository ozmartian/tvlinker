@echo off

rd /s /q build
rd /s /q dist
pyinstaller --clean tvlinker.%1.spec

REM verpatch.exe dist\tvlinker.exe /va 3.0.0.0 /pv 3.0.0.0 /s desc "TVLinker" /s name "TVLinker" /s copyright "2016 Pete Alexandrou" /s product "TVLinker x64"
