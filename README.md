# Feishu Wiki to Dify (飞书知识库同步到 Dify)

这是一个用于将**飞书知识库（Wiki）**下的所有新版文档（`.docx`）内容，自动递归增量/全量同步至 **Dify 知识库（Dataset）**的自动化服务。

项目支持使用 Docker 容器化部署，支持多级目录递归获取、定时循环自动执行以及单次执行退出模式。

## ✨ 特性

- **支持多级目录递归**：自动遍历并拉取飞书知识空间下的所有子级文档。
- **完整 Markdown 格式**：使用飞书 Blocks API 获取文档完整结构，支持标题、列表、代码块、引用、表格等富文本格式转换为 Markdown。
- **📸 图片同步支持**：自动下载文档中的嵌入图片，通过内置 Nginx 服务器托管，在 Dify 对话中可直接显示插图。
- **两种运行模式**：
  - **定时轮询模式**：容器常驻后台，每隔指定分钟数（`SYNC_INTERVAL_MINUTES`）自动跑一次同步。
  - **单次运行退出模式**：执行完一次同步后立即安全退出（`RUN_ONCE=true`），非常适合与系统的 Crontab 或 Kubernetes CronJob 搭配使用。
- **极简依赖**：仅使用 `requests` 库，核心功能极其轻量，容器构建速度极快。
- **环境安全隔离**：配置全部通过环境变量读取，不泄露敏感密钥。
- **CasaOS 支持**：内置 `x-casaos` 配置，可直接导入 CasaOS 面板安装使用。

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
| `IMAGE_BASE_URL` | `http://192.168.200.240:8089` | 图片服务的公开访问地址。**留空则跳过图片下载**，仅以占位符导入 |
| `IMAGE_PORT` | `8089` | 图片服务绑定的宿主机端口，默认 `8089` |

---

## 🚀 部署指南

### 1. 使用 Docker Compose 运行 (推荐)

在项目目录下准备好 `.env` 配置文件后，只需一行命令即可在后台常驻运行：

```bash
docker compose up -d
```

这将启动两个容器：
- **feishuwiki2dify**：同步主服务，定时从飞书拉取文档并导入 Dify
- **feishuwiki2dify-images**：Nginx 图片服务器，对外提供图片访问

查看运行日志：

```bash
docker compose logs -f feishu-wiki-sync
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

2. **创建共享数据卷：**
   ```bash
   docker volume create feishu-images
   ```

3. **启动同步容器：**
   ```bash
   docker run -d \
     --name feishuwiki2dify \
     --env-file .env \
     -v feishu-images:/app/images \
     --restart always \
     bbblq/feishuwiki2dify:latest
   ```

4. **启动图片服务容器：**
   ```bash
   docker run -d \
     --name feishuwiki2dify-images \
     -p 8089:80 \
     -v feishu-images:/usr/share/nginx/html/images:ro \
     --restart always \
     nginx:alpine
   ```

### 3. 本地 Python 运行

如果您不想使用 Docker，也可以直接在本地运行：

1. **安装依赖：**
   ```bash
   pip install requests python-dotenv
   ```

2. **创建 `.env` 文件** 并填入配置（参考 `.env.example`）。

3. **启动调度器：**
   ```bash
   python main.py
   ```

   > 注意：本地运行时，如果需要图片同步，还需要自行搭建图片 HTTP 服务器。

## 📸 图片同步说明

### 工作原理

1. 同步脚本使用飞书 **Blocks API** 获取文档的完整块结构（而非纯文本）
2. 遇到图片块时，自动通过飞书 **Drive API** 下载图片二进制文件
3. 图片保存在 Docker 共享卷中，由内置 Nginx 服务器对外提供 HTTP 访问
4. 文档内容以 Markdown 格式导入 Dify，图片以 `![描述](http://xxx/images/xxx.png)` 形式嵌入
5. 用户在 Dify 聊天界面提问时，AI 回答中引用的图片 URL 可被浏览器直接渲染

### 禁用图片同步

如果不需要图片功能（例如知识库中没有图片、或网络环境不方便托管图片服务），只需在 `.env` 中留空 `IMAGE_BASE_URL`：

```
IMAGE_BASE_URL=
```

此时脚本会自动回退为纯文本模式，图片位置以 `[图片: xxx]` 占位符替代。

## 🔒 飞书权限申请提示

为确保飞书 App 能够拉取到文档内容和图片，请确保您的飞书自建应用开通了以下权限并已**发布版本**：
1. **知识库** -> **查看知识库** (`wiki:wiki:readonly`)
2. **云文档** -> **查看、导出新版文档** (`docx:document:readonly`)
3. **云文档** -> **查看、下载云空间文件** (`drive:drive:readonly`)
4. **云文档** -> **下载云文档中的图片和附件** (`docs:document.media:download`) ⚠️ **图片同步必需**

> ⚠️ `docs:document.media:download` 权限与 `drive:drive:readonly` 不同！前者专门用于下载文档中嵌入的图片/附件，后者仅访问云空间文件。缺少此权限会导致图片下载返回 403。

## 🏠 CasaOS 安装

1. 在 CasaOS 面板中点击 **安装应用** → **自定义安装**
2. 点击 **导入**，粘贴本项目 `docker-compose.yml` 的内容
3. CasaOS 会自动解析环境变量，生成输入表单
4. 填入飞书和 Dify 的配置信息，点击安装即可

---

开源仓库地址：[https://github.com/bbblq/feishuwiki2dify](https://github.com/bbblq/feishuwiki2dify)
