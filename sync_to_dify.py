import os
import requests

# ===== 配置区 =====
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_WIKI_SPACE_ID = os.environ.get("FEISHU_WIKI_SPACE_ID", "")  # 飞书知识库空间ID

# Dify 知识库API Key
DIFY_API_KEY = os.environ.get("DIFY_API_KEY", "")  

DIFY_DATASET_ID = os.environ.get("DIFY_DATASET_ID", "")       # 刚创建的空知识库ID
DIFY_BASE_URL = os.environ.get("DIFY_BASE_URL", "http://localhost/v1")  # Dify API 基础地址

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

# ===== 获取文档内容 =====
def get_doc_content(token, doc_token):
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/raw_content",
        headers=headers).json()
    if res.get("code") == 0:
        return res["data"]["content"]
    else:
        print(f"获取文档内容失败 ({doc_token}): {res.get('msg')}")
        return ""

# ===== 写入 Dify 知识库 =====
def upsert_to_dify(title, content, doc_token):
    if not content.strip():
        print(f"文档 [{title}] 内容为空，跳过同步。")
        return
        
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}"}
    # 直接创建文本类型的文档
    url = f"{DIFY_BASE_URL}/datasets/{DIFY_DATASET_ID}/document/create-by-text"
    payload = {
        "name": title,
        "text": content,
        "indexing_technique": "high_quality",
        "process_rule": {"mode": "automatic"},
        "doc_metadata": {
            "feishu_token": doc_token,
            "doc_type": "feishu_wiki"
        }
    }
    
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200 or res.status_code == 201:
        print(f"成功导入: {title}")
    else:
        print(f"导入 Dify 失败: {title}, 状态码: {res.status_code}, 响应: {res.text}")

# ===== 主流程 =====
def sync():
    if not DIFY_API_KEY or DIFY_API_KEY == "dataset-xxxxxxxx":
        print("请注意：您尚未设置 Dify 知识库 API Key！请设置 DIFY_API_KEY 环境变量。")
        return
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET or not FEISHU_WIKI_SPACE_ID or not DIFY_DATASET_ID:
        print("请注意：飞书应用凭证、知识空间ID或Dify数据集ID配置不完整，请检查环境变量设置。")
        return
        
    print("正在获取飞书 Token...")
    token = get_feishu_token()
    
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
            
        print(f"同步: {title}")
        content = get_doc_content(token, node["obj_token"])
        upsert_to_dify(title, content, node["obj_token"])
        
    print("同步完成！")

if __name__ == "__main__":
    sync()
