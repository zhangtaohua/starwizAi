pip install django-q2


# 1 项目
```
django-admin startproject starwizAi
```

# 2 启动
```
python3 manage.py runserver
python3 manage.py runserver 5177
python3 manage.py runserver 0.0.0.0:8000
```

# 3 项目
```
python3 manage.py startapp ais
```

静态文件使用
https://www.cnblogs.com/gengyufei/p/12632408.html
https://github.com/cgohlke/geospatial-wheels/releases/tag/v2024.2.18

# django-q2
python3 manage.py migrate django_q
python3 manage.py qcluster


# 注意 
1  、 scikit-learn  要用1.3.1 版本

# 运行

python3 manage.py migrate django_q
python3 manage.py migrate admin
python3 manage.py migrate auth
python3 manage.py migrate contenttypes
python3 manage.py migrate sessions


# 生产启动 
https://github.com/cookiecutter/cookiecutter-django

https://github.com/wsvincent/awesome-django


# 错误处理
1、 proj_create_from_database: C:\Program Files\PostgreSQL\13\share\contrib\postgis-3.2\proj\proj.db contains DATABASE.LAYOUT.VERSION.MINOR = 0 whereas a number >= 2 is expected. It comes from another PROJ installation.

原因：
这个错误表明你的 PROJ 库版本与 PostGIS 库不兼容，特别是 proj.db 数据库文件的版本不匹配。这通常发生在系统上存在多个 PROJ 安装，或由于 PROJ 版本升级导致的不兼容。

解决办法： 
pip3 install pyproj
在代码中设置
os.environ["PROJ_LIB"] = r"C:\Python312\Lib\site-packages\pyproj\proj_dir\share\proj"