import os
import json
import sys
from flask import Flask, jsonify, request, render_template
import state
from sync_to_dify import CONFIG_PATH, load_settings

app = Flask(__name__, template_folder="templates")

# Log file path
LOG_FILE = os.environ.get("LOG_FILE", "/app/config/sync.log")

# Setup Logger redirection to file and console
class DualLogger(object):
    def __init__(self, filepath):
        self.terminal = sys.stdout
        # Ensure log folder exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.log_file = open(filepath, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

# Redirect standard outputs so the web UI logs view is populated
if not os.environ.get("NO_REDIRECT_LOGS"):
    sys.stdout = DualLogger(LOG_FILE)
    sys.stderr = sys.stdout

def get_last_logs(n=100):
    if not os.path.exists(LOG_FILE):
        return "日志文件尚不存在，请等待同步运行..."
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return "".join(lines[-n:])
    except Exception as e:
        return f"读取日志出错: {e}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def get_status():
    return jsonify({
        "status": state.status,
        "last_sync_time": state.last_sync_time,
        "next_sync_time": state.next_sync_time,
        "error_message": state.error_message,
        "total_docs_synced": state.total_docs_synced
    })

@app.route("/api/logs")
def get_logs():
    return jsonify({
        "logs": get_last_logs(50)
    })

@app.route("/api/config", methods=["GET", "POST"])
def manage_config():
    if request.method == "POST":
        new_config = request.json
        allowed_fields = [
            "FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_WIKI_SPACE_ID",
            "DIFY_API_KEY", "DIFY_DATASET_ID", "DIFY_BASE_URL",
            "IMAGE_BASE_URL", "SYNC_INTERVAL_MINUTES", "RUN_ONCE",
            "MAX_TOKENS", "CHUNK_OVERLAP"
        ]
        sanitized_config = {}
        for field in allowed_fields:
            if field in new_config:
                sanitized_config[field] = str(new_config[field]).strip()
        
        # Ensure configuration directory exists
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(sanitized_config, f, indent=4, ensure_ascii=False)
            return jsonify({"success": True, "message": "配置保存成功！"})
        except Exception as e:
            return jsonify({"success": False, "message": f"保存配置失败: {e}"}), 500
    else:
        # GET method
        settings = load_settings()
        # Ensure we return default values if not explicitly defined
        if "SYNC_INTERVAL_MINUTES" not in settings:
            settings["SYNC_INTERVAL_MINUTES"] = os.environ.get("SYNC_INTERVAL_MINUTES", "60")
        if "RUN_ONCE" not in settings:
            settings["RUN_ONCE"] = os.environ.get("RUN_ONCE", "false")
        if "MAX_TOKENS" not in settings:
            settings["MAX_TOKENS"] = os.environ.get("MAX_TOKENS", "800")
        if "CHUNK_OVERLAP" not in settings:
            settings["CHUNK_OVERLAP"] = os.environ.get("CHUNK_OVERLAP", "150")
        return jsonify(settings)

@app.route("/api/sync", methods=["POST"])
def trigger_sync():
    if state.status == "syncing":
        return jsonify({"success": False, "message": "同步任务已经在运行中..."}), 400
    state.sync_event.set()
    return jsonify({"success": True, "message": "已成功触发同步，正在排队启动..."})

if __name__ == "__main__":
    # Local dev mode (e.g. running python app.py directly)
    os.environ["NO_REDIRECT_LOGS"] = "1"
    app.run(host="0.0.0.0", port=8080, debug=True)
