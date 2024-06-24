#!/bin/bash

# 1. 挂载 Windows 目录到 Linux 系统
WINDOWS_DIR="//192.168.3.100/share"
MOUNT_POINT="/mnt/rj/share"
# HOME_DIR="/home/$(whoami)/"
HOME_DIR="/home/hkatg/app/datawiz-ai-bone"
WINDOWS_USERNAME="RJ"
WINDOWS_PASSWORD=""

# 检查操作系统类型
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot determine OS type"
    exit 1
fi

# 根据操作系统类型安装 cifs-utils
if [ "$OS" == "ubuntu" ]; then
  echo "Detected Ubuntu. Checking if cifs-utils is installed..."
  if ! dpkg -l | grep -q cifs-utils; then
    sudo apt-get update
    sudo apt-get install -y cifs-utils
  else
      echo "cifs-utils is already installed."
  fi
elif [ "$OS" == "centos" ] || [ "$OS" == "rhel" ]; then
    echo "Detected CentOS/RHEL. Checking if cifs-utils is installed..."

    # 检查是否已安装 cifs-utils
    if rpm -q cifs-utils >/dev/null 2>&1; then
        echo "cifs-utils is already installed."
    else
        echo "cifs-utils is not installed. Installing..."
        sudo yum install -y cifs-utils
    fi
else
    echo "Unsupported OS type: $OS"
    exit 1
fi

# 确保挂载点目录存在
sudo mkdir -p $MOUNT_POINT

# 挂载 Windows 共享目录
sudo mount -t cifs -o username=$WINDOWS_USERNAME,password=$WINDOWS_PASSWORD $WINDOWS_DIR $MOUNT_POINT
# sudo mount -t cifs -o $WINDOWS_DIR $MOUNT_POINT

# 检查是否挂载成功
if mountpoint -q $MOUNT_POINT; then
    echo "Windows directory mounted successfully at $MOUNT_POINT"
else
    echo "Failed to mount Windows directory" >&2
    exit 1
fi

# 2. 复制所有目录和文件到 home 目录
cp -r $MOUNT_POINT/django/* $HOME_DIR

# 检查是否复制成功
if [ $? -eq 0 ]; then
    echo "Files copied successfully to $HOME_DIR"
else
    echo "Failed to copy files" >&2
    exit 1
fi
