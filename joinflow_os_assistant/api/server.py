"""
API服务器
"""
import logging
from typing import Optional
from flask import Flask, jsonify, request
from flask_cors import CORS

from ..core.assistant import OSAssistant
from ..core.config import AssistantConfig

logger = logging.getLogger(__name__)


class OSAssistantAPI:
    """
    操作系统助手API封装
    """
    
    def __init__(self, assistant: Optional[OSAssistant] = None):
        self.assistant = assistant or OSAssistant()
    
    def execute(self, command: str, auto_confirm: bool = False) -> dict:
        """执行命令"""
        result = self.assistant.execute(command, auto_confirm)
        return {
            "success": result.success,
            "action": result.action,
            "message": result.message,
            "data": result.data,
            "error": result.error,
            "duration_ms": result.duration_ms,
        }
    
    def get_context(self) -> dict:
        """获取上下文"""
        ctx = self.assistant.get_context()
        return ctx.to_dict()
    
    def get_operations(self) -> list:
        """获取可用操作"""
        return self.assistant.get_available_operations()
    
    def get_memory_summary(self) -> Optional[dict]:
        """获取记忆摘要"""
        return self.assistant.get_memory_summary()


def create_app(config: Optional[AssistantConfig] = None, llm_client=None) -> Flask:
    """
    创建Flask应用
    
    Args:
        config: 助手配置
        llm_client: LLM客户端
    
    Returns:
        Flask: Flask应用实例
    """
    app = Flask(__name__)
    CORS(app)
    
    # 创建助手
    assistant = OSAssistant(config=config, llm_client=llm_client)
    api = OSAssistantAPI(assistant)
    
    # 注册路由
    @app.route("/api/execute", methods=["POST"])
    def execute():
        """执行命令"""
        data = request.json or {}
        command = data.get("command", "")
        auto_confirm = data.get("auto_confirm", False)
        
        if not command:
            return jsonify({"success": False, "message": "缺少command参数"}), 400
        
        try:
            result = api.execute(command, auto_confirm)
            return jsonify(result)
        except Exception as e:
            logger.error(f"执行错误: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
    
    @app.route("/api/context", methods=["GET"])
    def get_context():
        """获取上下文"""
        return jsonify(api.get_context())
    
    @app.route("/api/operations", methods=["GET"])
    def get_operations():
        """获取可用操作"""
        return jsonify({"operations": api.get_operations()})
    
    @app.route("/api/memory", methods=["GET"])
    def get_memory():
        """获取记忆摘要"""
        summary = api.get_memory_summary()
        if summary:
            return jsonify(summary)
        return jsonify({"message": "记忆功能未启用"})
    
    @app.route("/api/health", methods=["GET"])
    def health():
        """健康检查"""
        return jsonify({
            "status": "ok",
            "assistant": "running",
        })
    
    # 快捷方法路由
    @app.route("/api/file/read", methods=["POST"])
    def read_file():
        """读取文件"""
        data = request.json or {}
        path = data.get("path")
        
        if not path:
            return jsonify({"success": False, "message": "缺少path参数"}), 400
        
        result = assistant.read_file(path)
        return jsonify({
            "success": result.success,
            "message": result.message,
            "data": result.data,
        })
    
    @app.route("/api/file/create", methods=["POST"])
    def create_file():
        """创建文件"""
        data = request.json or {}
        path = data.get("path")
        content = data.get("content", "")
        
        if not path:
            return jsonify({"success": False, "message": "缺少path参数"}), 400
        
        result = assistant.create_file(path, content)
        return jsonify({
            "success": result.success,
            "message": result.message,
            "data": result.data,
        })
    
    @app.route("/api/app/open", methods=["POST"])
    def open_app():
        """打开应用"""
        data = request.json or {}
        app_name = data.get("app_name") or data.get("name")
        
        if not app_name:
            return jsonify({"success": False, "message": "缺少app_name参数"}), 400
        
        result = assistant.open_app(app_name)
        return jsonify({
            "success": result.success,
            "message": result.message,
            "data": result.data,
        })
    
    @app.route("/api/search", methods=["POST"])
    def search():
        """搜索文件"""
        data = request.json or {}
        query = data.get("query")
        path = data.get("path")
        
        if not query:
            return jsonify({"success": False, "message": "缺少query参数"}), 400
        
        result = assistant.search_files(query, path)
        return jsonify({
            "success": result.success,
            "message": result.message,
            "data": result.data,
        })
    
    @app.route("/api/system/info", methods=["GET"])
    def system_info():
        """系统信息"""
        result = assistant.get_system_info()
        return jsonify({
            "success": result.success,
            "message": result.message,
            "data": result.data,
        })
    
    @app.route("/api/system/screenshot", methods=["POST"])
    def screenshot():
        """截图"""
        data = request.json or {}
        path = data.get("path")
        
        result = assistant.screenshot(path)
        return jsonify({
            "success": result.success,
            "message": result.message,
            "data": result.data,
        })
    
    @app.route("/api/command", methods=["POST"])
    def run_command():
        """执行命令"""
        data = request.json or {}
        command = data.get("command")
        
        if not command:
            return jsonify({"success": False, "message": "缺少command参数"}), 400
        
        result = assistant.run_command(command)
        return jsonify({
            "success": result.success,
            "message": result.message,
            "data": result.data,
        })
    
    @app.route("/api/browser/search", methods=["POST"])
    def browser_search():
        """浏览器搜索"""
        data = request.json or {}
        query = data.get("query")
        engine = data.get("engine", "google")
        
        if not query:
            return jsonify({"success": False, "message": "缺少query参数"}), 400
        
        result = assistant.search_web(query, engine)
        return jsonify({
            "success": result.success,
            "message": result.message,
            "data": result.data,
        })
    
    return app


def run_server(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """运行服务器"""
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server(debug=True)

