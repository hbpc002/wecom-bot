# 企业微信听录音统计系统 - 部署文档

## 快速开始

### 方式一：Docker 部署（推荐）

1. **构建并启动容器**
```bash
docker-compose up -d
```

2. **访问系统**
- 打开浏览器访问：http://localhost:5000
- 默认用户名：admin
- 默认密码：admin123

3. **停止服务**
```bash
docker-compose down
```

### 方式二：本地部署

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **启动Web服务器**
```bash
python web_server.py
```

3. **访问系统**
- 打开浏览器访问：http://localhost:5000
- 默认用户名：admin
- 默认密码：admin123

## 功能说明

### 1. 文件上传
- 支持拖拽上传多个.zip格式的日志文件
- 支持点击选择文件上传
- 实时显示上传进度
- 自动处理并生成报表

### 2. 报表查询
- **日报表**：查看指定日期的听录音统计，包含当日次数和月累计
- **月报表**：查看指定月份的累计统计

### 3. 文件管理
- 查看已上传的所有文件
- 显示文件大小和修改时间

### 4. 数据库存储
- 自动保存所有听录音记录到SQLite数据库
- 自动生成日汇总和月汇总数据
- 支持历史数据查询

## 配置说明

### 修改默认密码

编辑 `web_server.py` 文件，修改以下部分：

```python
# 默认用户配置（生产环境请修改）
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'your_new_password'  # 修改为你的密码
```

### 修改数据库路径

默认数据库路径为 `data/wecom_bot.db`，如需修改，编辑 `web_server.py`：

```python
app.config['DATABASE_PATH'] = os.getenv('DATABASE_PATH', 'your_path/wecom_bot.db')
```

### 修改上传文件大小限制

默认最大上传100MB，如需修改，编辑 `web_server.py`：

```python
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB
```

## Docker配置

### 端口映射

默认映射5000端口，如需修改，编辑 `docker-compose.yml`：

```yaml
ports:
  - "8080:5000"  # 将本地8080端口映射到容器5000端口
```

### 数据持久化

数据文件和上传的文件会自动保存到以下目录：
- `./data` - 数据库文件
- `./file` - 上传的zip文件和生成的报表

## 原有命令行模式

系统保留了原有的命令行处理模式，可以独立使用：

```bash
# 立即处理当天文件
python main.py

# 定时任务模式
python main.py --schedule
```

## 注意事项

1. **团队映射文件**：确保 `file/team_mapping.csv` 文件存在且格式正确
2. **企业微信Webhook**：如需推送到企业微信，需在 `main.py` 中配置webhook_url
3. **首次登录**：首次登录后建议立即修改默认密码
4. **数据备份**：定期备份 `data` 目录中的数据库文件

## 故障排除

### 无法访问Web界面
- 检查防火墙是否开放5000端口
- 确认服务是否正常启动：`docker-compose logs` 或查看控制台输出

### 上传文件失败
- 检查文件格式是否为.zip
- 检查文件大小是否超过限制
- 查看日志文件 `test_message.log`

### 数据库错误
- 确保 `data` 目录有写入权限
- 检查数据库文件是否损坏

## 技术支持

如有问题，请查看日志文件：
- Web服务日志：控制台输出
- 文件处理日志：`test_message.log`
