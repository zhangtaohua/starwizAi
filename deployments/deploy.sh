#!/bin/bash

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Script directory: $SCRIPT_DIR"

# 获取上层目录
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
echo "Parent directory: $PARENT_DIR"

SUPER_LOGS_DIR="$PARENT_DIR/running/storage/logs/supervisord"
GNUICORN_LOGS_DIR="$PARENT_DIR/running/storage/logs/gunicorn"

sudo mkdir -p $SUPER_LOGS_DIR
sudo mkdir -p $GNUICORN_LOGS_DIR
sudo chmod -R 777 $PARENT_DIR

# 判断上层目录是否存在 /build 文件
IMAGE_TAR_FILE="$PARENT_DIR/build/images/starwiz_ai_django.tar.gz"

echo "IMAGE directory: $IMAGE_TAR_FILE"

if [ -f "$IMAGE_TAR_FILE" ]; then
    echo "images*.tar.gz found in parent directory. Running docker load ..."
    docker load -i $IMAGE_TAR_FILE
else
    echo "images*.tar.gz not found in parent directory."
fi

# 检查 docker load 是否成功
if [ $? -eq 0 ]; then
    echo "docker load completed successfully"
    echo $?
else
    echo "docker load failed"
    echo $?
    exit 1
fi

# 判断脚本所在目录下是否存在 docker-compose.yml 文件
DOCKER_COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

if [ -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "docker-compose.yml found, running docker-compose"
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
else
    echo "docker-compose.yml not found"
    exit 1
fi

# 获取上层目录
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
echo "Parent directory: $PARENT_DIR"

# 判断上层目录是否存在 /app/manage.py 文件
MANAGE_FILE = "$PARENT_DIR/manage.py"
if [ -f "$MANAGE_FILE" ]; then
    echo "manage.py found in parent directory. Running python3 manage.py..."
    python "$MANAGE_FILE" runserver
else
    echo "manage.py not found in parent directory."
fi

# 检查 migrate 是否成功
if [ $? -eq 0 ]; then
    echo "Django migrate completed successfully"
    echo $?
else
    echo "Django migrate failed"
    echo $?
    exit 1
fi


