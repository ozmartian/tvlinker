@echo off

rd /s /q build
rd /s /q dist
pyinstaller --clean tvlinker.win%1.spec

verpatch.exe dist\tvlinker.exe /va 3.0.5.0 /pv 3.0.5.0 /s desc "TVLinker" /s name "TVLinker" /s copyright "2017 Pete Alexandrou" /s product "TVLinker x64"
