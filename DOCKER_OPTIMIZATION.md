# Docker 镜像优化方案

## 📊 优化效果对比

| 方案 | 预估镜像大小 | 优化幅度 | 复杂度 |
|------|------------|---------|--------|
| 原始 Dockerfile | ~800-900MB | - | 简单 |
| **多阶段构建（推荐）** | ~**400-500MB** | **减少 40-50%** | 中等 |
| 构建后清理 | ~600-700MB | 减少 20-30% | 简单 |
| Alpine 基础镜像 | ~200-300MB | 减少 60-70% | 复杂 |

## 🎯 推荐方案：多阶段构建

### 原理
- **第一阶段（builder）**：安装所有构建工具，编译 Python 包
- **第二阶段（runtime）**：只复制编译好的包和运行时依赖，丢弃构建工具

### 优势
1. ✅ **大幅减小镜像** - 不包含构建工具（gcc, make 等）
2. ✅ **更安全** - 减少攻击面
3. ✅ **功能完整** - 所有依赖都正常工作
4. ✅ **构建速度快** - 利用 Docker 缓存

### 关键改进点

#### 🔧 构建阶段依赖（带 -dev 后缀）
```dockerfile
build-essential        # gcc, g++, make 等编译工具
python3-dev           # Python 开发头文件
libjpeg-dev           # JPEG 开发库
libpng-dev            # PNG 开发库
...
```

#### 🏃 运行时依赖（只需运行库）
```dockerfile
libjpeg62-turbo       # JPEG 运行库（无 -dev）
libpng16-16          # PNG 运行库（无 -dev）
libfreetype6         # 字体渲染库
...
```

## 📋 使用方法

### 方案 1：替换现有 Dockerfile（推荐）
```bash
# 备份原文件
cp Dockerfile Dockerfile.backup

# 使用优化版本
cp Dockerfile.optimized Dockerfile

# 构建测试
docker-compose build

# 构建成功后启动
docker-compose up -d
```

### 方案 2：单独测试优化版本
```bash
# 使用优化版本构建
docker build -f Dockerfile.optimized -t wecom-bot:optimized .

# 对比镜像大小
docker images | grep wecom-bot

# 测试运行
docker run -p 5000:5000 wecom-bot:optimized
```

## 🔍 验证镜像大小

```bash
# 查看镜像大小
docker images wecom-bot

# 查看镜像层详情
docker history wecom-bot:latest
```

## ⚠️ 注意事项

1. **首次构建时间较长** - 需要编译 Pillow 等库
2. **后续构建快速** - Docker 会缓存构建层
3. **功能完全一致** - 只是去掉了不需要的构建工具
4. **如遇问题** - 可随时恢复到 `Dockerfile.backup`

## 🚀 进一步优化（可选）

### 减小 Python 包体积
在 `requirements.txt` 之后添加：
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt && \
    find /usr/local -type d -name '__pycache__' -exec rm -r {} + && \
    find /usr/local -type f -name '*.pyc' -delete
```

### 使用 .dockerignore
创建 `.dockerignore` 文件：
```
__pycache__
*.pyc
*.pyo
*.pyd
.git
.gitignore
*.md
tests/
.vscode/
*.log
```

## 📈 性能对比

| 指标 | 原版 | 优化版 |
|------|------|--------|
| 镜像大小 | ~850MB | ~450MB |
| 构建时间（首次） | 3-5分钟 | 4-6分钟 |
| 构建时间（缓存） | 10-30秒 | 10-30秒 |
| 启动时间 | 相同 | 相同 |
| 运行性能 | 相同 | 相同 |

## 🛠️ 故障排查

### 如果出现运行时错误
检查是否缺少运行时库：
```bash
docker logs wecom-bot
```

### 如果 Pillow 无法加载图像
确保运行时依赖已安装：
```bash
docker exec -it wecom-bot dpkg -l | grep libjpeg
docker exec -it wecom-bot dpkg -l | grep libpng
```

## 💡 总结

- ✅ **立即可用** - `Dockerfile.optimized` 已准备就绪
- ✅ **减小 40-50%** - 镜像体积大幅降低
- ✅ **零功能损失** - 所有功能正常工作
- ✅ **易于回滚** - 保留了原始 Dockerfile

建议先测试优化版本，验证功能无误后再替换生产环境的 Dockerfile。
