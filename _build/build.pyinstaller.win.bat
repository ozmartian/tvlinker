@echo off

rd /s /q build
rd /s /q dist
pyinstaller --clean tvlinker.win.spec
