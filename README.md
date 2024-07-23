
## 准备工作

```
Python >= 3.8.0 (推荐3.8+版本)
nodejs >= 16.0 (推荐最新)
Mysql >= 5.7.0 
```
## 一.nginx安装

### nginx需要的依赖包括：gcc、g++、ssl、pcre、zlib；

#### 安装步骤

```text
1、安装依赖：gcc、gcc-c++、ssl、pcre、zlib。注意：一定要先安装gcc，再安装gcc-c++。然后再安装其他，其他的没有先后顺序。
2、安装Nginx；
3、启动Nginx（直接用默认配置启动测试即可）。
```

##### 详细步骤

```shell
#1、在CentOS服务器上解压源码包，并进入解压后的目录，如下所示：
tar -zxvf nginx-1.20.0.tar.gz
cd nginx-1.20.0
#2、为了使NGINX支持HTTPS协议，需要安装OpenSSL库。可以使用以下命令来安装：
yum install -y openssl openssl-devel
#3/为了确保编译过程中的依赖项已安装，可以使用以下命令：
yum groupinstall -y "Development Tools"
yum install -y zlib-devel
#4 配置NGINX的编译选项。可以使用以下命令来配置：
./configure --prefix=/usr/local/nginx --with-http_ssl_module
#5 编译并安装NGINX。可以使用以下命令来编译和安装：
make
make install
#6 启动NGINX。可以使用以下命令来启动：
/usr/local/nginx/sbin/nginx
#7 如果需要停止NGINX，可以使用以下命令：
/usr/local/nginx/sbin/nginx -s stop
#8 如果需要重新加载配置文件，可以使用以下命令：
/usr/local/nginx/sbin/nginx -s reload 
```

## 二.安装项目依赖包

### 安装步骤

```shell
#1、进入项目中的packagesDir目录
cd packagesDir
#2、执行批量安装命令
pip3 install *.whl
```

### 后端启动 
```bash
# 进入项目目录
cd backend
# 在 `env.py` 中配置数据库信息
# 默认是Mysql，如果使用SqlServer，qing在requirements.txt中打开 
   mssql-django==1.1.2 
   pyodbc==4.0.32
# 安装依赖环境
	pip3 install -r requirements.txt
# 执行迁移命令：
	python3 manage.py makemigrations system
	python3 manage.py migrate
# 初始化数据
	python3 manage.py init
# 初始化省市县数据:
	python3 manage.py init_area
# 启动项目
	python3 manage.py runserver 0.0.0.0:8000
```
### 四、后端项目部署，启动

#### 后端部署

```shell
#1、将项目拷贝到目录下面并解压，例
cp backend.tar /home
tar -xvf backend.tar
#2、在setting中找到DataBases修改数据库连接串
cd backend/backend
vim settings.py
#3、修改uwsgi配置文件(只用修改前三项即可)
cd /backend/uwsgiConfig/
vim uwsgiConfig.ini
```
#### 定时器启动
```shell
python manage.py runapscheduler
```

### 访问项目

- 文档访问地址：[http://IP:端口/api/docs](http://localhost:8080/api/docs) (默认为此地址，如有修改请按照配置文件)
- 账号：`superadmin` 密码：`123456`


### 五、前端项目部署启动

#### 前端部署

```shell
#1、在文件夹中新建www/vue目录,例如在/home路径下
mkdir www
cd www
mkdir vue
#2、将前端项目拷贝到目录中并解压
cp web.tar /home/www/vue
tar -xvf web.tar
#3、配置nginx.conf(默认路径如下，如找不到以nginx安装的路径为准，配置详情见nginx配置内容)
vim /etc/nginx/nginx.conf
#4、修改完成配置之后启动nginx
systemctl start nginx
#5、检查nginx状态
systemctl status nginx
```

#### nginx配置文件
```shell
#在server语句块中修改，添加以下内容
server{
        listen       8080;#为前端访问接口
        listen       [::]:80;
        server_name  172.16.38.11;# 为当前服务器ip或者hostname
        root         /home/www/vue/dist;# 前端静态页面路径
        location / {
           # root         /home/www/vue/dist;
            try_files $uri $uri/ /index.html   #解决post请求出现404问题
            index  index.html index.htm;
         }
}
```

## 三.安装uwsgi

### 安装步骤

```shell
#1、进入项目中的RegStudioBackendPackages目录
cd BackendPackages
#2、解压源码包，可以使用以下命令：
tar -zxvf uwsgi-2.0.21.tar.gz
#3、进入 uwsgi 源码包的目录，如下所示：
cd uwsgi-2.0.21
#4、安装编译 uwsgi 所需的依赖项，可以使用以下命令：
yum install gcc make automake autoconf libtool python-devel
#5、编译 uwsgi，可以使用以下命令：
python uwsgiconfig.py --build
#6、将 uwsgi 目录复制到某个系统路径中，例如 /usr/local/bin：
cp uwsgi /usr/local/bin/
#7、确认 uwsgi 安装成功，可以使用以下命令：
uwsgi --version
#8、需要注意的是，在执行编译 uwsgi 命令时，需要在具有管理员权限的用户下运行。
```

#### 配置文件内容如下，例
```shell
# path:/RegStudioBackend/uwsgiConfig/uwsgiConfig.ini
# 内容
[uwsgi]
# 使用nginx链接时使用
#socket=/tmp/uwsgi.sock
#chmod-socket=666
#socket=172.16.38.11:8080
# 直接做web服务器使用 python manage.py runserver ip:port
http=172.16.38.11:8000
# 项目目录 [pwd查看 直接填，不需要引号]
chdir=/home/backend
# 项目中wsgi.py文件的目录，相对于项目目录
wsgi-file=/home/backend/backend/wsgi.py
# 指定启动的工作进程数
processes=4
# 指定工作进程中的线程数
threads=2
# 进程中，有一个主进程
master=True
# 保存启动之后主进程的pid
pidfile=uwsgi.pid
# 设置uwsgi后台运行, uwsgi.log 保存日志信息
daemonize=uwsgi.log
# 设置虚拟环境的路径 [cd .virtualenvs]
#virtualenv=true
buffer-size = 32768
```