# RPA Tools - 社交媒体内容抓取工具

一个基于 Playwright 的自动化内容抓取工具，支持小红书、抖音和今日头条的内容提取和数据分析。

## 🌟 功能特性

- **多平台支持**: 支持小红书、抖音、今日头条三大主流社交媒体平台
- **内容抓取**: 自动提取帖子标题、作者、点赞数、评论数、发布时间等信息
- **媒体下载**: 支持图片和视频内容的下载
- **并发处理**: 基于 FastAPI 的异步处理，支持多并发任务
- **Docker 支持**: 提供完整的 Docker 容器化部署方案
- **配置文件**: 灵活的 XPath 配置，适应不同页面结构
- **数据存储**: 结构化 JSON 数据输出，便于后续分析

## 🏗️ 项目结构

```
RPA_tools/
├── Scripts/                  # 脚本工具
│   ├── debug_browser.py     # 浏览器调试工具
│   └── get_data.py          # 数据获取脚本
├── data/                     # 数据存储目录
│   ├── douyin.json          # 抖音数据
│   ├── toutiao.json         # 头条数据
│   └── xiaohongshu.json     # 小红书数据
├── RPA_douyin.py            # 抖音内容抓取模块，可单独运行
├── RPA_toutiao.py           # 今日头条内容抓取模块，可单独运行
├── RPA_xhs_sharelk.py       # 小红书内容抓取模块，可单独运行
├── server.py                # FastAPI 服务主程序
├── config.py                # 配置文件（包含 XPath 配置、服务器配置）
├── client_example.py        # 客户端示例代码（包含 POST 请求示例）
├── Dockerfile               # Docker 构建文件
└── pyproject.toml           # 项目依赖配置
```

## 🚀 快速开始

### 安装依赖

```bash
# 使用 UV 安装依赖
uv sync

# 安装 Playwright 浏览器
playwright install chromium
```

### 启动服务

```bash
# 启动 FastAPI 服务
python server.py

# 或使用 UV 运行
uv run server.py
```

服务将在 `http://localhost:8000` 启动

### 测试接口

```bash
# 运行客户端测试
python client_example.py
```

## 📡 API 接口

### 健康检查
```
GET /health
```

### 小红书内容抓取
```
POST /xhs
Content-Type: application/json

{
    "url": "http://xhslink.com/xxx",
    "download_img": true,
    "headless": true
}
```

### 抖音内容抓取
```
POST /douyin
Content-Type: application/json

{
    "url": "https://v.douyin.com/xxx",
    "download_video": false,
    "headless": true
}
```

### 今日头条内容抓取
```
POST /toutiao
Content-Type: application/json

{
    "url": "https://www.toutiao.com/w/xxx",
    "download_video": false,
    "headless": true
}
```

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -t rpa-tools .
```

### 运行容器

```bash
docker run -p 8000:8000 rpa-tools
```

## ⚙️ 配置说明

### 并发控制

服务默认使用 3 个工作进程，可以通过修改 `PROFILE_PATHS` 在 `server.py` 中调整并发数：

```python
PROFILE_PATHS = [
    str(BASE_DIR / "profiles" / "worker_1"),
    str(BASE_DIR / "profiles" / "worker_2"),
    str(BASE_DIR / "profiles" / "worker_3"),
]
```

### XPath 配置

每个平台的 XPath 配置都在 `config.py` 中定义，可以根据页面结构变化进行调整：

- **抖音**: 支持视频和图文两种内容类型
- **小红书**: 支持笔记内容抓取
- **今日头条**: 支持微头条和视频内容


## 🔧 开发指南

### 添加新平台

1. 创建新的 RPA 模块（参考 `RPA_douyin.py`）
2. 在 `config.py` 中添加平台 XPath 配置
3. 在 `server.py` 中添加 API 端点
4. 更新客户端示例代码

### 调试模式

```python
# 在请求中设置 headless=false 启用浏览器界面
{
    "url": "xxx",
    "headless": False
}

# 或者使用 debug_browser.py 调试
python Scripts/debug_browser.py
```

## 📝 注意事项

1. **反爬策略**: 工具使用 Playwright 模拟真实浏览器行为，但仍需注意请求频率
2. **XPath 维护**: 社交媒体平台经常更新页面结构，可能需要定期维护 XPath 配置
3. **并发限制**: 建议根据目标平台的限制调整并发数
4. **数据存储**: 抓取的数据默认保存在 `data/` 目录下

## ⚠️ 免责声明

本工具仅供学习和研究使用，请遵守相关平台的服务条款。