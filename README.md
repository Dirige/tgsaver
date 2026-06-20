<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white" alt="Telegram">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/github/license/dustinky/tgsaver" alt="License">
</p>

<h1 align="center">🎬 TGSaver</h1>

<p align="center">
  <b>智能 Telegram 视频下载助手</b><br>
  转发视频 → 自动识别 → 一键分类 → 整理入库
</p>

---

<p align="center">
  <a href="https://github.com/Dirige/tgsaver">📦 GitHub</a> •
  <a href="https://hub.docker.com/r/dustinky/tgsaver">🐳 Docker Hub</a>
</p>

---

## ✨ 功能亮点

- 🧠 **智能解析** — 自动识别文件名中的标题、季数、集数、年份、分辨率
- 📂 **自动分类** — 支持电影、电视剧、动漫、Cosplay 及自定义分类
- ✏️ **灵活编辑** — 下载前可修改标题、季数、集数
- 📁 **规范存储** — 自动生成标准媒体库文件夹结构
- 🐳 **Docker 部署** — 一条命令启动，开箱即用
- 🔒 **用户白名单** — 限制谁可以使用 Bot

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/Dirige/tgsaver.git
cd tgsaver

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 3. 启动服务
docker compose up -d

# 4. 查看日志
docker compose logs -f
```

### 方式二：直接运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
nano .env

# 3. 启动 Bot
python bot.py
```

---

## ⚙️ 配置说明

编辑 `.env` 文件：

```env
# Telegram Bot Token（从 @BotFather 获取）
BOT_TOKEN=your_bot_token_here

# 允许的用户 ID（逗号分隔，留空=不限制）
ALLOWED_USERS=123456789,987654321

# 下载目录
DOWNLOAD_DIR=/downloads

# Telegram 代理（可选）
PROXY_URL=socks5://127.0.0.1:6891

# Telegram API 凭证（用于大文件下载）
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_SESSION_STRING=your_session_string
```

### 获取 Telegram API 凭证

1. 访问 https://my.telegram.org
2. 登录你的 Telegram 账号
3. 进入「API development tools」
4. 创建应用，获取 `api_id` 和 `api_hash`

### 获取 Session String（可选，用于大文件下载）

```bash
# 运行登录脚本
python login.py
```

---

## 📂 文件夹结构

TGSaver 会自动创建规范的媒体库结构：

```
📁 /downloads
├── 🎬 电影
│   └── 肖申克的救赎 (1994)
│       └── 肖申克的救赎 (1994).mp4
├── 📺 电视剧
│   └── 狂飙
│       └── Season 01
│           └── 狂飙 - S01E01.mp4
├── 🎌 动漫
│   └── 鬼灭之刃
│       └── Season 01
│           └── 鬼灭之刃 - S01E05.mp4
├── 🎭 cosplay
│   └── 某视频
│       └── 某视频.mp4
└── 📁 自定义文件夹
    └── 其他内容.mp4
```

---

## 🎯 使用方法

### 基本流程

```
1️⃣ 转发视频给 Bot
      ↓
2️⃣ Bot 解析文件名，显示信息
      ↓
3️⃣ 选择类型（电影/电视剧/动漫/Cosplay/其他）
      ↓
4️⃣ 确认或修改信息
      ↓
5️⃣ 下载完成！
```

### 支持的命令

| 命令 | 说明 |
|------|------|
| `/start` | 启动 Bot，显示欢迎信息 |
| `/help` | 显示帮助信息 |
| `/menu` | 显示主菜单 |

---

## 🧠 智能解析规则

TGSaver 能从文件名中提取：

| 字段 | 示例 |
|------|------|
| 标题 | `肖申克的救赎` |
| 季数 | `S01`、`第2季` |
| 集数 | `E05`、`第12集` |
| 年份 | `(1994)`、`[2023]` |
| 分辨率 | `1080p`、`4K` |

### 动漫检测

自动识别动漫关键词（如字幕组名、编码格式等），自动归类到动漫分类。

---

## 🐳 Docker 部署

### docker-compose.yml

```yaml
services:
  tgsaver:
    image: dustinky/tgsaver:latest
    container_name: tgsaver
    restart: unless-stopped
    env_file: .env
    volumes:
      - /path/to/media:/downloads
    network_mode: host  # 如需代理
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BOT_TOKEN` | Telegram Bot Token | *必填* |
| `ALLOWED_USERS` | 允许的用户 ID（逗号分隔） | 空（不限制） |
| `DOWNLOAD_DIR` | 下载目录 | `/downloads` |
| `PROXY_URL` | Telegram 代理地址 | 空 |
| `TG_API_ID` | Telegram API ID | 空 |
| `TG_API_HASH` | Telegram API Hash | 空 |
| `TG_SESSION_STRING` | Telethon Session String | 空 |

---

## 📁 项目结构

```
tgsaver/
├── bot.py              # 主 Bot 逻辑（交互状态机）
├── parser.py           # 文件名解析器
├── config.py           # 配置管理
├── downloader.py       # Pyrogram 下载器（大文件支持）
├── queue.py            # 下载队列管理
├── login.py            # Session String 登录工具
├── requirements.txt    # Python 依赖
├── Dockerfile          # Docker 镜像构建
├── docker-compose.yml  # Docker Compose 配置
├── .env.example        # 环境变量模板
└── README.md           # 项目文档
```

---

## ❓ 常见问题

### Q: 为什么只能下载 20MB 以下的文件？

A: Telegram Bot API 限制单次下载最大 20MB。如需下载大文件，请配置：
- `TG_API_ID`
- `TG_API_HASH`  
- `TG_SESSION_STRING`

运行 `python login.py` 获取 Session String。

### Q: 如何配置代理？

A: 在 `.env` 中设置 `PROXY_URL`：
```env
PROXY_URL=socks5://127.0.0.1:6891
# 或 HTTP 代理
PROXY_URL=http://127.0.0.1:7890
```

### Q: 如何限制只有我能使用 Bot？

A: 获取你的 Telegram 用户 ID（可通过 @userinfobot），然后设置：
```env
ALLOWED_USERS=你的用户ID
```

### Q: 如何自定义分类？

A: 目前分类固定为：电影、电视剧、动漫、Cosplay、其他。
选择「其他」后可以输入自定义文件夹名。

---

## 🔗 相关链接

- 📦 **GitHub**: https://github.com/Dirige/tgsaver
- 🐳 **Docker Hub**: https://hub.docker.com/r/dustinky/tgsaver

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

---

## 📄 许可证

本项目基于 MIT 许可证开源 - 详见 [LICENSE](LICENSE) 文件

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Dirige">Dustinky</a>
</p>
