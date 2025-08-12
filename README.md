# 律师办案智能助手

一个集成了PDF文档管理、目录提取、用户认证和卷宗管理功能的智能办案助手系统。

## 功能特性

### 🔐 用户管理
- 用户注册和登录
- 密码加密存储
- 会话管理
- 用户权限控制

### 📁 卷宗管理
- 创建和管理卷宗
- PDF文件上传和存储
- 卷宗信息编辑
- 卷宗列表查看

### 📋 目录管理
- 自动从PDF提取目录
- 手动添加和编辑目录项
- 目录序号、文件名称、页码管理
- 点击页码跳转功能

### 📄 PDF处理
- PDF文件解析和显示
- 目录内容智能识别
- 支持多种PDF格式

### 💬 智能对话
- 集成聊天界面
- 支持文档相关问答
- 智能助手功能

## 系统要求

- Python 3.8+
- MySQL 8.0+
- Windows 10+ (主要测试环境)

## 安装步骤

### 1. 克隆项目
```bash
git clone https://github.com/zygcool/lawyer-assistant-backup.git
cd lawyer-assistant-backup
```

### 2. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 3. 配置数据库

#### 3.1 创建MySQL数据库
```sql
CREATE DATABASE lawyer_assistant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 3.2 创建数据库用户（可选）
```sql
CREATE USER 'lawyer_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON lawyer_assistant.* TO 'lawyer_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 3.3 导入数据库结构
```bash
mysql -u root -p lawyer_assistant < database_schema.sql
```

### 4. 配置数据库连接

编辑 `database_config.py` 文件中的数据库配置：

```python
class DatabaseConfig:
    HOST = 'localhost'
    PORT = 3306
    DATABASE = 'lawyer_assistant'
    USERNAME = 'lawyer_user'  # 或 'root'
    PASSWORD = 'your_password'
```

### 5. 启动应用程序

```bash
python app.py
```

或者直接运行登录窗口：

```bash
python login_window.py
```

## 使用说明

### 首次使用

1. **启动应用程序**：运行 `python app.py`
2. **创建账户**：点击"立即注册"创建新用户账户
3. **登录系统**：使用创建的账户登录

### 默认管理员账户

如果运行了 `app.py`，系统会自动创建默认管理员账户：
- 用户名：`admin`
- 密码：`admin123`

**⚠️ 请在首次登录后立即修改默认密码！**

### 卷宗管理

1. **添加卷宗**：
   - 点击左侧卷宗管理区域的 ➕ 按钮
   - 选择PDF文件
   - 填写卷宗信息（名称、编号、描述）
   - 确认添加

2. **查看卷宗**：
   - 在卷宗列表中点击任意卷宗
   - 系统会加载PDF内容和目录信息

3. **管理目录**：
   - **自动提取**：点击"📄 提取"按钮从PDF自动提取目录
   - **手动添加**：点击"➕ 添加"按钮手动添加目录项
   - **编辑目录**：双击目录项进行编辑
   - **页码跳转**：点击页码数字跳转到对应页面

### 目录格式要求

系统支持以下格式的PDF目录自动识别：
- `1 文件名称 10`
- `1. 文件名称 10`
- `(1) 文件名称 10`
- `1） 文件名称 10`

目录项格式：**序号 + 中文文件名 + 页码**

## 项目结构

```
律师办案智能助手/
├── app.py                 # 主启动程序
├── login_window.py        # 登录窗口
├── main_with_db.py        # 集成数据库的主程序
├── database_config.py     # 数据库配置和操作
├── database_schema.sql    # 数据库结构
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
└── main.py               # 原始主程序（无数据库）
```

## 数据库结构

### 主要表结构

- **users**: 用户信息表
- **cases**: 卷宗信息表
- **case_directories**: 卷宗目录表
- **user_sessions**: 用户会话表
- **operation_logs**: 操作日志表

详细结构请参考 `database_schema.sql` 文件。

## 开发说明

### 技术栈

- **前端界面**: Python Tkinter
- **数据库**: MySQL 8.0
- **PDF处理**: PyPDF2, pdfplumber, PyMuPDF
- **图像处理**: Pillow
- **数据库连接**: mysql-connector-python

### 核心模块

1. **DatabaseManager**: 数据库连接和操作管理
2. **UserManager**: 用户认证和会话管理
3. **CaseManager**: 卷宗管理
4. **DirectoryManager**: 目录管理
5. **PDFChatApp**: 主应用程序界面

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 验证数据库配置信息
   - 确认用户权限

2. **PDF文件无法加载**
   - 检查文件路径是否正确
   - 确认PDF文件未损坏
   - 验证文件权限

3. **目录提取失败**
   - 检查PDF是否包含文本内容
   - 验证目录格式是否符合要求
   - 尝试手动添加目录项

4. **依赖包安装失败**
   - 更新pip: `python -m pip install --upgrade pip`
   - 使用国内镜像: `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`

### 日志查看

系统运行日志存储在数据库的 `operation_logs` 表中，可以通过以下SQL查询：

```sql
SELECT * FROM operation_logs ORDER BY created_at DESC LIMIT 100;
```

## 更新日志

### v1.0.0 (当前版本)
- 初始版本发布
- 用户认证系统
- 卷宗管理功能
- PDF目录提取
- 基础聊天界面

## 许可证

本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。

## 联系方式

如有问题或建议，请联系开发团队。

---

**注意**: 本系统仅供学习和研究使用，在生产环境中使用前请进行充分测试。