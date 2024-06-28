#!/bin/bash

# 启动 Gunicorn
gunicorn -c /app/build/docker/gunicorn.conf.py starwizAi.wsgi:application &

# 启动 qcluster
python manage.py qcluster &

# 等待所有后台进程
wait -n

# 获取第一个进程的退出代码
exit $?