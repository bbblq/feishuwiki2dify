import os
import json
import requests

# ===== 配置区 =====
CONFIG_PATH = os.environ.get("CONFIG_PATH", "/app/config/config.json")

FEISHU_APP_ID = ""
FEISHU_APP_SECRET = ""
FEISHU_WIKI_SPACE_ID = ""
DIFY_API_KEY = ""
DIFY_DATASET_ID = ""
DIFY_BASE_URL = "http://localhost/v1"
IMAGE_BASE_URL = ""
IMAGES_DIR = "/app/images"
MAX_TOKENS = "800"
CHUNK_OVERLAP = "150"
FORCE_SINGLE_CHUNK = "true"

def load_settings():
    """Load configuration from JSON file first, falling back to environment variables"""
    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading config file: {e}")
            
    return {
        "FEISHU_APP_ID": config.get("FEISHU_APP_ID") or os.environ.get("FEISHU_APP_ID", ""),
        "FEISHU_APP_SECRET": config.get("FEISHU_APP_SECRET") or os.environ.get("FEISHU_APP_SECRET", ""),
        "FEISHU_WIKI_SPACE_ID": config.get("FEISHU_WIKI_SPACE_ID") or os.environ.get("FEISHU_WIKI_SPACE_ID", ""),
        "DIFY_API_KEY": config.get("DIFY_API_KEY") or os.environ.get("DIFY_API_KEY", ""),
        "DIFY_DATASET_ID": config.get("DIFY_DATASET_ID") or os.environ.get("DIFY_DATASET_ID", ""),
        "DIFY_BASE_URL": config.get("DIFY_BASE_URL") or os.environ.get("DIFY_BASE_URL", "http://localhost/v1"),
        "IMAGE_BASE_URL": config.get("IMAGE_BASE_URL") or os.environ.get("IMAGE_BASE_URL", ""),
        "IMAGES_DIR": config.get("IMAGES_DIR") or os.environ.get("IMAGES_DIR", "/app/images"),
        "MAX_TOKENS": config.get("MAX_TOKENS") or os.environ.get("MAX_TOKENS", "800"),
        "CHUNK_OVERLAP": config.get("CHUNK_OVERLAP") or os.environ.get("CHUNK_OVERLAP", "150"),
        "FORCE_SINGLE_CHUNK": config.get("FORCE_SINGLE_CHUNK") or os.environ.get("FORCE_SINGLE_CHUNK", "true")
    }

def load_globals():
    global FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_WIKI_SPACE_ID
    global DIFY_API_KEY, DIFY_DATASET_ID, DIFY_BASE_URL
    global IMAGE_BASE_URL, IMAGES_DIR, MAX_TOKENS, CHUNK_OVERLAP, FORCE_SINGLE_CHUNK
    settings = load_settings()
    FEISHU_APP_ID = settings["FEISHU_APP_ID"]
    FEISHU_APP_SECRET = settings["FEISHU_APP_SECRET"]
    FEISHU_WIKI_SPACE_ID = settings["FEISHU_WIKI_SPACE_ID"]
    DIFY_API_KEY = settings["DIFY_API_KEY"]
    DIFY_DATASET_ID = settings["DIFY_DATASET_ID"]
    DIFY_BASE_URL = settings["DIFY_BASE_URL"]
    IMAGE_BASE_URL = settings["IMAGE_BASE_URL"]
    IMAGES_DIR = settings["IMAGES_DIR"]
    MAX_TOKENS = settings["MAX_TOKENS"]
    CHUNK_OVERLAP = settings["CHUNK_OVERLAP"]
    FORCE_SINGLE_CHUNK = settings["FORCE_SINGLE_CHUNK"]

# Initial load
load_globals()

# ===== 飞书文档 Block 类型常量 =====
BLOCK_PAGE = 1
BLOCK_TEXT = 2
BLOCK_H1 = 3
BLOCK_H2 = 4
BLOCK_H3 = 5
BLOCK_H4 = 6
BLOCK_H5 = 7
BLOCK_H6 = 8
BLOCK_H7 = 9
BLOCK_H8 = 10
BLOCK_H9 = 11
BLOCK_BULLET = 12
BLOCK_ORDERED = 13
BLOCK_CODE = 14
BLOCK_QUOTE = 15
BLOCK_TODO = 17
BLOCK_CALLOUT = 19
BLOCK_DIVIDER = 22
BLOCK_FILE = 23
BLOCK_GRID = 24
BLOCK_GRID_COLUMN = 25
BLOCK_IMAGE = 27
BLOCK_TABLE = 33       # 飞书 API 实际：33 = 表格本体（有 'table' 键）
BLOCK_TABLE_CELL = 32  # 飞书 API 实际：32 = 表格单元格（有 'table_cell' 键）
BLOCK_QUOTE_CONTAINER = 35

# Block 类型到其数据字段名的映射（这些 block 都包含 elements 列表）
TEXT_BLOCK_FIELDS = {
    BLOCK_TEXT: "text",
    BLOCK_H1: "heading1", BLOCK_H2: "heading2", BLOCK_H3: "heading3",
    BLOCK_H4: "heading4", BLOCK_H5: "heading5", BLOCK_H6: "heading6",
    BLOCK_H7: "heading7", BLOCK_H8: "heading8", BLOCK_H9: "heading9",
    BLOCK_BULLET: "bullet",
    BLOCK_ORDERED: "ordered",
    BLOCK_CODE: "code",
    BLOCK_QUOTE: "quote",
    BLOCK_TODO: "todo",
    BLOCK_CALLOUT: "callout",
}

# ===== 获取飞书 Token =====
def get_feishu_token():
    res = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET})
    return res.json()["tenant_access_token"]

# ===== 获取知识空间下所有节点 (支持多级目录递归获取) =====
def get_wiki_nodes(token):
    headers = {"Authorization": f"Bearer {token}"}
    nodes = []

    def traverse(parent_token=None):
        page_token = None
        while True:
            params = {"page_size": 50}
            if page_token:
                params["page_token"] = page_token
            if parent_token:
                params["parent_node_token"] = parent_token

            url = f"https://open.feishu.cn/open-apis/wiki/v2/spaces/{FEISHU_WIKI_SPACE_ID}/nodes"
            res = requests.get(url, headers=headers, params=params).json()

            if res.get("code") != 0:
                print(f"获取节点失败 (parent: {parent_token}): {res.get('msg')}")
                break

            data = res.get("data", {})
            items = data.get("items", [])
            for item in items:
                nodes.append(item)
                # 如果该节点有子节点，递归获取
                if item.get("has_child"):
                    traverse(item["node_token"])

            if not data.get("has_more"):
                break
            page_token = data.get("page_token")

    traverse()
    return nodes

# ===== 获取文档所有 Block（带分页）=====
def get_doc_blocks(token, doc_token):
    """通过 blocks API 获取文档的完整块列表（含图片块等结构信息）"""
    headers = {"Authorization": f"Bearer {token}"}
    blocks = []
    page_token = None

    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token

        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
        res = requests.get(url, headers=headers, params=params).json()

        if res.get("code") != 0:
            print(f"  获取文档块失败 ({doc_token}): {res.get('msg')}")
            break

        data = res.get("data", {})
        items = data.get("items", [])
        blocks.extend(items)

        if not data.get("has_more"):
            break
        page_token = data.get("page_token")

    return blocks

# ===== 从 Block 的 elements 列表中提取纯文本 =====
def extract_text_from_elements(elements):
    """提取 elements 中的所有文本片段，拼接返回"""
    parts = []
    for elem in elements:
        if "text_run" in elem:
            parts.append(elem["text_run"].get("content", ""))
        elif "mention_user" in elem:
            parts.append(f"@{elem['mention_user'].get('user_id', '用户')}")
        elif "mention_doc" in elem:
            title = elem["mention_doc"].get("title", "文档")
            parts.append(f"[{title}]")
        elif "equation" in elem:
            parts.append(f"${elem['equation'].get('content', '')}$")
    return "".join(parts)

# ===== 从 Block 中提取文本内容 =====
def get_block_text(block, block_type):
    """获取文本类型 block 的文本内容"""
    field_name = TEXT_BLOCK_FIELDS.get(block_type)
    if not field_name:
        return ""
    data = block.get(field_name, {})
    elements = data.get("elements", [])
    return extract_text_from_elements(elements)

# ===== 下载图片到本地 =====
def download_image(token, image_token, doc_token):
    """从飞书下载图片，保存到本地目录，返回公开访问 URL"""
    if not IMAGE_BASE_URL:
        return None

    # 创建文档对应的图片目录
    doc_images_dir = os.path.join(IMAGES_DIR, doc_token)
    os.makedirs(doc_images_dir, exist_ok=True)

    # 检查是否已经下载过（任意扩展名）
    for existing in os.listdir(doc_images_dir):
        if existing.startswith(image_token):
            return f"{IMAGE_BASE_URL.rstrip('/')}/images/{doc_token}/{existing}"

    # 从飞书 Drive API 下载
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://open.feishu.cn/open-apis/drive/v1/medias/{image_token}/download"

    try:
        res = requests.get(url, headers=headers, stream=True, timeout=30)
        if res.status_code == 200:
            # 根据 Content-Type 确定扩展名
            content_type = res.headers.get("Content-Type", "image/png")
            ext = "png"
            if "jpeg" in content_type or "jpg" in content_type:
                ext = "jpg"
            elif "gif" in content_type:
                ext = "gif"
            elif "webp" in content_type:
                ext = "webp"
            elif "svg" in content_type:
                ext = "svg"

            image_path = os.path.join(doc_images_dir, f"{image_token}.{ext}")
            with open(image_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"    图片已下载: {image_token}.{ext}")
            return f"{IMAGE_BASE_URL.rstrip('/')}/images/{doc_token}/{image_token}.{ext}"
        else:
            print(f"    下载图片失败 ({image_token}): HTTP {res.status_code} - {res.text[:200]}")
            return None
    except Exception as e:
        print(f"    下载图片异常 ({image_token}): {e}")
        return None

# ===== 将 Block 树转换为 Markdown 文本（含图片链接）=====
def blocks_to_markdown(blocks, doc_token, token):
    """将飞书文档的 block 列表转换为 Markdown 字符串"""
    # 构建 block_id → block 的映射
    block_map = {b["block_id"]: b for b in blocks}

    # 找到根 Page block
    root = None
    for b in blocks:
        if b.get("block_type") == BLOCK_PAGE:
            root = b
            break

    if not root:
        return ""

    lines = []
    ordered_counters = {}  # 记录有序列表计数器

    def process_block(block_id):
        block = block_map.get(block_id)
        if not block:
            return

        bt = block.get("block_type")

        # ---- Page（根节点）：递归处理子节点 ----
        if bt == BLOCK_PAGE:
            for child_id in block.get("children", []):
                process_block(child_id)

        # ---- 文本段落 ----
        elif bt == BLOCK_TEXT:
            text = get_block_text(block, bt)
            if text:
                lines.append(text)

        # ---- 标题 H1~H9 ----
        elif BLOCK_H1 <= bt <= BLOCK_H9:
            text = get_block_text(block, bt)
            level = bt - BLOCK_H1 + 1
            if text:
                lines.append(f"{'#' * level} {text}")

        # ---- 无序列表 ----
        elif bt == BLOCK_BULLET:
            text = get_block_text(block, bt)
            lines.append(f"- {text}")
            # 处理嵌套子项
            for child_id in block.get("children", []):
                child = block_map.get(child_id)
                if child:
                    child_bt = child.get("block_type")
                    child_text = get_block_text(child, child_bt)
                    if child_bt == BLOCK_BULLET:
                        lines.append(f"  - {child_text}")
                    elif child_bt == BLOCK_ORDERED:
                        lines.append(f"  1. {child_text}")
                    else:
                        process_block(child_id)

        # ---- 有序列表 ----
        elif bt == BLOCK_ORDERED:
            text = get_block_text(block, bt)
            parent_id = block.get("parent_id", "")
            ordered_counters[parent_id] = ordered_counters.get(parent_id, 0) + 1
            lines.append(f"{ordered_counters[parent_id]}. {text}")
            for child_id in block.get("children", []):
                process_block(child_id)

        # ---- 代码块 ----
        elif bt == BLOCK_CODE:
            text = get_block_text(block, bt)
            data = block.get("code", {})
            style = data.get("style", {})
            # language 可能是整数（枚举值），也可能是字符串
            lang = style.get("language", "")
            if isinstance(lang, int):
                lang = ""  # 飞书用整数表示语言类型，这里简化处理
            lines.append(f"```{lang}")
            lines.append(text)
            lines.append("```")

        # ---- 引用 ----
        elif bt == BLOCK_QUOTE:
            text = get_block_text(block, bt)
            lines.append(f"> {text}")

        # ---- 待办 ----
        elif bt == BLOCK_TODO:
            text = get_block_text(block, bt)
            data = block.get("todo", {})
            style = data.get("style", {})
            done = style.get("done", False)
            checkbox = "[x]" if done else "[ ]"
            lines.append(f"- {checkbox} {text}")

        # ---- 高亮块 (Callout) ----
        elif bt == BLOCK_CALLOUT:
            text = get_block_text(block, bt)
            if text:
                lines.append(f"> 💡 {text}")
            # Callout 可能有子 block
            for child_id in block.get("children", []):
                process_block(child_id)

        # ---- 分隔线 ----
        elif bt == BLOCK_DIVIDER:
            lines.append("---")

        # ---- 图片 ----
        elif bt == BLOCK_IMAGE:
            image_data = block.get("image", {})
            image_token = image_data.get("token", "")
            caption = ""
            caption_data = image_data.get("caption")
            if caption_data:
                # caption 可能是字符串或包含 content 的对象
                if isinstance(caption_data, dict):
                    caption = caption_data.get("content", "")
                elif isinstance(caption_data, str):
                    caption = caption_data

            if image_token and IMAGE_BASE_URL:
                image_url = download_image(token, image_token, doc_token)
                if image_url:
                    alt_text = caption if caption else "插图"
                    lines.append(f"![{alt_text}]({image_url})")
                else:
                    lines.append(f"[图片: {caption or image_token}]")
            elif image_token:
                lines.append(f"[图片: {caption or image_token}]")

        # ---- 表格 ----
        elif bt == BLOCK_TABLE:
            table_lines = table_to_markdown_lines(block, block_map)
            if table_lines:
                # 必须用\n拼接表格行，再作为一个整体添加到 lines，避免\n\njoin 把表格行切断
                lines.append("\n".join(table_lines))

        # ---- 容器类 block（Grid / GridColumn / QuoteContainer）——递归处理子节点 ----
        elif bt in (BLOCK_GRID, BLOCK_GRID_COLUMN, BLOCK_QUOTE_CONTAINER):
            for child_id in block.get("children", []):
                process_block(child_id)

        # ---- 文件附件 ----
        elif bt == BLOCK_FILE:
            file_data = block.get("file", {})
            file_name = file_data.get("name", "附件")
            lines.append(f"[📎 附件: {file_name}]")

        # ---- 其他未知类型 ——尝试递归处理子节点 ----
        else:
            for child_id in block.get("children", []):
                process_block(child_id)

    # 从根节点开始处理
    process_block(root["block_id"])

    # 后处理1：将连续的列表项（有序/无序）用\n合并成一个整体段落
    def is_list_item(s):
        if not s:
            return False
        import re
        return bool(re.match(r'^(\d+\.|  \d+\.|  -|- |> 💡)', s))

    merged = []
    i = 0
    filtered = [l for l in lines if l is not None]
    while i < len(filtered):
        line = filtered[i]
        if is_list_item(line):
            group = [line]
            i += 1
            while i < len(filtered) and is_list_item(filtered[i]):
                group.append(filtered[i])
                i += 1
            merged.append("\n".join(group))
        else:
            merged.append(line)
            i += 1

    # 后处理2：将"短标题行"（≤20字、末尾是冒号/：的行）和紧跟的下一块用\n合并
    # 避免"注意事项：""字段定义："等独立成只有5个字的碎片 chunk
    import re
    final = []
    j = 0
    while j < len(merged):
        block = merged[j]
        # 判断是否是短标题行：纯文本、不超过20个字符、末尾是中文冒号或英文冒号
        stripped = block.strip()
        is_short_heading = (
            len(stripped) <= 20
            and not stripped.startswith('#')
            and not stripped.startswith('![')
            and not stripped.startswith('|')
            and not stripped.startswith('-')
            and not stripped.startswith('>')
            and re.search(r'[：:]\s*$', stripped)
            and j + 1 < len(merged)
        )
        if is_short_heading:
            # 与下一块合并
            final.append(block + "\n" + merged[j + 1])
            j += 2
        else:
            final.append(block)
            j += 1

    return "\n\n".join(final)


def table_to_markdown_lines(table_block, block_map):
    """将表格 Block 转换为 Markdown 表格文本行"""
    table_data = table_block.get("table", {})
    prop = table_data.get("property", {})
    rows = prop.get("row_size", 0)
    cols = prop.get("column_size", 0)

    # 优先使用 table.cells，回退到 children
    cell_ids = table_data.get("cells", []) or table_block.get("children", [])

    if not cell_ids:
        return []

    # 如果 row/col 尺寸未知，递归得到 cols 数
    if rows == 0 or cols == 0:
        # 无法确定表格结构，逐个提取文本并拼接
        texts = []
        for cell_id in cell_ids:
            cell_block = block_map.get(cell_id)
            if cell_block:
                cell_text = extract_cell_text(cell_block, block_map)
                if cell_text.strip():
                    texts.append(cell_text.strip())
        return [" | ".join(texts)] if texts else []

    result_lines = []
    table_rows = []

    for r in range(rows):
        row = []
        for c in range(cols):
            idx = r * cols + c
            if idx < len(cell_ids):
                cell_block = block_map.get(cell_ids[idx])
                if cell_block:
                    cell_text = extract_cell_text(cell_block, block_map)
                    row.append(cell_text.replace("\n", " ").strip())
                else:
                    row.append("")
            else:
                row.append("")
        table_rows.append(row)

    if table_rows:
        # 表头
        result_lines.append("| " + " | ".join(table_rows[0]) + " |")
        result_lines.append("| " + " | ".join(["---"] * cols) + " |")
        for row in table_rows[1:]:
            result_lines.append("| " + " | ".join(row) + " |")

    return result_lines

def extract_cell_text(cell_block, block_map):
    """从表格单元格 Block 及其子 Block 中提取文本"""
    texts = []
    for child_id in cell_block.get("children", []):
        child = block_map.get(child_id)
        if not child:
            continue
        bt = child.get("block_type")
        if bt in TEXT_BLOCK_FIELDS:
            texts.append(get_block_text(child, bt))
        elif bt == BLOCK_IMAGE:
            image_data = child.get("image", {})
            caption = ""
            caption_data = image_data.get("caption")
            if caption_data and isinstance(caption_data, dict):
                caption = caption_data.get("content", "")
            texts.append(f"[图片: {caption or '嵌入图'}]")
    return " ".join(texts)

# ===== 获取文档内容（Markdown 格式，含图片链接）=====
def get_doc_content(token, doc_token):
    """获取文档内容，优先使用 blocks API 解析为带图片的 Markdown，失败时回退到纯文本"""
    # 尝试使用 blocks API 获取完整结构
    blocks = get_doc_blocks(token, doc_token)
    if blocks:
        md = blocks_to_markdown(blocks, doc_token, token)
        if md.strip():
            return md

    # 回退到纯文本 raw_content
    print(f"  回退到 raw_content 接口...")
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/raw_content",
        headers=headers).json()
    if res.get("code") == 0:
        return res["data"]["content"]
    else:
        print(f"  获取文档内容失败 ({doc_token}): {res.get('msg')}")
        return ""

# ===== 获取 Dify 已有文档列表 =====
def get_dify_documents():
    """获取 Dify 知识库中已有的所有文档，返回 feishu_token 到 dify_document_id 的映射字典"""
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}"}
    doc_map = {}
    page = 1
    while True:
        url = f"{DIFY_BASE_URL}/datasets/{DIFY_DATASET_ID}/documents?page={page}&limit=100"
        try:
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code != 200:
                print(f"  获取 Dify 文档列表失败，状态码: {res.status_code}")
                break
            
            data = res.json()
            items = data.get("data", [])
            if not items:
                break
                
            for item in items:
                metadata = item.get("doc_metadata") or {}
                feishu_token = metadata.get("feishu_token")
                if feishu_token:
                    doc_map[feishu_token] = item["id"]
                    
            if len(items) < 100:
                break
            page += 1
        except Exception as e:
            print(f"  获取 Dify 文档列表发生异常: {e}")
            break
    return doc_map

# ===== 写入/更新 Dify 知识库 =====
def upsert_to_dify(title, content, doc_token, existing_doc_id=None):
    if not content.strip():
        print(f"文档 [{title}] 内容为空，跳过同步。")
        return

    # 将文档标题作为 Markdown 一级标题注入到文本内容最前方，确保 Dify 进行向量索引，能够精准被标题搜索召回
    if title:
        title_header = f"# {title}"
        if not content.strip().startswith(title_header):
            content = f"{title_header}\n\n{content}"

    headers = {"Authorization": f"Bearer {DIFY_API_KEY}"}
    
    # 构建自定义分块规则
    is_force_single = str(FORCE_SINGLE_CHUNK).lower() in ("true", "1", "yes")

    if is_force_single:
        # 强制单文档作为一个分段模式：使用永远不匹配的分段符，并且分段上限设为 4000（Dify 支持的上限值），实现单篇整页尽量不切分
        process_rule = {
            "mode": "custom",
            "rules": {
                "pre_processing_rules": [
                    { "id": "remove_extra_spaces", "enabled": True },
                    { "id": "remove_urls_emails", "enabled": False }
                ],
                "segmentation": {
                    "separator": "###___NEVER_SPLIT_THIS_DOCUMENT___###",
                    "max_tokens": 4000,
                    "chunk_overlap": 0
                }
            }
        }
    else:
        try:
            max_tok = int(MAX_TOKENS)
        except ValueError:
            max_tok = 800
            
        try:
            overlap = int(CHUNK_OVERLAP)
        except ValueError:
            overlap = 150

        process_rule = {
            "mode": "custom",
            "rules": {
                "pre_processing_rules": [
                    { "id": "remove_extra_spaces", "enabled": True },
                    { "id": "remove_urls_emails", "enabled": False }
                ],
                "segmentation": {
                    "separator": "\n\n",
                    "max_tokens": max_tok,
                    "chunk_overlap": overlap
                }
            }
        }
    
    if existing_doc_id:
        # 更新已有文档
        url = f"{DIFY_BASE_URL}/datasets/{DIFY_DATASET_ID}/documents/{existing_doc_id}/update-by-text"
        payload = {
            "name": title,
            "text": content,
            "process_rule": process_rule
        }
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200 or res.status_code == 201:
            print(f"  更新 Dify 文档成功: {title}")
            import state
            state.total_docs_synced += 1
        else:
            print(f"  更新 Dify 文档失败: {title}, 状态码: {res.status_code}, 响应: {res.text}")
    else:
        # 创建新文档
        url = f"{DIFY_BASE_URL}/datasets/{DIFY_DATASET_ID}/document/create-by-text"
        payload = {
            "name": title,
            "text": content,
            "indexing_technique": "high_quality",
            "process_rule": process_rule,
            "doc_metadata": {
                "feishu_token": doc_token,
                "doc_type": "feishu_wiki"
            }
        }
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200 or res.status_code == 201:
            print(f"  创建 Dify 文档成功: {title}")
            import state
            state.total_docs_synced += 1
        else:
            print(f"  创建 Dify 文档失败: {title}, 状态码: {res.status_code}, 响应: {res.text}")

# ===== 主流程 =====
def sync():
    load_globals()
    import state
    state.total_docs_synced = 0
    if not DIFY_API_KEY or DIFY_API_KEY == "dataset-xxxxxxxx":
        print("请注意：您尚未设置 Dify 知识库 API Key！请设置 DIFY_API_KEY 环境变量。")
        return
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET or not FEISHU_WIKI_SPACE_ID or not DIFY_DATASET_ID:
        print("请注意：飞书应用凭证、知识空间ID或Dify数据集ID配置不完整，请检查环境变量设置。")
        return

    if IMAGE_BASE_URL:
        print(f"图片同步已启用，图片服务地址: {IMAGE_BASE_URL}")
        os.makedirs(IMAGES_DIR, exist_ok=True)
    else:
        print("提示: 未设置 IMAGE_BASE_URL，图片将以占位符形式导入（不含实际图片链接）。")

    print("正在获取飞书 Token...")
    token = get_feishu_token()

    print("正在拉取 Dify 已有文档列表...")
    dify_doc_map = get_dify_documents()
    print(f"Dify 中已存在 {len(dify_doc_map)} 个关联文档")

    print("正在读取飞书知识空间节点列表...")
    nodes = get_wiki_nodes(token)
    print(f"找到 {len(nodes)} 个节点")

    for node in nodes:
        title = node.get("title", "未命名文档")
        # 仅同步新版文档(docx)，如果是快捷方式(shortcut)或旧版doc则根据需要过滤或处理
        obj_type = node.get("obj_type")
        if obj_type != "docx":
            print(f"跳过非新版文档 ({obj_type}): {title}")
            continue

        obj_token = node["obj_token"]
        print(f"同步: {title}")
        content = get_doc_content(token, obj_token)
        
        # 检查是否在 Dify 中已存在
        existing_id = dify_doc_map.get(obj_token)
        upsert_to_dify(title, content, obj_token, existing_id)

    print("同步完成！")

if __name__ == "__main__":
    sync()
