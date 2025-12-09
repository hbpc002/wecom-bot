# 多阶段构建：第一阶段 - 构建环境
FROM python:3.11-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖到临时目录
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 多阶段构建：第二阶段 - 运行环境
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 只安装运行时需要的库（不包括构建工具）
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    fonts-symbola \
    locales \
    # Pillow 运行时依赖（不需要 -dev 包）
    libjpeg62-turbo \
    libpng16-16 \
    libfreetype6 \
    liblcms2-2 \
    libopenjp2-7 \
    libtiff6 \
    libwebp7 \
    libharfbuzz0b \
    libfribidi0 \
    && rm -rf /var/lib/apt/lists/*

# 配置 locale 为 UTF-8
RUN sed -i '/zh_CN.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen zh_CN.UTF-8

# 从构建阶段复制已安装的Python包
COPY --from=builder /install /usr/local

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/file /app/data

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=web_server.py


ENV LANG=zh_CN.UTF-8
ENV LC_ALL=zh_CN.UTF-8
ENV PYTHONIOENCODING=utf-8

# 启动命令(使用Gunicorn生产服务器)
CMD ["gunicorn", "-c", "gunicorn.conf.py", "web_server:app"]
