# 企微听录音统计报表系统

一个基于 Flask 的 Web 应用系统，用于自动处理听录音操作日志，生成统计报表并发送到企业微信群。

## 功能特性

### 核心功能

1. **Web 管理界面**
   - 用户登录认证
   - 文件拖拽上传
   - 在线报表查询
   - 团队组长管理
   - 定时任务配置

2. **数据处理**
   - 自动解析 ZIP 格式的操作日志
   - 智能识别中文编码（GBK、UTF-8、GB2312等）
   - 自动去重，防止重复上传
   - SQLite 数据库持久化存储

3. **报表生成**
   - 日报表：显示当日听录音次数和月累计次数
   - 月报表：显示整月累计统计
   - 图片报表：生成美观的图表图片
   - 文本报表：纯文本格式摘要

4. **企微集成**
   - 手动发送到测试/生产环境
   - 定时自动推送（可配置时间）
   - 智能选择前一天数据
   - 自动上传图片并发送

5. **数据管理**
   - 文件列表查看
   - 文件删除管理
   - 历史数据查询
   - 自动清理过期文件

## 文件结构

```
wecom-bot/
├── web_server.py          # Flask Web 服务器主程序
├── main.py                # 命令行处理模块（被 web_server 调用）
├── database.py            # SQLite 数据库管理
├── report_generator.py    # 报表图片生成器
├── requirements.txt       # Python 依赖包
├── DEPLOYMENT.md          # 详细部署文档
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── run.bat                # Windows 快速启动脚本
├── data/                  # 数据目录
│   └── wecom_bot.db       # SQLite 数据库文件
├── file/                  # 文件存储目录
│   └── *.zip              # 上传的日志文件
├── templates/             # HTML 模板
│   ├── index.html         # 主界面
│   └── login.html         # 登录页面
└── static/                # 静态资源
    ├── css/               # 样式文件
    └── js/                # JavaScript 文件
```

## 快速开始

### 方式一：本地运行（推荐）

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **启动服务**
```bash
python web_server.py
```

3. **访问系统**
- 浏览器访问：http://localhost:5000
- 默认用户名：`admin`
- 默认密码：`admin123`

### 方式二：Docker 部署

```bash
docker-compose up -d
```

详细部署说明请参考 [DEPLOYMENT.md](DEPLOYMENT.md)

## 依赖包

```
Flask==3.0.0
Flask-Login==0.6.3
Werkzeug==3.0.1
requests==2.31.0
schedule==1.2.0
chardet==5.2.0
Pillow==8.2.0
```

## 使用指南

### 1. 团队组长管理

首次使用需要在"团队组长管理"页面配置团队信息：
- 团队名称：如"客服部"
- 组长姓名
- 组长账号：如"KF77100064"

### 2. 上传日志文件

在主界面上传 ZIP 格式的操作日志文件：
- 支持拖拽上传
- 支持多文件批量上传
- 自动解析并存入数据库
- 自动生成日报表和月报表

### 3. 查看报表

- **日报表**：选择日期查看当日统计，包含月累计信息
- **月报表**：选择年月查看整月累计统计
- 支持按团队、个人查看详细数据

### 4. 推送到企微

- **测试环境**：点击"发送到测试环境"按钮立即发送
- **生产环境**：点击"发送到生产环境"按钮发送正式报表
- **定时推送**：在设置中启用定时任务，每天自动推送

### 5. 定时任务配置

在"定时任务设置"中：
- 启用/禁用定时任务
- 设置每天推送时间（默认10:00）
- 定时任务会自动发送前一天的数据

## 配置说明

### 修改登录密码

编辑 `web_server.py`，修改以下部分：

```python
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'your_new_password'  # 修改为新密码
```

### 修改企微 Webhook

编辑 `web_server.py`，修改以下部分：

```python
WEBHOOK_TEST = "your_test_webhook_url"  # 测试环境
WEBHOOK_PROD = "your_prod_webhook_url"  # 生产环境
```

### 修改数据库路径

编辑 `web_server.py`：

```python
app.config['DATABASE_PATH'] = 'your/path/wecom_bot.db'
```

### 修改上传限制

默认最大上传 100MB，如需修改：

```python
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB
```

## 报表格式

生成的图片报表包含：
- 📊 报表标题和日期
- 📈 汇总信息（总次数、参与人数、平均次数、月累计）
- 📋 详细排名表格（排名、团队、姓名、账号、当日次数、月累计次数）
- 🎨 美观的表格样式和配色

## 日志说明

程序运行日志保存在 `test_message.log`，包含：
- Web 服务器启动信息
- 文件上传处理记录
- 数据库操作日志
- 企微推送结果
- 错误详细信息

## 故障排除

### 无法访问 Web 界面
- 检查 5000 端口是否被占用
- 查看控制台是否有启动错误
- 确认防火墙是否开放端口

### 文件上传失败
- 确认文件格式为 `.zip`
- 检查文件大小是否超过限制
- 查看 `test_message.log` 获取详细错误

### 报表数据为空
- 确认已在"团队组长管理"中配置团队信息
- 检查上传的 ZIP 文件中是否包含有效的 CSV 数据
- 验证 CSV 中的账号与团队组长账号是否匹配

### 企微推送失败
- 确认 Webhook URL 配置正确
- 检查网络连接是否正常
- 查看日志中的详细错误信息

## 命令行模式（可选）

系统保留了命令行处理模式，可独立使用：

```bash
# 立即处理当天文件
python main.py

# 定时任务模式
python main.py --schedule
```

## 技术支持

如有问题，请：
1. 查看 `test_message.log` 日志文件
2. 检查控制台输出信息
3. 参考 `DEPLOYMENT.md` 部署文档