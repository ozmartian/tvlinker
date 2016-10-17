@echo off

cd ..
nuitka --recurse-all --remove-output --windows-disable-console --windows-icon=assets\teevee.ico main.py
