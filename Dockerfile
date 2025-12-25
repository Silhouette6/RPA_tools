# 使用指定的 Playwright 官方镜像 (基于 Ubuntu Noble)
FROM mcr.microsoft.com/playwright/python:v1.56.0-noble

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# 允许 uv 在系统 Python 环境安装包
ENV UV_SYSTEM_PYTHON=1

# 设置工作目录
WORKDIR /app

# 从官方镜像引入 uv (高性能 Python 包管理器)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 复制依赖定义文件
COPY pyproject.toml ./

# 安装依赖
# 注意：官方镜像自带 Python 3.12 左右，我们会自动安装项目依赖
RUN uv sync -i https://mirrors.aliyun.com/pypi/simple

# 官方镜像已经预装了浏览器，但为了确保版本匹配，我们可以运行一次安装
# 仅安装 Chromium 即可
# RUN playwright install chromium

# 复制项目所有代码
COPY . .

# 创建必要的数据目录和 Profile 目录
RUN mkdir -p data/xhs data/douyin data/toutiao profiles

# 暴露 FastAPI 端口
EXPOSE 8000

# 启动服务
CMD ["uv", "run", "server.py"]
