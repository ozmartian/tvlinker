@echo off

cd ..
nuitka --recurse-all --remove-output --windows-disable-console --windows-icon=assets\images\tvlinker.ico main.py
