# 基金笔记微信小程序后台服务

这是一个名叫基金笔记的基金购买记录的微信小程序的后台服务，使用Python语言，Flask框架，MySQL数据库。

## 项目结构

```
fund-notes-server/
├── app/                    # 应用主目录
│   ├── __init__.py         # 应用初始化
│   ├── config.py           # 配置文件
│   ├── models/             # 数据模型
│   ├── api/                # API路由
│   ├── services/           # 业务逻辑
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

## 部署

使用Gunicorn作为WSGI服务器:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
``` 