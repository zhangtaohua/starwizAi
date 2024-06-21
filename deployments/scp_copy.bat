@echo off
setlocal

rem 定义变量
set USER=hkatg
set PASSWORD=123456
set HOST=192.168.3.247
set REMOTE_DIR=/home/hkatg/rj/
set SOURCE_DIR=D:\Work\project\Python\starwizAi\*

rem 使用 scp 复制文件
scp -r %SOURCE_DIR% %USER%@%HOST%:%REMOTE_DIR%

rem 使用 pscp 复制文件
rem pscp -r -pw %PASSWORD% %SOURCE_DIR% %USER%@%HOST%:%REMOTE_DIR%

endlocal
echo Files copied successfully.
pause
