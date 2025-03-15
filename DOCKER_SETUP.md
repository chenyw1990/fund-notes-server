# 使用Docker设置基金笔记后台服务

本文档提供了使用Docker设置基金笔记后台服务的步骤。

## 前提条件

- 安装 [Docker](https://docs.docker.com/get-docker/)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/)

## 启动MySQL和Redis容器

1. 在项目根目录下运行以下命令启动MySQL和Redis容器：

```bash
docker-compose up -d
```

这将在后台启动MySQL和Redis容器。

2. 验证容器是否正在运行：

```bash
docker-compose ps
```

你应该看到`fund_notes_mysql`和`fund_notes_redis`容器的状态为`Up`。

## 配置应用程序

1. 确保`.env`文件中的数据库和Redis配置与Docker Compose配置匹配：

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=fund_user
DB_PASSWORD=fund_password
DB_NAME=fund_notes

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## 初始化数据库

1. 创建虚拟环境并安装依赖：

```bash
python -m venv venv
source venv/bin/activate  # 在Windows上使用 venv\Scripts\activate
pip install -r requirements.txt
```

2. 运行初始化脚本：

```bash
python init_db.py
```

## 运行应用程序

启动应用程序：

```bash
python run.py
```

应用程序将在 http://localhost:5000 上运行。

## 停止容器

当你完成工作后，可以停止容器：

```bash
docker-compose down
```

如果你想同时删除卷（这将删除所有数据），使用：

```bash
docker-compose down -v
```

## 连接到MySQL容器

如果你需要直接连接到MySQL容器，可以使用以下命令：

```bash
docker exec -it fund_notes_mysql mysql -ufund_user -pfund_password fund_notes
```

## 查看Redis数据

如果你需要查看Redis中的数据，可以使用以下命令：

```bash
docker exec -it fund_notes_redis redis-cli
``` 