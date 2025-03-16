# 基金笔记微信小程序 API 文档

本文档详细说明了基金笔记微信小程序后台服务的 API 接口。

## 基础信息

- 基础URL: `http://your-server-domain/api`
- 所有请求和响应均使用 JSON 格式
- 认证方式: JWT (JSON Web Token)
- 在需要认证的接口中，请在 HTTP 头部添加 `Authorization: Bearer {token}`

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（未登录或 token 无效） |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 用户认证 API

### 用户注册

- **URL**: `/auth/register`
- **方法**: `POST`
- **认证**: 不需要
- **请求参数**:

```json
{
  "username": "用户名",
  "password": "密码",
  "email": "邮箱地址"
}
```

- **成功响应** (201):

```json
{
  "message": "注册成功",
  "access_token": "JWT令牌",
  "user": {
    "id": 1,
    "username": "用户名",
    "email": "邮箱地址",
    "avatar": "头像URL",
    "created_at": "创建时间",
    "updated_at": "更新时间"
  }
}
```

- **错误响应**:
  - 400: 缺少必要字段
  - 400: 用户名已存在
  - 400: 邮箱已存在

### 用户登录

- **URL**: `/auth/login`
- **方法**: `POST`
- **认证**: 不需要
- **请求参数**:

```json
{
  "username": "用户名",
  "password": "密码"
}
```

- **成功响应** (200):

```json
{
  "message": "登录成功",
  "access_token": "JWT令牌",
  "user": {
    "id": 1,
    "username": "用户名",
    "email": "邮箱地址",
    "avatar": "头像URL",
    "created_at": "创建时间",
    "updated_at": "更新时间"
  }
}
```

- **错误响应**:
  - 400: 缺少必要字段
  - 401: 用户名或密码错误

### 微信小程序登录

- **URL**: `/auth/wechat_login`
- **方法**: `POST`
- **认证**: 不需要
- **请求参数**:

```json
{
  "code": "微信登录凭证"
}
```

- **成功响应** (200):

```json
{
  "message": "登录成功",
  "access_token": "JWT令牌",
  "user": {
    "id": 1,
    "username": "用户名",
    "email": "邮箱地址",
    "avatar": "头像URL",
    "created_at": "创建时间",
    "updated_at": "更新时间"
  }
}
```

- **错误响应**:
  - 400: 缺少code字段
  - 400: 微信登录失败
  - 500: 微信服务器请求失败

### 获取用户资料

- **URL**: `/auth/profile`
- **方法**: `GET`
- **认证**: 需要
- **请求参数**: 无

- **成功响应** (200):

```json
{
  "id": 1,
  "username": "用户名",
  "email": "邮箱地址",
  "avatar": "头像URL",
  "created_at": "创建时间",
  "updated_at": "更新时间"
}
```

- **错误响应**:
  - 401: 未授权
  - 404: 用户不存在

### 更新用户资料

- **URL**: `/auth/profile`
- **方法**: `PUT`
- **认证**: 需要
- **请求参数**:

```json
{
  "username": "新用户名",  // 可选
  "email": "新邮箱",      // 可选
  "avatar": "新头像URL"   // 可选
}
```

- **成功响应** (200):

```json
{
  "message": "资料更新成功",
  "user": {
    "id": 1,
    "username": "用户名",
    "email": "邮箱地址",
    "avatar": "头像URL",
    "created_at": "创建时间",
    "updated_at": "更新时间"
  }
}
```

- **错误响应**:
  - 400: 用户名已存在
  - 400: 邮箱已存在
  - 401: 未授权
  - 404: 用户不存在

## 基金 API

### 获取基金列表

- **URL**: `/funds`
- **方法**: `GET`
- **认证**: 不需要
- **请求参数**:
  - `keyword`: 搜索关键字（可选）
  - `type`: 基金类型（可选）
  - `page`: 页码，默认为1
  - `per_page`: 每页数量，默认为10

- **成功响应** (200):

```json
{
  "funds": [
    {
      "id": 1,
      "code": "000001",
      "name": "华夏成长混合",
      "type": "混合型",
      "manager": "王经理",
      "company": "华夏基金",
      "inception_date": "2020-01-01",
      "size": 56.78,
      "description": "该基金是一只混合型基金，投资于股票和债券市场。",
      "created_at": "创建时间",
      "updated_at": "更新时间"
    },
    // 更多基金...
  ],
  "total": 100,
  "pages": 10,
  "current_page": 1
}
```

### 获取基金详情

- **URL**: `/funds/{code}`
- **方法**: `GET`
- **认证**: 不需要
- **请求参数**: 无

- **成功响应** (200):

```json
{
  "id": 1,
  "code": "000001",
  "name": "华夏成长混合",
  "type": "混合型",
  "manager": "王经理",
  "company": "华夏基金",
  "inception_date": "2020-01-01",
  "size": 56.78,
  "description": "该基金是一只混合型基金，投资于股票和债券市场。",
  "notes_count": 5,
  "created_at": "创建时间",
  "updated_at": "更新时间"
}
```

- **错误响应**:
  - 404: 基金不存在

### 搜索基金

- **URL**: `/funds/search`
- **方法**: `GET`
- **认证**: 不需要
- **请求参数**:
  - `keyword`: 搜索关键字（必填）

- **成功响应** (200):

```json
[
  {
    "id": 1,
    "code": "000001",
    "name": "华夏成长混合",
    "type": "混合型",
    "manager": "王经理",
    "company": "华夏基金",
    "inception_date": "2020-01-01",
    "size": 56.78,
    "description": "该基金是一只混合型基金，投资于股票和债券市场。",
    "created_at": "创建时间",
    "updated_at": "更新时间"
  },
  // 更多基金...
]
```

- **错误响应**:
  - 400: 请提供搜索关键字

### 从天天基金网查询基金信息

- **URL**: `/funds/query_external/{code}`
- **方法**: `GET`
- **认证**: 不需要
- **请求参数**: 无

- **成功响应** (200):

```json
{
  "fundcode": "161725",
  "name": "招商中证白酒指数(LOF)",
  "jzrq": "2023-05-09",
  "dwjz": "1.5439",
  "gsz": "1.6183",
  "gszzl": "4.82",
  "gztime": "2023-05-10 15:00",
  "fund_type": "指数型",
  "manager": "侯昊",
  "found_date": "2015-05-27",
  "company": "招商基金"
}
```

- **错误响应**:
  - 500: 天天基金网API请求失败
  - 500: 天天基金网API返回数据格式错误
  - 500: 查询天天基金网API失败

### 从天天基金网同步基金信息

- **URL**: `/funds/sync_from_external/{code}`
- **方法**: `POST`
- **认证**: 需要
- **请求参数**: 无

- **成功响应** (200):

```json
{
  "message": "基金 000001 同步成功"
}
```

- **错误响应**:
  - 401: 未授权
  - 500: 天天基金网API请求失败
  - 500: 天天基金网API返回数据格式错误
  - 500: 从天天基金网同步基金信息失败

### 同步基金数据

- **URL**: `/funds/sync`
- **方法**: `POST`
- **认证**: 需要
- **请求参数**: 无

- **成功响应** (200):

```json
{
  "message": "基金数据同步成功"
}
```

- **错误响应**:
  - 401: 未授权

### 获取基金相关笔记

- **URL**: `/funds/{code}/notes`
- **方法**: `GET`
- **认证**: 不需要
- **请求参数**:
  - `page`: 页码，默认为1
  - `per_page`: 每页数量，默认为10

- **成功响应** (200):

```json
{
  "notes": [
    {
      "id": 1,
      "title": "笔记标题",
      "content": "笔记内容",
      "rating": 5,
      "user_id": 1,
      "fund_id": 1,
      "is_public": true,
      "created_at": "创建时间",
      "updated_at": "更新时间",
      "author": {
        "id": 1,
        "username": "用户名",
        "avatar": "头像URL"
      }
    },
    // 更多笔记...
  ],
  "total": 20,
  "pages": 2,
  "current_page": 1
}
```

- **错误响应**:
  - 404: 基金不存在

## 笔记 API

### 获取笔记列表

- **URL**: `/notes`
- **方法**: `GET`
- **认证**: 不需要
- **请求参数**:
  - `fund_id`: 基金ID（可选）
  - `user_id`: 用户ID（可选）
  - `page`: 页码，默认为1
  - `per_page`: 每页数量，默认为10

- **成功响应** (200):

```json
{
  "notes": [
    {
      "id": 1,
      "title": "笔记标题",
      "content": "笔记内容",
      "rating": 5,
      "user_id": 1,
      "fund_id": 1,
      "is_public": true,
      "created_at": "创建时间",
      "updated_at": "更新时间",
      "author": {
        "id": 1,
        "username": "用户名",
        "avatar": "头像URL"
      },
      "fund": {
        "id": 1,
        "code": "000001",
        "name": "华夏成长混合"
      }
    },
    // 更多笔记...
  ],
  "total": 50,
  "pages": 5,
  "current_page": 1
}
```

### 获取单个笔记

- **URL**: `/notes/{note_id}`
- **方法**: `GET`
- **认证**: 如果笔记不公开，则需要认证
- **请求参数**: 无

- **成功响应** (200):

```json
{
  "id": 1,
  "title": "笔记标题",
  "content": "笔记内容",
  "rating": 5,
  "user_id": 1,
  "fund_id": 1,
  "is_public": true,
  "created_at": "创建时间",
  "updated_at": "更新时间",
  "author": {
    "id": 1,
    "username": "用户名",
    "avatar": "头像URL"
  },
  "fund": {
    "id": 1,
    "code": "000001",
    "name": "华夏成长混合"
  }
}
```

- **错误响应**:
  - 403: 无权访问此笔记
  - 404: 笔记不存在

### 创建笔记

- **URL**: `/notes`
- **方法**: `POST`
- **认证**: 需要
- **请求参数**:

```json
{
  "title": "笔记标题",
  "content": "笔记内容",
  "rating": 5,           // 可选，1-5星评分
  "fund_id": 1,
  "is_public": true      // 可选，默认为true
}
```

- **成功响应** (201):

```json
{
  "message": "笔记创建成功",
  "note": {
    "id": 1,
    "title": "笔记标题",
    "content": "笔记内容",
    "rating": 5,
    "user_id": 1,
    "fund_id": 1,
    "is_public": true,
    "created_at": "创建时间",
    "updated_at": "更新时间"
  }
}
```

- **错误响应**:
  - 400: 缺少必要字段
  - 401: 未授权
  - 404: 基金不存在

### 更新笔记

- **URL**: `/notes/{note_id}`
- **方法**: `PUT`
- **认证**: 需要
- **请求参数**:

```json
{
  "title": "新标题",      // 可选
  "content": "新内容",    // 可选
  "rating": 4,           // 可选
  "is_public": false     // 可选
}
```

- **成功响应** (200):

```json
{
  "message": "笔记更新成功",
  "note": {
    "id": 1,
    "title": "新标题",
    "content": "新内容",
    "rating": 4,
    "user_id": 1,
    "fund_id": 1,
    "is_public": false,
    "created_at": "创建时间",
    "updated_at": "更新时间"
  }
}
```

- **错误响应**:
  - 401: 未授权
  - 403: 无权更新此笔记
  - 404: 笔记不存在

### 删除笔记

- **URL**: `/notes/{note_id}`
- **方法**: `DELETE`
- **认证**: 需要
- **请求参数**: 无

- **成功响应** (200):

```json
{
  "message": "笔记删除成功"
}
```

- **错误响应**:
  - 401: 未授权
  - 403: 无权删除此笔记
  - 404: 笔记不存在

## 数据结构

### 用户 (User)

```json
{
  "id": 1,
  "username": "用户名",
  "email": "邮箱地址",
  "avatar": "头像URL",
  "created_at": "创建时间",
  "updated_at": "更新时间"
}
```

### 基金 (Fund)

```json
{
  "id": 1,
  "code": "000001",
  "name": "华夏成长混合",
  "type": "混合型",
  "manager": "王经理",
  "company": "华夏基金",
  "inception_date": "2020-01-01",
  "size": 56.78,
  "description": "该基金是一只混合型基金，投资于股票和债券市场。",
  "created_at": "创建时间",
  "updated_at": "更新时间"
}
```

### 笔记 (Note)

```json
{
  "id": 1,
  "title": "笔记标题",
  "content": "笔记内容",
  "rating": 5,
  "user_id": 1,
  "fund_id": 1,
  "is_public": true,
  "created_at": "创建时间",
  "updated_at": "更新时间"
}
```

## 认证说明

本 API 使用 JWT (JSON Web Token) 进行认证。在需要认证的接口中，请在 HTTP 头部添加：

```
Authorization: Bearer {token}
```

其中 `{token}` 是通过登录或注册接口获取的 `access_token`。

## 错误处理

所有 API 在发生错误时会返回相应的 HTTP 状态码和错误信息：

```json
{
  "message": "错误信息"
}
``` 