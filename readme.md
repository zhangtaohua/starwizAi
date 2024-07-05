pip install django-q2


# 1 新建项目
```
django-admin startproject starwizAi
```

# 2 新建应用
```
python3 manage.py startapp ais
```

# 3 本地启动调试

## 3.1 运行前准备：
```
python3 manage.py migrate django_q
python3 manage.py migrate admin
python3 manage.py migrate auth
python3 manage.py migrate contenttypes
python3 manage.py migrate sessions
```

## 3.2 启动应用

```
python3 manage.py runserver
python3 manage.py runserver 5177
python3 manage.py runserver 0.0.0.0:8000
```

# 4 部署
## 4.1 部署前检查代码命令 

**注意此步骤实际部署时不用进行**
```
python3 manage.py check --deploy
```

## 4.2 前置条件：

### 4.2.1 硬件条件
CPU：
GPU：
内存：
硬盘：


### 4.2.2 软件条件

操作系统： linux(ubuntu, centos)
依赖库： cifs-utils、cuda, cudnn
软件： docker、

## 4.3 实际步骤：

以下所有步骤均认为已满足前置条件.

### 4.3.1 复制文件
假设

源文件目录：
目标文件目录：

使用任意办法将源文件目录下所有文件复制到目标文件目录下。

### 4.3.2 执行脚本



# 5 其他
## 静态文件使用参考
https://www.cnblogs.com/gengyufei/p/12632408.html
https://github.com/cgohlke/geospatial-wheels/releases/tag/v2024.2.18

## whls 查找目录 
https://wheelhouse.openquake.org/
https://girder.github.io/large_image_wheels/

## django-q2
python3 manage.py migrate django_q
python3 manage.py qcluster

## cuDNN 
https://developer.nvidia.com/rdp/cudnn-archive

192.168.3.250:\softwares\CUDA 请别删

## 注意 
1  、 scikit-learn  要用1.3.1 版本

## 清空间
```
docker system df
docker builder prune
docker system prune -a
wsl --shutdown
```

再进行

```
 diskpart
# 选择虚拟机文件执行瘦身
> select vdisk file="C:\Users\RJ\AppData\Local\Docker\wsl\data\ext4.vhdx"
> attach vdisk readonly
> compact vdisk
> detach vdisk
> exit

链接：https://juejin.cn/post/7256966480229646391

```

## 生产启动参考 
https://github.com/cookiecutter/cookiecutter-django

https://github.com/wsvincent/awesome-django

https://testdriven.io/blog/docker-best-practices/#use-multi-stage-builds


# 6 错误处理
## 1 、It comes from another PROJ installation.

proj_create_from_database: C:\Program Files\PostgreSQL\13\share\contrib\postgis-3.2\proj\proj.db contains DATABASE.LAYOUT.VERSION.MINOR = 0 whereas a number >= 2 is expected. It comes from another PROJ installation.

**原因：**
这个错误表明你的 PROJ 库版本与 PostGIS 库不兼容，特别是 proj.db 数据库文件的版本不匹配。这通常发生在系统上存在多个 PROJ 安装，或由于 PROJ 版本升级导致的不兼容。

**解决办法：** 
`pip3 install pyproj`
在代码中设置
`os.environ["PROJ_LIB"] = r"C:\Python312\Lib\site-packages\pyproj\proj_dir\share\proj"`

docker run -d --name test_starwiz_ai_django -v /d/Work/project/Python/starwizAi:/app -p 5177:5177  starwiz_ai_django:prod

## docker 镜像
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "registry-mirrors": [
    "https://registry.docker-cn.com",
    "https://docker.mirrors.ustc.edu.cn",
    "http://hub-mirror.c.163.com",
    "https://mirror.sjtu.edu.cn"
  ],
  "experimental": false,
  "features": {
    "buildkit": true
  }
}