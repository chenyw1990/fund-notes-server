# 基金购买记录系统

这是一个基金笔记记录系统，包含微信小程序和Web前端，后台使用Python语言，Flask框架，MySQL数据库。

## 项目结构

```
fund-notes-server/
├── app/                    # 应用主目录
│   ├── __init__.py         # 应用初始化
│   ├── config.py           # 配置文件
│   ├── models/             # 数据模型
│   │   ├── user.py         # 用户模型
│   │   ├── fund.py         # 基金模型
│   │   ├── note.py         # 笔记模型
│   │   └── purchase.py     # 购买记录模型
│   ├── api/                # API路由
│   │   ├── auth.py         # 认证API
│   │   ├── funds.py        # 基金API
│   │   ├── notes.py        # 笔记API
│   │   └── purchases.py    # 购买记录API
│   ├── web/                # Web前端路由
│   ├── services/           # 业务逻辑
│   ├── static/             # 静态资源(CSS, JS, 图片)
│   ├── templates/          # HTML模板
│   └── utils/              # 工具函数
├── migrations/             # 数据库迁移文件
├── .env                    # 环境变量
├── .env.example            # 环境变量示例
├── run.py                  # 应用入口
└── requirements.txt        # 依赖包
```

## 安装与设置

1. 克隆仓库
```bash
git clone <repository-url>
cd fund-notes-server
```

2. 创建虚拟环境并安装依赖
```bash
python -m venv venv
source venv/bin/activate  # 在Windows上使用 venv\Scripts\activate
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入正确的配置信息
```

4. 初始化数据库
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. 运行应用
```bash
python run.py
```

## API文档

### 用户认证
- `POST /api/auth/login`: 用户登录
- `POST /api/auth/register`: 用户注册

### 基金笔记
- `GET /api/notes`: 获取所有笔记
- `GET /api/notes/<id>`: 获取单个笔记
- `POST /api/notes`: 创建新笔记
- `PUT /api/notes/<id>`: 更新笔记
- `DELETE /api/notes/<id>`: 删除笔记

### 基金信息
- `GET /api/funds`: 获取基金列表
- `GET /api/funds/<code>`: 获取基金详情

### 购买记录
- `GET /api/purchases`: 获取用户购买记录
- `GET /api/purchases/<id>`: 获取单条购买记录
- `POST /api/purchases`: 创建新购买记录
- `PUT /api/purchases/<id>`: 更新购买记录
- `DELETE /api/purchases/<id>`: 删除购买记录

## Web前端

系统提供完整的Web前端界面，支持以下功能：

### 用户功能
- 用户注册和登录
- 个人资料管理
- 密码修改

### 基金功能
- 浏览基金列表
- 按类型和关键词筛选基金
- 查看基金详情

### 笔记功能
- 浏览所有公开笔记
- 创建、编辑和删除个人笔记
- 为笔记添加评分
- 设置笔记公开或私密状态

### 购买记录功能
- 记录基金购买信息（金额、份额、单价等）
- 查看和管理个人购买记录
- 按基金筛选购买记录
- 查看购买汇总信息（总投资、总份额、平均成本等）
- 基金代码快速搜索功能

### 访问方式
Web前端可通过以下URL访问:
```
http://[服务器IP]:5010/
```

## 部署

使用Gunicorn作为WSGI服务器:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## 技术栈

- 后端：Python, Flask, SQLAlchemy, Redis
- 前端：HTML, CSS, JavaScript, Bootstrap 5
- 数据库：MySQL
- 缓存：Redis 