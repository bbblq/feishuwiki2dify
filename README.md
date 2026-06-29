# Feishu Wiki to Dify (飞书知识库同步到 Dify)

这是一个用于将**飞书知识库（Wiki）**下的所有新版文档（`.docx`）内容，自动递归增量/全量同步至 **Dify 知识库（Dataset）**的自动化服务。

项目支持使用 Docker 容器化部署，支持多级目录递归获取、定时循环自动执行以及单次执行退出模式。

## ✨ 特性

- **支持多级目录递归**：自动遍历并拉取飞书知识空间下的所有子级文档。
- **Docx 纯文本解析**：自动调用飞书 `docx/v1` 标准接口读取纯文本，过滤媒体与空白内容，极速导入。
- **两种运行模式**：
  - **定时轮询模式**：容器常驻后台，每隔指定分钟数（`SYNC_INTERVAL_MINUTES`）自动跑一次同步。
  - **单次运行退出模式**：执行完一次同步后立即安全退出（`RUN_ONCE=true`），非常适合与系统的 Crontab 或 Kubernetes CronJob 搭配使用。
- **极简依赖**：仅使用 `requests` 库，核心功能极其轻量，容器构建速度极快。
- **环境安全隔离**：配置全部通过环境变量读取，不泄露敏感密钥。

## ⚙️ 环境变量配置

请参考项目目录下的 `.env.example` 模版，并在根目录下创建 `.env` 文件。

| 环境变量名 | 示例值 | 说明 |
| :--- | :--- | :--- |
| `FEISHU_APP_ID` | `cli_aaa27583c4f9dcce` | 飞书开放平台应用的 App ID |
| `FEISHU_APP_SECRET` | `oePGWKr5Y16c33ErD3...` | 飞书开放平台应用的 App Secret |
| `FEISHU_WIKI_SPACE_ID` | `7633633397621378226` | 飞书知识空间的 Space ID |
| `DIFY_API_KEY` | `dataset-DxLDyKUWkgEH...` | Dify 知识库的全局/只写 API Key（以 `dataset-` 开头） |
| `DIFY_DATASET_ID` | `76de4aa9-1abc-416b-8f30...` | Dify 刚创建的空白知识库 ID |
| `DIFY_BASE_URL` | `http://192.168.200.240:3701/v1` | Dify 后端 API 接口路径（本地或公网） |
| `SYNC_INTERVAL_MINUTES`| `60` | 自动轮询执行的时间间隔（单位：分钟），默认 60 分钟 |
| `RUN_ONCE` | `false` | 是否仅同步一次即退出容器（`true` 或 `false`） |

---

## 🚀 部署指南

### 1. 使用 Docker Compose 运行 (推荐)

在项目目录下准备好 `.env` 配置文件后，只需一行命令即可在后台常驻运行：

```bash
docker compose up -d
```

查看运行日志：

```bash
docker compose logs -f
```

停止服务：

```bash
docker compose down
```

### 2. 使用 Docker CLI 运行

1. **构建镜像：**
   ```bash
   docker build -t bbblq/feishuwiki2dify:latest .
   ```

2. **启动容器：**
   ```bash
   docker run -d \
     --name feishuwiki2dify \
     --env-file .env \
     --restart always \
     bbblq/feishuwiki2dify:latest
   ```

### 3. 本地 Python 运行

如果您不想使用 Docker，也可以直接在本地运行：

1. **安装依赖：**
   ```bash
   pip install requests
   ```

2. **设置环境变量并启动：**
   - **Windows (PowerShell)：**
     ```powershell
     $env:FEISHU_APP_ID="your_id"
     $env:FEISHU_APP_SECRET="your_secret"
     $env:FEISHU_WIKI_SPACE_ID="your_space_id"
     $env:DIFY_API_KEY="your_dify_key"
     $env:DIFY_DATASET_ID="your_dify_dataset_id"
     $env:DIFY_BASE_URL="http://192.168.200.240:3701/v1"
     $env:SYNC_INTERVAL_MINUTES="60"
     $env:RUN_ONCE="false"
     python main.py
     ```
   - **Linux/macOS：**
     ```bash
     export FEISHU_APP_ID="your_id"
     export FEISHU_APP_SECRET="your_secret"
     export FEISHU_WIKI_SPACE_ID="your_space_id"
     export DIFY_API_KEY="your_dify_key"
     export DIFY_DATASET_ID="your_dify_dataset_id"
     export DIFY_BASE_URL="http://192.168.200.240:3701/v1"
     export SYNC_INTERVAL_MINUTES="60"
     export RUN_ONCE="false"
     python main.py
     ```

## 🔒 飞书权限申请提示

为确保飞书 App 能够拉取到文档内容，请确保您的飞书自建应用开通了以下权限并已**发布版本**：
1. **知识库** -> **查看知识库** (`wiki:wiki:readonly`)
2. **云文档** -> **查看、导出新版文档** (`docx:document:readonly`)
3. **云文档** -> **查看、下载云空间文件** (`drive:drive:readonly`)

开源仓库地址：[https://github.com/bbblq/feishuwiki2dify](https://github.com/bbblq/feishuwiki2dify)
